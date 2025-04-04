import aiohttp
import requests
from secret import RIOTAPIKEY

async def get_riot_id(name, tagline):
    summoner_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tagline}?api_key={RIOTAPIKEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(summoner_url) as response:
            if response.status == 200:
                data = await response.json()
                return data["puuid"]
            else:
                return f"Error fetching riot id: {response.status}"

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