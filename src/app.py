import json
import os
import sys
from typing import Optional

from telethon import TelegramClient, hints
from telethon.errors import (BadRequestError, FloodWaitError, RPCError,
                             ServerError, InputFetchFailError, TypeNotFoundError)
from telethon.tl import types
from telethon.tl.types import (InputMessagesFilterDocument, Message,
                               MessageMediaPhoto)
from telethon.utils import get_appropriated_part_size
from tqdm import tqdm

from src.channel import get_channel_info_rows, get_channel_username
from src.db import Database
from src.logging_config import get_logger
from src.message import (create_message_data, get_first_message_date,
                         get_fwd_channel_username)
from src.utils import (callback_document, callback_photo, get_document_name,
                       get_mime_type, read_binary_file)


app_logger = get_logger("app")
THRESHOLD_SIZE_IN_MB = 500
MESSAGES_WITH_BIG_FILES = {}

async def init_telegram_client(
        session_name, phone: str, api_id: int, api_hash: str
) -> TelegramClient:
    try:
        client = TelegramClient(session_name, int(api_id), api_hash)
        await client.connect()

        if await client.is_user_authorized():
            app_logger.info("Client is authorized.")
            return client
        else:
            app_logger.info(
                "Client is not authorized! Sending code request to telegram app."
            )
            await client.send_code_request(phone)
            await client.sign_in(phone, input("Enter the code from the Telegram app: "))
            return client
    except Exception as e:
        app_logger.error(
            "Error occurred while during authentication of the user:\n\t%s" % str(e)
        )
        sys.exit()


async def validate_channel(client: TelegramClient, channel: str) -> Optional[hints.EntityLike]:
    try:
        app_logger.info("Processing channel %s" % channel)
        channel_entity = await client.get_entity(channel)
        return channel_entity
    except Exception as err:
        app_logger.error(f"Invalid channel: {channel}. Error: {err}")
        return None


async def process_channel(
        client: TelegramClient,
        channel_url: str,
        channel_entity: hints.EntitiesLike,
        db: Database,
) -> None:
    tg_channel_name = channel_entity.username
    app_logger.info("Checking if channel name %s is in the db" % tg_channel_name)
    is_in_database = await db.is_channel_in_database(tg_channel_name)
    if is_in_database:
        app_logger.info("Channel %s was found in the db." % tg_channel_name)
    else:
        app_logger.info(
            "Channel %s was not found in the db. Adding channel to the db."
            % tg_channel_name
        )
        await create_and_save_channel_info(client, channel_url, channel_entity, db)


async def create_and_save_channel_info(
        client: TelegramClient,
        channel_url: str,
        channel_entity: hints.EntitiesLike,
        db: Database,
) -> None:
    try:
        channel_creation_date = await get_first_message_date(client, channel_url)
        channel_information = get_channel_info_rows(
            channel_url, channel_creation_date, channel_entity
        )
        await db.save_channel_record(channel_information)
    except Exception as e:
        app_logger.error(
            "Exception %s occured while obtaining and saving channel information" % str(e)
        )


async def download_messages(
        client: TelegramClient, db: Database, channel: str, db_message_id=None, limit=None
) -> None:
    if db_message_id is None:
        # Start downloading all messages from the beginning of the channel with hardcoded limit 1000
        iterator = client.iter_messages(channel, reverse=True, limit=1000)
    else:
        iterator = client.iter_messages(
            channel, limit=limit, min_id=db_message_id, reverse=True
        )

    async for message in iterator:
        app_logger.info("Processing current message %s" % message)
        await process_and_save_message(client, db, channel, message)
        # Update the checkpoint with the ID of the last successfully processed message
        await db.update_last_processed_message_id(channel, message.id)


async def check_and_save_reactions(
        db: Database, message: Message, channel_id: int, channel_username: str
) -> None:
    if message.reactions:
        try:
            reaction_results_list = message.reactions.to_dict()["results"]
            for data in reaction_results_list:
                emoticon = data["reaction"]["emoticon"]
                count = data["count"]
                app_logger.info("Saving emoticons to db")
                await db.save_reactions(
                    message.id, channel_id, channel_username, emoticon, count
                )
        except Exception as e:
            print(e, "emoticon not found")


async def check_and_save_photo(
        client: TelegramClient,
        db: Database,
        message: Message,
        channel_id: int,
        channel_username: str,
) -> None:
    """
    Check if media needs to be downloaded and save it to the database if required.

    Args:
        :param client (TelegramClient): The Telegram client instance.
        :param db (Database): The database instance for storing media.
        :param message (Message): The Telegram message to check for media.
        :param channel_username: The Telegram name
        :param channel_id: The Telegram channel id
    """

    try:
        if message.media and isinstance(message.media, MessageMediaPhoto):
            photo_id: int = message.media.photo.id
            app_logger.info(
                "Checking if %s for message %s is in db." % (photo_id, message.id)
            )
            is_image_in_db = await db.is_image_in_db(message.id, photo_id)
            if not is_image_in_db:
                app_logger.info("Saving %s for message %s to db." % (photo_id, message.id))
            blob = await client.download_media(
                message, bytes, progress_callback=callback_photo
            )  # Download to memory
            await db.save_image_blob(
                channel_id, channel_username, message.id, photo_id, blob
            )
    except Exception as e:
        app_logger.error("Error processing photo %s:" % str(e))


async def write_message_ids_to_file():
    try:
        with open("messages_with_big_files.json", "w") as file:
            json.dump(MESSAGES_WITH_BIG_FILES, file)
        app_logger.info("Message IDs written to 'messages_with_big_files.json'")
    except Exception as e:
        app_logger.error("Error writing message IDs to file: %s" % str(e))


async def process_and_save_message(
        client: TelegramClient, db: Database, channel: str, message: Message
) -> None:
    """
    Process and save a Telegram message to the database.

    Args:
        client (TelegramClient): The Telegram client instance.
        db (Database): The database instance for storing messages.
        channel (str): The name of the Telegram channel.
        message (Message): The Telegram message to process and save.
    """
    try:
        channel_id = message.peer_id.channel_id
        channel_username = await get_channel_username(client, channel_id)

        last_message_id_in_db, from_channel = await db.get_last_message_record(channel)
        app_logger.info(
            "Last message id saved in the database is %s." % last_message_id_in_db
        )
        app_logger.info(
            "Comparing message %s from the channel %s with last_message_id_in_db %s."
            % (message.id, channel_username, last_message_id_in_db)
        )

        if last_message_id_in_db == 0:
            app_logger.info(
                "No messages found in db. Starting to save all messages from the channel to db."
            )
            await saving_data_to_db(channel_id, channel_username, client, db, message)

        if message.id > last_message_id_in_db:
            app_logger.info(
                "Some messages missing from the db. Downloading missing message with id %s from channel %s"
                % (message.id, channel_username)
            )
            await saving_data_to_db(channel_id, channel_username, client, db, message)

        # all messages are in db
        if message.id == last_message_id_in_db:
            return

    except (FloodWaitError, ServerError, RPCError, BadRequestError) as e:
        app_logger.error(
            "Error processing message %s: %s" % (message.id, type(e).__name__),
            exc_info=True,
        )


async def saving_data_to_db(
        channel_id: int,
        channel_username: str,
        client: TelegramClient,
        db: Database,
        message: Message,
) -> None:
    fwd_from_channel_username, tg_link = (
        await get_fwd_channel_username(client, message)
        if message.fwd_from
        else (None, None)
    )
    message_data = create_message_data(
        message, channel_id, channel_username, fwd_from_channel_username, tg_link
    )
    app_logger.info(
        "Saving message %s from %s to the db."
        % (message_data.message_id, channel_username)
    )
    await db.save_message_record(message_data)
    await check_and_save_photo(client, db, message, channel_id, channel_username)
    await check_and_save_reactions(db, message, channel_id, channel_username)


async def download_document(
        client: TelegramClient, db: Database, channel_id: int, channel_username: str
) -> None:
    total_documents_in_channel = await client.get_messages(
        channel_username, 0, filter=InputMessagesFilterDocument
    )
    dir_name = f"{channel_username}_downloads"
    processed_messages = set()

    with tqdm(total=total_documents_in_channel.total, unit=" documents") as pbar_total:
        async for message in client.iter_messages(channel_username, filter=InputMessagesFilterDocument):
            if not message.media or not isinstance(message.media, types.MessageMediaDocument):
                continue  # Skip messages without a document
            if message.id in processed_messages:
                continue  # Skip already processed messages
            document = message.media.document
            app_logger.info("Processing document in the message %s", message.id)
            if document is not None:
                mime_type = get_mime_type(message)
                file_size_in_mb = get_appropriated_part_size(document.size)
                file_name = get_document_name(message)

            if file_size_in_mb < THRESHOLD_SIZE_IN_MB:
                os.makedirs(dir_name, exist_ok=True)
                try:
                    file_path = os.path.join(dir_name, file_name)
                    if os.path.exists(file_path):
                        app_logger.warning(
                            "Channel [%s] message id [%s]File %s already exists at %s. Skipping download."
                            % (channel_username, message.id, file_name, file_path)
                        )
                        continue

                    await client.download_media(
                        message, file=file_path, progress_callback=callback_document
                    )
                    pbar_total.update(1)
                    app_logger.info(
                        "Downloaded document %s to %s for message %s"
                        % (file_name, file_path, message.id)
                    )
                    file_blob = read_binary_file(file_path)
                    if file_blob is not None:
                        await db.insert_document_blob(
                            message.id,
                            channel_id,
                            channel_username,
                            mime_type,
                            file_name,
                            file_blob,
                        )
                        app_logger.info(
                            "Downloaded and saved document name [%s] to the db."
                            % file_name
                        )
                    else:
                        app_logger.warning(
                            "Document with the name [%s] was not found for message %s. Skipping."
                            % (file_name, message)
                        )
                except (
                        FloodWaitError, ServerError, RPCError, BadRequestError, InputFetchFailError,
                        TypeNotFoundError) as e:
                    app_logger.error(
                        "Error downloading document from message %s: %s" %
                        (message.id, type(e).__name__),
                        exc_info=True,
                    )
                except AttributeError:
                    pass
            else:
                app_logger.info(
                    "[Message %s] has file size %s MB bigger than %s MB. Process later."
                    % (message.id, file_size_in_mb, THRESHOLD_SIZE_IN_MB)
                )
                MESSAGES_WITH_BIG_FILES.setdefault(channel_username, []).append(
                    message.id
                )
                app_logger.info("Savind id of message with humongous size to a file")
                await write_message_ids_to_file()
