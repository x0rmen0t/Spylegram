import asyncio
import base64
import sys
from typing import Optional

from telethon import TelegramClient, hints
from telethon.errors import BadRequestError, FloodWaitError, RPCError, ServerError
from telethon.tl.types import Message

from src.channel import get_channel_username, get_channel_info_rows
from src.db import DatabaseManager
from src.logging_config import get_logger
from src.message import create_message_data, get_first_message_date, get_fwd_channel_username
from src.utils import async_retry

app_logger = get_logger("app")


async def init_telegram_client(session_name: str, phone: str, api_id: int, api_hash: str) -> TelegramClient:
    try:
        client = TelegramClient(session_name, int(api_id), api_hash)
        await client.connect()

        if await client.is_user_authorized():
            app_logger.info("Client is authorized.")
            return client

        app_logger.info("Client is not authorized. Sending code request.")
        await client.send_code_request(phone)
        await client.sign_in(phone, input("Enter the code from the Telegram app: "))
        return client
    except Exception as e:
        app_logger.error("Error during authentication: %s", str(e))
        sys.exit()


async def validate_channel(client: TelegramClient, channel: str) -> Optional[hints.EntityLike]:
    try:
        app_logger.info("Processing channel %s", channel)
        return await client.get_entity(channel)
    except Exception as err:
        app_logger.error("Invalid channel %s: %s", channel, err)
        return None


async def process_channel(client: TelegramClient, channel_url: str, channel_entity: hints.EntitiesLike,
                          db: DatabaseManager) -> None:
    tg_channel_username = channel_entity.username

    if not tg_channel_username:
        app_logger.warning("Channel entity has no username. Skipping.")
        return

    app_logger.info("Checking if channel '%s' is in DB", tg_channel_username)
    if not await db.is_channel_in_database(tg_channel_username):
        app_logger.info("Channel '%s' not found. Saving info.", tg_channel_username)
        await create_and_save_channel_info(client, channel_url, channel_entity, db)
    else:
        app_logger.info("Channel '%s' found in DB.", tg_channel_username)


async def create_and_save_channel_info(client: TelegramClient, channel_url: str, channel_entity: hints.EntitiesLike,
                                       db: DatabaseManager) -> None:
    try:
        creation_date = await get_first_message_date(client, channel_url)
        channel_info = get_channel_info_rows(channel_url, creation_date, channel_entity)
        await db.save_channel_record(channel_info)
    except Exception as e:
        app_logger.error("Error saving channel info: %s", str(e))


def get_message_iterator(client: TelegramClient, channel: int, db_message_id: Optional[int], limit: Optional[int]):
    return client.iter_messages(
        channel,
        reverse=True,
        limit=limit or 1000,
        min_id=db_message_id if db_message_id else None
    )


async def download_messages(
        client: TelegramClient, db: DatabaseManager, channel: hints.EntityLike, db_message_id=None, limit=None
) -> None:
    if db_message_id is None:
        # Start downloading all messages from the beginning of the channel with hardcoded limit 1000
        iterator = client.iter_messages(channel, reverse=True, limit=1000)
    else:
        iterator = client.iter_messages(
            channel, limit=limit, min_id=db_message_id, reverse=True
        )

    async for message in iterator:
        app_logger.info("Processing message %s", message.id)
        await process_and_save_message(client, db, message)


async def check_and_save_reactions(
        db: DatabaseManager, message: Message, channel_id: int
) -> None:
    if message.reactions and message.reactions.results:
        for reaction_result in message.reactions.results:
            try:
                reaction = reaction_result.reaction
                count = int(reaction_result.count)

                # Defaults
                emoticon = "unknown"
                document_id = None
                emoticon_base64 = None

                if hasattr(reaction, "emoticon"):
                    emoticon = reaction.emoticon
                elif hasattr(reaction, "document_id"):
                    document_id = reaction.document_id
                    emoticon = f":custom:{document_id}"
                    emoticon_base64 = base64.b64encode(
                        document_id.to_bytes(8, "big")
                    ).decode()

                app_logger.info("Saving reaction: %s (%d)", emoticon, count)

                await db.save_reactions(
                    message.id,
                    channel_id,
                    emoticon,
                    count,
                    document_id=document_id,
                    emoticon_base64=emoticon_base64,
                )

            except Exception as e:
                app_logger.error(
                    "Error saving reaction for message %s: %s", message.id, str(e)
                )


async def process_and_save_message(client: TelegramClient, db: DatabaseManager, message: Message) -> None:
    try:
        channel_id = message.peer_id.channel_id
        channel_username = await get_channel_username(client, channel_id)
        if not channel_username:
            app_logger.warning("Missing username for channel ID %s", channel_id)
            return

        last_id = await db.get_last_processed_message_id(channel_id)

        if message.id >= last_id:
            await saving_data_to_db(channel_id, channel_username, client, db, message)

    except (FloodWaitError, ServerError, RPCError, BadRequestError) as e:
        app_logger.error("Error processing message %s: %s", message.id, type(e).__name__, exc_info=True)


@async_retry(retries=3, delay=1, backoff=2, exceptions=(Exception,))
async def saving_data_to_db(
        channel_id: int,
        channel_username: str,
        client: TelegramClient,
        db: DatabaseManager,
        message: Message
) -> None:
    try:
        fwd_username, tg_link = await get_fwd_channel_username(client, message) if message.fwd_from else (None, None)
        message_data = create_message_data(message, channel_id, channel_username, fwd_username, tg_link)
        await db.save_message_record(message_data)

        tasks = await asyncio.gather(
            check_and_save_reactions(db, message, channel_id),
            db.update_last_processed_message_id(channel_id, message.id),
            return_exceptions=True
        )

        for result in tasks:
            if isinstance(result, Exception):
                app_logger.error("Error during saving task: %s", str(result))
