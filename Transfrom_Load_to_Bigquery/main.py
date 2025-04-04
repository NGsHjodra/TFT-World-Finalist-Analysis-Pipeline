import json
from google.cloud import storage, bigquery
from datetime import datetime
import functions_framework
from google.cloud import bigquery
import logging
from flask import jsonify

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def flatten_participant(match_id, game_datetime, game_version, participant):
    return {
        "match_id": match_id,
        "puuid": participant["puuid"],
        "placement": participant["placement"],
        "level": participant["level"],
        "gold_left": participant["gold_left"],
        "last_round": participant["last_round"],
        "augments": participant.get("augments", []),
        "traits": participant.get("traits", []),
        "units": participant.get("units", []),
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
        match_data = json.loads(blob.download_as_string())
        match_id = match_data["metadata"]["match_id"]
        game_datetime = match_data["info"]["game_datetime"]
        game_version = match_data["info"]["game_version"]

        for participant in match_data["info"]["participants"]:
            flat_row = flatten_participant(match_id, game_datetime, game_version, participant)
            rows_to_insert.append(flat_row)

    job = bq.insert_rows_json(bq_table, rows_to_insert)
    if job:
        logger.error(f"Error loading data into BigQuery: {job}")
    else:
        logger.info(f"Successfully loaded {len(rows_to_insert)} rows into {bq_table}")

@functions_framework.cloud_event
def main(cloud_event):
    if cloud_event.data is None:
        return 'Bad Request', 400
    logger.info(f"Cloud Event Data: {cloud_event.data}")
    try:
        data = cloud_event.data
        project_id = data["project_id"]
        bucket_name = data["bucket_name"]
        folder_path = data["folder_path"]
        bq_table = data["bq_table"]
        load_transformed_data(bucket_name, folder_path, project_id, bq_table)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing cloud event: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500