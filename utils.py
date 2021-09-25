import requests
import config


def get_token(code: str):
    data = {
        'client_id': config.CLIENT_ID,
        'client_secret': config.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.REDIRECT_URI,
        'scope': 'identify guilds'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    resp = requests.post(
        "https://discord.com/api/oauth2/token", data=data, headers=headers)
    resp.raise_for_status()
    return resp.json()['access_token']


def get_user_info(token):
    resp = requests.get("https://discord.com/api/v6/users/@me",
                        headers={"Authorization": f"Bearer {token}"})

    resp.raise_for_status()
    return resp.json()


def get_user_info_by_id(user_id):
    token = config.BOT_TOKEN
    resp = requests.get(f"https://discord.com/api/v6/users/{user_id}",
                        headers={"Authorization": f"Bot {token}"})

    resp.raise_for_status()

    json = {
        'user_name': f'{resp.json()["username"]}#{resp.json()["discriminator"]}',
        'avatar_url': f'https://cdn.discordapp.com/avatars/{resp.json()["id"]}/{resp.json()["avatar"]}.png'if resp.json()["avatar"] is not None else f'https://www.shitpostbot.com/resize/585/400?img=%2Fimg%2Fsourceimages%2Fdefault-discord-icon-5b254285e1034.png"'
    }
    return json


def get_user_guilds(token: str):
    resp = requests.get("https://discord.com/api/v6/users/@me/guilds",
                        headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def get_bot_guilds():
    token = config.BOT_TOKEN
    resp = requests.get("https://discord.com/api/v6/users/@me/guilds",
                        headers={"Authorization": f"Bot {token}"})
    resp.raise_for_status()
    return resp.json()


def get_mutual_guilds(user_guilds: list, bot_guilds: list):
    return [guild for guild in user_guilds if (guild['permissions'] & 0x20) == 0x20]


def get_guild_data(guild_id: int):
    token = config.BOT_TOKEN
    resp = requests.get(
        f"https://discord.com/api/v6/guilds/{guild_id}", headers={"Authorization": f"Bot {token}"})

    try:
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError:
        return None


def get_guild_channels(guild_id: int):
    token = config.BOT_TOKEN
    resp = requests.get(
        f"https://discord.com/api/v6/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"}
    )
    channels = []
    for channel in resp.json():
        if channel['type'] == 0:
            channels.append(channel)

    return channels


def get_channel_by_id(guild_id: int, channel_id: str):
    token = config.BOT_TOKEN
    resp = requests.get(
        f"https://discord.com/api/v6/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"}
    )
    for channel in resp.json():
        if channel["type"] == 0 and channel["id"] == channel_id:
            channel_name = channel["name"]

    return channel_name


def get_channel_by_name(guild_id: int, channel_name: str):
    token = config.BOT_TOKEN
    resp = requests.get(
        f"https://discord.com/api/v6/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"}
    )
    for channel in resp.json():
        if channel['type'] == 0 and channel['name'] == channel_name:
            channel_id = channel['id']

    return channel_id
