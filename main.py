import argparse
import asyncio
import os
from typing import List
from dotenv import load_dotenv
import yaml

from src.app import (download_document,
                     download_messages, init_telegram_client, process_channel, validate_channel)
from src.db import Database
from src.logging_config import get_logger
from src.message import get_last_message_id

load_dotenv()
main_logger = get_logger("main")

load_dotenv()


def get_user_arg():
    parser = argparse.ArgumentParser(
        prog='Spylegram',
        description='Downloads messages from Telegram Channels')
    parser.add_argument('-c','--channel', help='Enter the name of Telegram channel url for processing', type=str, action='store',
                        required=False)
    parser.add_argument('-p', '--path_to_yml', help='Enter path to the YAML file with Telegram channels',
                        type=str, action='store', required=False)
    args = parser.parse_args()
    return args


def get_channels(yml_file: str) -> List[str]:
    try:
        with open(yml_file, "r") as file:
            yaml_data = yaml.safe_load(file)
            if "channels" in yaml_data:
                return yaml_data["channels"]
            else:
                return yaml_data
            # return yaml.safe_load(file)["channels"]
    except yaml.YAMLError as e:
        main_logger.error("Error while reading yml file:\t%s" % type(e).__name__)


async def main():
    # Initialize Telegram client and database
    client = await init_telegram_client(
        os.getenv("TG_SESSION_NAME"), os.getenv("PHONE"), int(os.getenv("API_ID")), os.getenv("API_HASH")
    )
    main_logger.info("Telegram client initialized")
    db = Database(os.getenv("DB_NAME"))
    await db.create_schema()
    main_logger.info("Connection to database created")
    user_args = get_user_arg()
    if user_args.channel:
        channel_list = [get_channels("telegram_channels.yml")]
    elif user_args.path_to_yml:
        channel_list = get_channels(user_args.path_to_yml)
    else:
        channel_list = get_channels("telegram_channels.yml")

    # channel_list = get_channels("telegram_channels.yml")
    for channel in channel_list:
        try:
            validated_channel_entity = await validate_channel(client, channel)
            if validated_channel_entity is None:
                continue

            # Process the validated channel
            tg_channel_name = validated_channel_entity.username
            main_logger.info("Processing channel %s information" % tg_channel_name)
            await process_channel(client, channel, validated_channel_entity, db)

            last_message_id_in_db, from_channel = await db.get_last_message_record(tg_channel_name)
            main_logger.info(
                "Last message in db is number %s, from channel ---> %s" % (last_message_id_in_db, from_channel))

            if last_message_id_in_db > 0:
                # check if we have any messages in db.
                last_message_in_channel = await get_last_message_id(client, tg_channel_name)
                main_logger.info("Last message_id %s in our db, last message id in channel %s channel %s" %
                                 (last_message_id_in_db, last_message_in_channel, tg_channel_name))

                if last_message_id_in_db < last_message_in_channel:
                    await download_messages(client, db, tg_channel_name, db_message_id=last_message_id_in_db)

            if last_message_id_in_db == 0:
                # we don't have messages yet, download all of them
                main_logger.info("Downloading all messages for channel %s" % tg_channel_name)
                await download_messages(client, db, tg_channel_name, db_message_id=None)

            await download_document(client, db, validated_channel_entity.id, tg_channel_name)
        except asyncio.CancelledError:
            pass
        except ValueError as e:
            main_logger.error("Cannot find any entity corresponding to channel %s" % e)
        except Exception as e:
            main_logger.error(f"An error occurred in the main loop: {str(e)}")

    try:
        await client.disconnect()
        main_logger.info("Disconnected from Telegram.")
    except Exception as e:
        main_logger.error(f"Error during disconnect: {str(e)}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())