import json
from google.cloud import storage, bigquery, pubsub_v1
from datetime import datetime
import functions_framework
import logging
from flask import jsonify

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

project_id = "phuttimate-temp"
topic_id = "bigquery-staging-to-production"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

def publish_transform_event():
    message_data = {
        "status": "staging_loaded",
        "trigger": "match_data_ready"
    }
    message_json = json.dumps(message_data).encode("utf-8")
    future = publisher.publish(topic_path, data=message_json)
    print(f"Published message to {topic_path}: {future.result()}")

def flatten_participant(match_id, game_datetime, game_version, participant):
    # Ensure correct transformation of traits
    transformed_traits = []
    for trait in participant.get("traits", []):
        transformed_traits.append({
            "name": trait.get("name"),
            "num_units": trait.get("num_units"),
            "style": trait.get("style"),
            "tier_current": trait.get("tier_current"),
            "tier_total": trait.get("tier_total")
        })

    # Ensure correct transformation of units
    transformed_units = []
    for unit in participant.get("units", []):
        transformed_units.append({
            "character_id": unit.get("character_id"),
            "itemNames": unit.get("itemNames", []),  # Must be a list!
            "name": unit.get("name"),
            "rarity": unit.get("rarity"),
            "tier": unit.get("tier")
        })

    return {
        "match_id": match_id,
        "puuid": participant["puuid"],
        "placement": participant["placement"],
        "level": participant["level"],
        "gold_left": participant["gold_left"],
        "last_round": participant["last_round"],
        "augments": participant.get("augments", []),
        "traits": transformed_traits,
        "units": transformed_units,
        "game_version": game_version,
        "game_datetime": datetime.fromtimestamp(game_datetime / 1000).isoformat()
    }


def load_transformed_data(bucket_name, folder_path, project_id, bq_table):
    logger.info(f"Loading data from GCS bucket: {bucket_name}, folder: {folder_path}")
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    bq = bigquery.Client(project=project_id)
    rows_to_insert = []

    blobs = bucket.list_blobs(prefix=f"{folder_path}/raw_matches/")

    for blob in blobs:
        logger.info(f"Processing blob: {blob.name}")
        try:
            content = blob.download_as_string().decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to download or decode {blob.name}: {e}")
            continue

        if not content.strip():
            logger.warning(f"{blob.name} is empty. Skipping.")
            continue

        try:
            match_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"{blob.name} is not valid JSON: {e}")
            continue

        try:
            match_id = match_data["metadata"]["match_id"]
            game_datetime = match_data["info"]["game_datetime"]
            game_version = match_data["info"]["game_version"]

            for participant in match_data["info"]["participants"]:
                flat_row = flatten_participant(match_id, game_datetime, game_version, participant)
                rows_to_insert.append(flat_row)

        except Exception as e:
            logger.error(f"Failed to extract fields from {blob.name}: {e}")
            continue

    if not rows_to_insert:
        logger.warning("No rows to insert into BigQuery.")
        return

    try:
        job = bq.insert_rows_json(bq_table, rows_to_insert)
        if job:
            logger.error(f"BigQuery insert errors: {job}")
        else:
            logger.info(f"Successfully loaded {len(rows_to_insert)} rows into {bq_table}")
    except Exception as e:
        logger.error(f"BigQuery insertion failed: {e}")


@functions_framework.cloud_event
def main(cloud_event):
    if cloud_event.data is None:
        return 'Bad Request', 400
    logger.info(f"Cloud Event Data: {cloud_event.data}")
    try:
        # data = cloud_event.data
        project_id = "phuttimate-temp"
        bucket_name = "tft_pipeline_bucket"
        folder_path = "TFT"
        bq_table = f"{project_id}.TFT_dataset.raw_matches"
        load_transformed_data(bucket_name, folder_path, project_id, bq_table)
        publish_transform_event()
        logger.info("Data loaded successfully and event published.")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing cloud event: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500