# Twitch-Notifier

A python script which posts a notification to my social media accounts on Mastodon and Twitter.

## Config

The bot is controlled via a configuration file with the name `config.yaml` in the directory above the script.
An empty config can be found in `config.sample.yaml`.
All keys should be self-explaining.

Additionally, the config can also be provided by an environment variable `CONFIG`.
For that the config file needs to be base64 encoded and put into the value of the variable.
This is useful for the execution in a docker container.

```shell
export CONFIG="$(base64 config.yaml)"
```

## Run it

### Directly with python3

To run the script directly navigate to the project folder and execute the following.

```shell
# Setup venv
python3 -m venv .venv
source .venv/Scripts/activate

# Install requirements
pip3 install -r requirements.txt

# Execute application
python3 twitch-notifier/__init__.py
```

### Via Docker

//TBD