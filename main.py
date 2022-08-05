import requests
import os, json, time

from dotenv import load_dotenv

load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')
GUILD_ID = os.getenv('GUILD_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')

PLAYER_JSON = os.getenv('PLAYER_JSON')

players = json.loads(PLAYER_JSON)


def callAPI(region, endpoint):
    res = requests.get(f"https://{region}.api.riotgames.com{endpoint}",
        headers = { "X-Riot-Token": RIOT_API_KEY })

    if res.status_code != 200:
        raise Exception(f"Non-200 Response. Body: {res.text}")

    return res.json()

def getSummonerID(region, summonerName):
    return callAPI(region, f"/lol/summoner/v4/summoners/by-name/{summonerName}")["id"]

def getPlayerInfo(region, SummonerID):
    return callAPI(region, f"/lol/league/v4/entries/by-summoner/{SummonerID}")


def parsePlayerInfo(playerInfoJSON):
    # Solo/Duo W:L SII WLWLN 
    # Flex W:L SII     WLLNN

    flexRoleString = ""
    sdRoleString = ""

    for playerQueue in playerInfoJSON:
        
        queue      = playerQueue["queueType"]
        tier       = playerQueue["tier"]
        rank       = playerQueue["rank"]
        wins       = playerQueue["wins"]
        losses     = playerQueue["losses"]
        miniSeries = playerQueue.get("miniSeries")
        
        if tier == "GRANDMASTER":
            tier = "GR"
        else:
            tier = tier[0]

        miniSeriesProgress = ""

        if miniSeries is not None:
            miniSeriesProgress = miniSeries["progress"]
            miniSeriesProgress = miniSeriesProgress.replace("N", "⚪").replace("W", "🟢").replace("L", "🔴")

        if queue == "RANKED_FLEX_SR":
            flexRoleString = f"Flex {wins}:{losses} {tier}{rank}"

            if miniSeriesProgress != "":
                flexRoleString += f" {miniSeriesProgress}"
        elif queue == "RANKED_SOLO_5x5":
            sdRoleString = f"Solo/Duo {wins}:{losses} {tier}{rank}"

            if miniSeriesProgress != "":
                sdRoleString += f" {miniSeriesProgress}"
        else:
            raise Exception(f"Unknown queue: {queue}")
    
    flexRoleString = flexRoleString if flexRoleString != "" else "NO Flex DATA"
    sdRoleString = sdRoleString if sdRoleString != "" else "NO Solo/Duo DATA"

    return (flexRoleString, sdRoleString)


def changeRole(ROLE_ID, roleName):

    res = requests.patch(f"https://discord.com/api/v9/guilds/{GUILD_ID}/roles/{ROLE_ID}",
        headers = {
            'Authorization': f"Bot {BOT_TOKEN}",
            'Content-Type': 'application/json'
        }, data = json.dumps({ "name": roleName }))

    if res.status_code != 200:
        raise Exception(f"Non-200 Response. Body: {res.text}")


def main():
    for key, val in players.items():

        summonerRegion = val.get("region", "na1")
        
        try:
            encSummID = getSummonerID(summonerRegion, key) 
            playerInfo = getPlayerInfo(summonerRegion, encSummID)
            roles = parsePlayerInfo(playerInfo)

            print(roles)

            for i, role in enumerate(roles):
                changeRole(val["roles"][i], role)

        except Exception as e:
            print(f"Failed for {key}. Reason: {e}")
            continue

        time.sleep(2)
        

if __name__ == "__main__":
    main()
