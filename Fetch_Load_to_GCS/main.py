import functions_framework
import asyncio
import yaml
import json
from flask import jsonify
from google.cloud import storage
# from Riot.function import get_match_ids, get_match_data
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

RIOTAPIKEY = os.getenv("RIOT_API_KEY")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

async def get_match_ids(puuid):
    summoner_url = f"https://sea.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=20&api_key={RIOTAPIKEY}"
    match_ids = requests.get(summoner_url)
    if match_ids.status_code == 200:
        return match_ids.json()
    else:
        return None
    
async def get_match_data(match_id):
    summoner_url = f"https://sea.api.riotgames.com/tft/match/v1/matches/{match_id}?api_key={RIOTAPIKEY}"
    match_data = requests.get(summoner_url)
    if match_data.status_code == 200:
        return match_data.json()
    else:
        return None

def match_exists_in_gcs(bucket_name, folder, match_id, project_id):
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"{folder}/raw_matches/{match_id}.json")
    return blob.exists()

async def process_match_data(player_list, bucket_name, destination_folder, project_id):
    for player in player_list:
        puuid = player[3]
        logger.info(f"Fetching match IDs for {player[0]}")
        match_ids = await get_match_ids(puuid)
        if match_ids:
            logger.info(f"Match IDs for {player[0]}: {match_ids}")
            for match_id in match_ids:
                logger.info(f"Fetching match data for {match_id}")
                # Check if match data already exists in GCS
                if match_exists_in_gcs(bucket_name, destination_folder, match_id, project_id):
                    logger.info(f"Match data for {match_id} already exists in GCS. Skipping.")
                    continue
                # Fetch match data
                try:
                    match_data = await get_match_data(match_id)
                    if match_data:
                        save_to_gcs(match_data, bucket_name, destination_folder, match_id)
                    else:
                        logger.error(f"Failed to fetch match data for {match_id}")
                except Exception as e:
                    logger.error(f"Error fetching match data for {match_id}: {e}")

def save_to_gcs(match_data, bucket_name, folder, match_id, project_id):
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"{folder}/raw_matches/{match_id}.json")
    blob.upload_from_string(json.dumps(match_data), content_type='application/json')
    logger.info(f"Match data for {match_id} saved to {bucket_name}/{folder}/raw_matches/{match_id}.json")

# fetch match history from riot api
@functions_framework.http
def main(request):
    if request.method != 'POST':
        return 'Method not allowed', 405
    try:
        request_json = request.get_json()
        if request_json is None:
            return 'Bad Request', 400
        logger.info(f"Request JSON: {request_json}")

        data = request.get_json(silent=True) or {}

        project_id = data.get("project_id")
        bucket_name = data.get("bucket_name")
        destination_folder = data.get("destination_folder", "TFT")

        #read player_list from yaml file
        with open("config/player_list.yaml", "r") as file:
            player_list = yaml.safe_load(file)

        logger.info(f"Player list: {player_list}")

        # process match data
        asyncio.run(process_match_data(player_list, bucket_name, destination_folder, project_id))
        return jsonify({
            "message": "Schedule fetched successfully",
            "bucket_name": bucket_name,
            "destination_folder": destination_folder,
            "project_id": project_id,
        }), 200

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return 'Internal Server Error', 500