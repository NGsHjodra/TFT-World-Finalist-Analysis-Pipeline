import json
from google.cloud import storage, bigquery
from datetime import datetime
import functions_framework
import logging
from flask import jsonify

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

player_list = [
    ["Dishsoap", "NA2", "NA", "GDtO4yJ1GG0b4C4S2zxqxUhdcPju_rmtGnsVVzNdvbOG0XRrh2bo2g3ekCC-eyXJVNC9B8kKkXe33g"],
    ["M8 Jedusor", "12345", "EUW", "kOsBya31_nrnKb4zXBoXJa9IKnMz9JIa8i_Dyxf6bMvXy5GzuFYDoxtiVrtWMpAV1CKLOjQf4fkkgQ"],
    ["eusouolucas", "1111", "BR", "w8vSvHzPK4lcrlnqQWlQ2JNH36xqf0CIbHhBYV-n-H8x2gtwC8djiK1stYmFgfTh8sXSCNfrLKOnXw"],
    ["Deis1k", "EUW", "EUW", "Nc13EOew5HOm8epkuLLehYTMHEwP0QIWVH1MWWwloCqAozwfZi1vuRxWCwPxEHIgvDPf6IvT-ZumxA"],
    ["Só bio", "BR1", "BR", "F35MREp64IcD2bSekqk89rON6qkzdD_BnEEL7T5XBn4ZYC7JzzwQrd-tOb1dKf2kEzjSOxNrkpTJlg"],
    ["VIT prestivent", "123", "NA", "XXSIWM79xLgJeyY0bn8bFnDBC1vcqZJVr6l2UUX9pyqFgQzyc3Xiw184sLGatcXJE25ZfQdN1AC3cg"],
    ["RCS Xperion", "EUW11", "EUW", "o3OEd_6rmOKd1HqpFksDtihgpgy1JNXOx8DI7kO5HrJf-LLsKFadRDnT5fDRM2IbhccbL37w7pTkVQ"],
    ["MIH TarteMan", "EUW", "EUW", "vY0cq71fLXi9sQbTZjkDzeWacza-Ku3Y-1K8poEx5QsfhptbtnR7llzjYjh-MJfWdlVWodrY3fNhRA"],
    ["Boomhae", "0901", "SEA", "cXgVs5Lha9SqCMQb65Kuum9Uk7-WizwffHyslrnRRAcYGI0qlG9smSeyKAWnd_V6b1p4nF1JpqPnuw"],
    ["빈 칠", "123", "KR", "WZoTjjJHQNgWjO4aydENeJT9Euo1VFSv-o00YWcesFCu1_EV8FUzjFVTeMm9BAi5o1RQS00yIadDlA"],
    ["META SpencerTFT", "TFT", "NA", "CzOmt0D3kLzljvMUZ8_VqSnHU1HdqSw3qzsL1R7GZchfEwcLWOeRLzctXRTL82a4jwRTX_dJjHaN1g"]
]

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
        project_id = "primeval-proton-449808-i6"
        bucket_name = "really_not_a_bucket"
        folder_path = "TFT"
        bq_table = "primeval-proton-449808-i6.TFT_dataset.match_participants"
        load_transformed_data(bucket_name, folder_path, project_id, bq_table)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing cloud event: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500