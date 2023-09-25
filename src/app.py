import asyncio
import sys
import os
import time

from tqdm import tqdm
from telethon import TelegramClient, hints
from telethon.errors import FloodWaitError, ServerError, RPCError, BadRequestError
from telethon.tl.types import MessageMediaPhoto, InputMessagesFilterDocument, Message
from telethon.utils import get_appropriated_part_size

from src.channel import get_channel_info_rows, get_channel_username
from src.db import Database
from src.message import get_first_message_date, get_fwd_channel_username, create_message_data, get_message
from src.utils import read_binary_file, callback_photo, get_mime_type, get_document_name, callback_document
from src.logging_config import logger

THRESHOLD_SIZE_IN_MB = 500
MESSAGES_WITH_BIG_FILES = {}


async def init_telegram_client(session_name, phone: str, api_id: int, api_hash: str) -> TelegramClient:
    try:
        client = TelegramClient(session_name, int(api_id), api_hash)
        await client.connect()

        if await client.is_user_authorized():
            logger.info('Client is authorized.')
            return client
        else:
            logger.info('Client is not authorized! Sending code request to telegram app.')
            await client.send_code_request(phone)
            await client.sign_in(
                phone,
                input('Enter the code from the telegram app: ')
            )
            return client
    except Exception as e:
        logger.error('Error occurred while during authentication of the user:\n\t%s' % str(e))
        sys.exit()


async def process_channel(client: TelegramClient, channel_url: str, channel_entity: hints.EntitiesLike,
                          db: Database) -> None:
    tg_channel_name = channel_entity.username
    logger.info("Checking if channel name %s is in the db" % tg_channel_name)
    is_in_database = await db.is_channel_in_database(tg_channel_name)
    if is_in_database:
        logger.info("Channel %s was found in the db." % tg_channel_name)
    else:
        logger.info(f"Channel %s was not found in the db. Adding channel to the db." % tg_channel_name)
        await create_and_save_channel_info(client, channel_url, channel_entity, db)


async def create_and_save_channel_info(client: TelegramClient, channel_url: str, channel_entity: hints.EntitiesLike,
                                       db: Database) -> None:
    try:
        channel_creation_date = await get_first_message_date(client, channel_url)
        channel_information = get_channel_info_rows(channel_url, channel_creation_date, channel_entity)
        await db.save_channel_record(channel_information)
    except Exception as e:
        logger.error("Exception occured while obtaining and saving channel information", str(e))


async def download_messages(client: TelegramClient, db: Database, channel: str, db_message_id=None, limit=None) -> None:
    if db_message_id is None:
        # Start downloading all messages from the beginning of the channel, limit
        iterator = client.iter_messages(channel, reverse=True, limit=1000)
    else:
        iterator = client.iter_messages(channel, limit=limit, min_id=db_message_id, reverse=True)

    async for message in iterator:
        await process_and_save_message(client, db, channel, message)
        # Update the checkpoint with the ID of the last successfully processed message
        await db.update_last_processed_message_id(channel, message.id)


async def check_and_save_reactions(db: Database, message: Message, channel_id: int, channel_username: str) -> None:
    if message.reactions:
        reaction_results_list = message.reactions.to_dict()['results']
        for data in reaction_results_list:
            emoticon = data['reaction']['emoticon']
            count = data['count']
            logger.info("Saving emoticons to db")
            await db.save_reactions(message.id, channel_id, channel_username, emoticon, count)


async def check_and_save_photo(client: TelegramClient, db: Database, message: Message, channel_id: int,
                               channel_username: str) -> None:
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
            logger.info("Checking if %s for message %s is in db." % (photo_id, message.id))
            is_image_in_db = await db.is_image_in_db(message.id, photo_id)
            if not is_image_in_db:
                logger.info("Saving %s for message %s to db." % (photo_id, message.id))
            blob = await client.download_media(message, bytes, progress_callback=callback_photo)  # Download to memory
            await db.save_image_blob(channel_id, channel_username, message.id, photo_id, blob)
    except Exception as e:
        logger.error("Error processing photo %s:", str(e))


async def process_and_save_message(client: TelegramClient, db: Database, channel: str, message: Message) -> None:
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
        logger.info("Last message id saved in the database is %s." % last_message_id_in_db)
        logger.info("Comparing message %s from the channel with last_message_id_in_db %s." % (message.id,
                                                                                              last_message_id_in_db))

        if last_message_id_in_db == 0:
            logger.info("No messages found in db. Starting to save all messages from the channel to db.")
            await saving_data_to_db(channel_id, channel_username, client, db, message)

        if message.id > last_message_id_in_db:
            logger.info("Some messages missing from the db. Downloading missing message with id %s from channel %s" %
                        (message.id, channel_username))
            await saving_data_to_db(channel_id, channel_username, client, db, message)

        # all messages are in db
        if message.id == last_message_id_in_db:
            return

    except (FloodWaitError, ServerError, RPCError, BadRequestError) as e:
        logger.error("Error processing message %s: %s" % (message.id, type(e).__name__), exc_info=True)


async def saving_data_to_db(channel_id: int, channel_username: str, client: TelegramClient, db: Database,
                            message: Message) -> None:
    fwd_from_channel_username, tg_link = (
        await get_fwd_channel_username(client, message) if message.fwd_from else (None, None)
    )
    message_data = create_message_data(message, channel_id, channel_username, fwd_from_channel_username,
                                       tg_link)
    logger.info("Saving message %s from %s to the db." % (message_data.message_id, channel_username))
    await db.save_message_record(message_data)
    await check_and_save_photo(client, db, message, channel_id, channel_username)
    await check_and_save_reactions(db, message, channel_id, channel_username)


async def download_document(client: TelegramClient, db: Database, channel_id: int, channel_username: str) -> None:
    total_documents_in_channel = await client.get_messages(channel_username, 0, filter=InputMessagesFilterDocument)
    dir_name = f'{channel_username}_downloads'
    processed_messages = set()

    with tqdm(total=total_documents_in_channel.total, unit=' documents') as pbar_total:
        async for message in client.iter_messages(channel_username, filter=InputMessagesFilterDocument):
            if message.id in processed_messages:
                continue  # Skip already processed messages
            document = message.media.document
            mime_type = get_mime_type(message)
            file_size_in_mb = get_appropriated_part_size(document.size)
            file_name = get_document_name(message)

            if file_size_in_mb < THRESHOLD_SIZE_IN_MB:
                os.makedirs(dir_name, exist_ok=True)
                try:
                    file_path = os.path.join(dir_name, file_name)
                    if os.path.exists(file_path):
                        logger.warning("Channel [%s] message id [%s]File %s already exists at %s. Skipping download." % (channel_username, message.id, file_name, file_path))
                        continue

                    await client.download_media(message, file=file_path, progress_callback=callback_document)
                    pbar_total.update(1)
                    logger.info("Downloaded document %s to %s for message %s" % (file_name, file_path, message.id))
                    file_blob = read_binary_file(file_path)
                    if file_blob is not None:
                        await db.insert_document_blob(message.id, channel_id, channel_username, mime_type, file_name,
                                                      file_blob)
                        logger.info("Downloaded and saved document name [%s] to the db." % file_name)
                    else:
                        logger.warning("Document with the name [%s] was not found for message %s. Skipping." % (file_name,
                                                                                                              message))
                except (FloodWaitError, ServerError, RPCError, BadRequestError) as e:
                    logger.error("Error downloading document from message %s: %s", message.id, type(e).__name__,
                                 exc_info=True)

            else:
                logger.info("[Message %s] has file size %s MB bigger than %s MB. Process later." % (message.id,
                                                                                                  file_size_in_mb,
                                                                                                  THRESHOLD_SIZE_IN_MB))
                MESSAGES_WITH_BIG_FILES.setdefault(channel_username, []).append(message.id)


async def download_large_file(client: TelegramClient, message, message_size: int, local_file_path: str,
                              file_name: str) -> None:
    chunk_size = 256 * 1024
    offset = 0
    total_chunks = (message_size + chunk_size - 1) // chunk_size  # Calculate total chunks
    chunks_downloaded = 0

    logger.info("Saving message with id [%s] to %s" % (message.id, local_file_path))

    tqdm_params = {
        'desc': file_name,
        'total': total_chunks,
        'miniters': 1,
        'unit': 'B',
        'unit_scale': True,
        'unit_divisor': 1024,
    }
    with tqdm(**tqdm_params) as pbar:
        while offset < message_size:
            try:
                logger.info(
                    "[%s] Download started at %s" % (file_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                async for chunk in client.iter_download(message, offset=offset, chunk_size=chunk_size):
                    with open(local_file_path, 'ab') as file:
                        file.write(chunk)
                        offset += len(chunk)
                        chunks_downloaded += 1
                        pbar.update(1)
                        print(f"Downloaded {chunks_downloaded}/{total_chunks} chunks ({offset}/{message_size} bytes)")

            except (TimeoutError, ConnectionError) as e:
                logger.exception("Exception occurred while downloading large file. Sleeping.", type(e).__name__)
                await asyncio.sleep(0.3)
                continue

            # If offset is greater than or equal to the total file size, the download is complete.
            if offset >= message_size:
                end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.info("[%s] Successfully downloaded message %s size of %s to %s at %s" % (
                    message.id, message_size, file_name, local_file_path, end_time))
                break


async def download_large_media(client: TelegramClient, channel_name: str) -> None:
    if channel_name in MESSAGES_WITH_BIG_FILES:
        message_ids: list = MESSAGES_WITH_BIG_FILES[channel_name]
        dir_name_large = f'{channel_name}_downloads_big_files'
        os.makedirs(dir_name_large, exist_ok=True)
        async for message in client.iter_messages(channel_name, ids=message_ids):

            document = message.media.document
            message_size = document.size
            logger.info("Processing file with size %s, [message %s] from channel %s"% (message_size, message.id, channel_name))
            try:
                file_name = get_document_name(message)
                file_path = os.path.join(dir_name_large, file_name)
                if os.path.exists(file_path):
                    logger.info("File %s already exists at %s. Skipping large download." % (file_name,file_path))
                    continue
                logger.info("Start to download large file in chunks")
                await download_large_file(client, message, message_size, file_path, file_name)
            except (Exception, AttributeError) as e:
                logger.exception("Exception occurred calling download_large_file func", str(e), message)
    else:
        logger("Channel %s has no large files. Nothing to download" % channel_name)
