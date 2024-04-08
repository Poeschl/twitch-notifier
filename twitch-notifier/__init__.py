import asyncio
from base64 import b64decode
from os import getenv
from os.path import dirname, realpath

from discord import SyncWebhook
from mastodon import Mastodon, MastodonError
from twitchAPI.twitch import Twitch
from twitter import Api, TwitterError
from yaml import YAMLError, safe_load


def read_config():
    script_path = dirname(realpath(__file__))
    # Environment config is the config file encoded in base64
    env_config = getenv("CONFIG")

    if env_config is None:
        with open(script_path + "/../config.yaml", 'r', encoding="utf-8") as stream:
            try:
                local_config = safe_load(stream)
                return local_config
            except YAMLError as exc:
                print("Error on file config read. {}".format(exc))
                return {}
    else:
        print("Using environment config")
        try:
            local_config = safe_load(b64decode(env_config))
            return local_config
        except YAMLError as exc:
            print("Error on environment config read. {}".format(exc))
            return {}


def login_twitch(config: dict):
    return Twitch(config["twitch"]["app_id"], config["twitch"]["app_secret"])


def login_mastodon(config: dict):
    return Mastodon(api_base_url=config["mastodon"]["instance"],
                    client_id=config["mastodon"]["client_token"],
                    client_secret=config["mastodon"]["client_secret"],
                    access_token=config["mastodon"]["access_token"])


def login_twitter(config: dict):
    return Api(consumer_key=config["twitter"]["api_key"],
               consumer_secret=config["twitter"]["api_secret"],
               access_token_key=config["twitter"]["access_token"],
               access_token_secret=config["twitter"]["access_token_secret"])


def send_mastodon_troet(config: dict, content: str):
    if config["mastodon"]["client_token"] is None:
        print("No mastodon client token given, skipping mastodon posting.")
        return

    try:
        mastodon = login_mastodon(config)
        if not config["dry_run"]:
            mastodon.status_post(content,
                                 visibility="unlisted")
        else:
            print("Would have posted on Mastodon:\n" + content)
    except MastodonError as ex:
        print("Could not send mastodon notification")
        print(ex)


def send_twitter(config: dict, content: str):
    if config["twitter"]["api_key"] is None:
        print("No twitter api key given, skipping twitter posting.")
        return

    try:
        twitter = login_twitter(config)
        if not config["dry_run"]:
            twitter.PostUpdate(content)
        else:
            print("Would have posted on Twitter:\n" + content)
    except TwitterError as ex:
        print("Could not send twitter notification")
        print(ex)


def send_discord(config: dict, content: str):
    if config["discord"]["webhook"] is None:
        print("No Discord webhook url given, skipping Discord posting.")
        return

    webhook = SyncWebhook.from_url(config["discord"]["webhook"])
    if not config["dry_run"]:
        webhook.send(content)
    else:
        print("Would have posted on Discord:\n" + content)


def get_notification_text(config: dict, stream: dict):
    return config["notification_template"].format(title=stream["title"], game=stream["game_name"])


def get_game_switching_text(config: dict, stream: dict):
    return config["game_switch_template"].format(title=stream["title"], game=stream["game_name"])


async def check_loop(config: dict):
    currently_streaming = None
    current_game = ""
    while True:
        twitch = login_twitch(config)
        user = twitch.get_users(logins=config["twitch"]["watched_channel"])["data"][0]
        print("Checking user {} to be online".format(user["display_name"]))
        current_streams: list = twitch.get_streams(user_id=user["id"])["data"]

        if getenv("DEBUG"):
            current_streams.append({'id': '12345', 'user_id': '123414362', 'user_login': 'mr_poeschl', 'user_name': 'Mr_Poeschl',
                                    'game_id': '45z2546', 'game_name': 'Tinykin', 'type': 'live',
                                    'title': 'Bleiben wir bei kleinen Wesen und spielen Tinykin!', 'viewer_count': 105,
                                    'started_at': '2022-1sdf1-06j27:06Z', 'language': 'de',
                                    'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_mr_poeschl-{width}x{height}.jpg',
                                    'tag_ids': ['9166ad14-41f1-4b04-a3b8-c8eb838c6be6'], 'is_mature': True})

        if currently_streaming is None:
            currently_streaming = len(current_streams) > 0
            if currently_streaming:
                stream = current_streams[0]
                current_game = stream["game_id"]

        else:
            if len(current_streams) > 0:
                stream = current_streams[0]
                if not currently_streaming and stream["type"] == "live":
                    currently_streaming = True
                    current_game = stream["game_id"]
                    print("Currently streaming, sending notifications")
                    stream_start_text = get_notification_text(config, stream)
                    send_mastodon_troet(config, stream_start_text)
                    send_twitter(config, stream_start_text)
                    send_discord(config, stream_start_text)
                elif currently_streaming and current_game != stream["game_id"]:
                    current_game = stream["game_id"]
                    print("Game changed, sending update posts")
                    game_switch_text = get_game_switching_text(config, stream)
                    send_mastodon_troet(config, game_switch_text)
                    send_twitter(config, game_switch_text)
                    send_discord(config, game_switch_text)
            else:
                currently_streaming = False

        await asyncio.sleep(config["update_interval_seconds"])


def main():
    print("Starting Notifier")
    stored_config = read_config()
    stored_config["dry_run"] = getenv("DRY_RUN", False)
    asyncio.run(check_loop(stored_config))


if __name__ == '__main__':
    exit(main())
