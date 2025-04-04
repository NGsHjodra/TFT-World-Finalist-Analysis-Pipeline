import yaml
import asyncio
from Riot.function import get_riot_id

# world finalist + participants
player_list = [
    ["Dishsoap", "NA2", "NA"],
    ["M8 Jedusor", "12345", "EUW"],
    ["eusouolucas", "1111", "BR"],
    ["Deis1k", "EUW", "EUW"],
    ["Só bio", "BR1", "BR"],
    ["VIT prestivent", "123", "NA"],
    ["RCS Xperion", "EUW11", "EUW"],
    ["MIH TarteMan", "EUW", "EUW"],
    ["강선종", "KR123", "KR"],
    ["Boomhae", "0901", "SEA"],
    ["빈 틈","123", "KR"],
    ["META SpencerTFT", "TFT", "NA"],
]

# get puuid from player_list
async def get_puuid(player_list):
    for player in player_list:
        puuid = await get_riot_id(player[0], player[1])
        player.append(puuid)
    return player_list

player_list = asyncio.run(get_puuid(player_list))

# save player_list to a yaml file
with open("config/player_list.yaml", "w") as file:
    yaml.dump(player_list, file)