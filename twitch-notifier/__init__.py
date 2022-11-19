import asyncio
from base64 import b64decode
from os import getenv
from os.path import dirname, realpath

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


def send_mastodon_troet(config: dict, stream: dict):
    if config["mastodon"]["client_token"] is None:
        print("No mastodon client token given, skipping mastodon posting.")
        return

    try:
        mastodon = login_mastodon(config)
        text = get_notification_text(config, stream)
        if not config["dry_run"]:
            mastodon.status_post(text,
                                 idempotency_key=stream["started_at"],
                                 visibility="unlisted")
        else:
            print("Would have posted on Mastodon:\n" + text)
    except MastodonError as ex:
        print("Could not send mastodon notification")
        print(ex)


def send_twitter(config: dict, stream: dict):
    if config["twitter"]["api_key"] is None:
        print("No twitter api key given, skipping twitter posting.")
        return

    try:
        twitter = login_twitter(config)
        text = get_notification_text(config, stream)
        if not config["dry_run"]:
            twitter.PostUpdate(text)
        else:
            print("Would have posted on Twitter:\n" + text)
    except TwitterError as ex:
        print("Could not send twitter notification")
        print(ex)


def get_notification_text(config: dict, stream: dict):
    return config["notification_template"].format(title=stream["title"], game=stream["game_name"])


async def check_loop(config: dict):
    currently_streaming = False
    while True:
        twitch = login_twitch(config)
        user = twitch.get_users(logins=config["twitch"]["watched_channel"])["data"][0]
        print("Checking user {} to be online".format(user["display_name"]))
        current_streams: list = twitch.get_streams(user_id=user["id"])["data"]

        if len(current_streams) > 0:
            stream = current_streams[0]
            if not currently_streaming and stream["type"] == "live":
                currently_streaming = True
                print("Currently streaming, sending notifications")
                send_mastodon_troet(config, stream)
                send_twitter(config, stream)
        else:
            currently_streaming = False

        await asyncio.sleep(config["update_interval_seconds"])


def main():
    print("Starting Notifier")
    stored_config = read_config()
    asyncio.run(check_loop(stored_config))


if __name__ == '__main__':
    exit(main())
