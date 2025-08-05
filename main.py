import argparse
import asyncio
import os
from typing import Optional, List
import yaml
from dotenv import load_dotenv

from src.app import download_messages, init_telegram_client, process_channel, validate_channel
from src.db import DatabaseManager
from src.logging_config import get_logger
from src.message import get_last_message_id

main_logger = get_logger("main")
load_dotenv()

db = DatabaseManager()


def get_user_arg():
    parser = argparse.ArgumentParser(
        prog='Spylegram',
        description='Downloads messages from Telegram Channels')
    parser.add_argument('-c', '--channel', type=str,
                        help='Telegram channel URL or username')
    parser.add_argument('-p', '--path_to_yml', type=str,
                        help='Path to YAML file with Telegram channels')
    return parser.parse_args()


def get_channels(yml_file: str) -> Optional[List[str]]:
    try:
        with open(yml_file, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            return yaml_data.get("channels") if isinstance(yaml_data, dict) else None
    except Exception as e:
        main_logger.error("Error reading YAML file: %s", str(e))
        return None


async def main():
    client = await init_telegram_client(
        os.getenv("TG_SESSION_NAME"),
        os.getenv("PHONE"),
        int(os.getenv("API_ID")),
        os.getenv("API_HASH")
    )
    main_logger.info("Telegram client initialized")

    await db.connect()
    main_logger.info("Connected to the database")

    args = get_user_arg()
    if args.channel:
        channel_list = [args.channel]
    else:
        yaml_path = args.path_to_yml or "telegram_channels.yml"
        channel_list = get_channels(yaml_path)
        if not channel_list:
            main_logger.error("No channels found in YAML file: %s", yaml_path)
            return

    for channel in channel_list:
        try:
            main_logger.info("Validating channel: %s", channel)
            validated_channel_entity = await validate_channel(client, channel)
            if validated_channel_entity is None:
                main_logger.warning("Channel validation failed: %s", channel)
                continue

            tg_channel_name = validated_channel_entity.username
            if not tg_channel_name:
                main_logger.warning("Channel has no username, skipping: %s", channel)
                continue

            original_channel_id = validated_channel_entity.id
            main_logger.info("Processing channel: %s (%s)", tg_channel_name, original_channel_id)
            await process_channel(client, channel, validated_channel_entity, db)

            last_message_id_in_db = await db.get_last_processed_message_id(original_channel_id)

            # Resolve proper entity for iter_messages()
            resolved_entity = await client.get_entity(validated_channel_entity)

            if last_message_id_in_db is None or last_message_id_in_db == 0:
                main_logger.info("Downloading all messages for new channel: %s", tg_channel_name)
                await download_messages(client, db, resolved_entity, db_message_id=None)
            else:
                last_message_in_channel = await get_last_message_id(client, tg_channel_name)
                if last_message_in_channel is None:
                    main_logger.warning("Could not fetch last message ID from Telegram for %s", tg_channel_name)
                    continue

                main_logger.info("DB last_message_id: %s | Channel last_message_id: %s",
                                 last_message_id_in_db, last_message_in_channel)

                if last_message_id_in_db < last_message_in_channel:
                    main_logger.info("Downloading missing messages from ID %s for %s",
                                     last_message_id_in_db, tg_channel_name)
                    await download_messages(client, db, resolved_entity, db_message_id=last_message_id_in_db)
                else:
                    main_logger.info("Channel %s is up to date", tg_channel_name)

        except asyncio.CancelledError:
            pass
        except ValueError as e:
            main_logger.error("Invalid channel entity: %s", e)
        except Exception as e:
            main_logger.error("Unexpected error: %s", str(e))


    await client.disconnect()
    await db.disconnect()
    main_logger.info("Disconnected cleanly.")



if __name__ == "__main__":
    asyncio.run(main())
