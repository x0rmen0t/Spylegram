import asyncio
import os
from typing import List

import yaml
from dotenv import load_dotenv

from src.app import (download_document, download_large_media,
                     download_messages, init_telegram_client, process_channel)
from src.db import Database
from src.logging_config import logger
from src.message import get_last_message_id

load_dotenv()


def get_channels(yml_file: str) -> List[str]:
    try:
        with open(yml_file, "r") as file:
            return yaml.safe_load(file)["channels"]
    except yaml.YAMLError as e:
        logger.error("Error while reading yml file:\t%s" % type(e).__name__)


async def main():
    client = await init_telegram_client(
        "snooper", os.getenv("PHONE"), int(os.getenv("API_ID")), os.getenv("API_HASH")
    )
    logger.info("Telegram client initialized")
    db = Database(os.getenv("DB_NAME"))
    await db.create_schema()
    logger.info("Connection to database created")
    tasks = []
    channel_list = get_channels("telegram_channels.yml")
    try:
        for channel in channel_list:
            channel_entity = await client.get_entity(channel)
            tg_channel_name = channel_entity.username
            logger.info("Processing channel %s information" % tg_channel_name)
            await process_channel(client, channel, channel_entity, db)

            last_message_id_in_db, from_channel = await db.get_last_message_record(
                tg_channel_name
            )
            logger.info(
                "Last message in db is %s, from channel > %s" %
                (last_message_id_in_db,
                from_channel)
            )

            if last_message_id_in_db > 0:
                # check if we have any messages in db.
                last_message_in_channel = await get_last_message_id(
                    client, tg_channel_name
                )
                logger.info(
                    "Last message_id %s in our db, last message id in channel %s channel %s" %
                    (last_message_id_in_db,
                     last_message_in_channel,
                     tg_channel_name),
                )

                if last_message_id_in_db < last_message_in_channel:
                    await download_messages(
                        client, db, tg_channel_name, db_message_id=last_message_id_in_db
                    )

            if last_message_id_in_db == 0:
                # we don't have messages yet, download all of them
                logger.info("Downloading all messages for channel %s" % tg_channel_name)
                await download_messages(client, db, tg_channel_name, db_message_id=None)

            await download_document(client, db, channel_entity.id, tg_channel_name)
            await asyncio.sleep(1)
            tasks.append(download_large_media(client, tg_channel_name))
            await asyncio.sleep(1)

        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("An error %s occurred" % str(e))
        pass


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
