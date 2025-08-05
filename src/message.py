from typing import List, Tuple, Union, Any
import json

from telethon import TelegramClient
from telethon.errors import ChannelPrivateError
from telethon.tl.types import (Message, MessageEntityTextUrl,
                               MessageEntityUnknown, MessageEntityUrl,
                               MessageService, PeerChannel, MessageMediaPhoto)

from src.logging_config import get_logger

message_module = get_logger("message")

TypeMessageEntity = Union[MessageEntityUnknown, MessageEntityUrl]

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from langdetect import detect, LangDetectException

def detect_lang(text: str) -> Optional[str]:
    try:
        return detect(text)
    except LangDetectException:
        return None


class MessageData(BaseModel):
    original_message_id: int
    original_channel_id: int
    channel_username: Optional[str]
    date: Optional[datetime] = None
    message: Optional[str] = None
    message_eng: Optional[str] = None
    lang_code: Optional[str] = None
    ts_config: Optional[str] = "simple"

    pinned: Optional[bool] = False
    views: Optional[int] = 0
    forwards: Optional[int] = 0
    edit_date: Optional[datetime] = None
    url_in_message: Optional[str] = None

    fwd_from: Optional[str] = None
    fwd_from_date: Optional[datetime] = None
    fwd_from_channel_id: Optional[int] = None
    fwd_from_channel_username: Optional[str] = None
    fwd_from_channel_link: Optional[str] = None
    fwd_from_id: Optional[str] = None

    media: Optional[str] = None



async def get_first_message_date(
        client: TelegramClient, channel_url: str
) -> Union[None, str, datetime]:
    """We count channel creation date by the 1st service message posted in the channel;
       If None then we take creation date from channel entity
    """
    async for message in client.iter_messages(channel_url, reverse=True, limit=1):
        if isinstance(message, MessageService):
            return message.date
        else:
            return ""


async def get_last_message_id(client: TelegramClient, channel: str) -> Optional[Any]:
    async for message in client.iter_messages(channel, limit=1):
        return message.id


def get_url(message_entity: Optional[List["TypeMessageEntity"]]) -> str:
    list_of_entities = []
    for entity in message_entity:
        if isinstance(entity, MessageEntityTextUrl):
            list_of_entities.append(entity.url)
    return str(list_of_entities)


def get_telegram_link(fwd_channel_username: str) -> str:
    return f"https://t.me/{fwd_channel_username}"


async def get_fwd_channel_username(client: TelegramClient, message: Message) -> Union[
    Tuple[str, str], Tuple[None, None]]:  # type: ignore
    if isinstance(message.fwd_from.from_id, PeerChannel):
        try:
            entity = await client.get_entity(message.fwd_from.from_id.channel_id)
            tg_link = get_telegram_link(entity.username)
            return entity.username, tg_link
        except ChannelPrivateError as e:
            message_module.warning(
                "Cant get information about the channel due to access restrictions. Channel might be marked as private",
                e,
            )
            return None, None
    else:
        return message.fwd_from.from_name, message.fwd_from.from_id

def create_message_data(
    message: Message,
    channel_id: int,
    channel_username: str,
    fwd_from_channel_username: Optional[str],
    tg_link: Optional[str],
) -> MessageData:
    """
    Create a MessageData object from a Telegram message.

    Args:
        message (Message): The Telegram message.
        channel_id (int): The Telegram channel ID.
        channel_username (str): The Telegram channel username.
        fwd_from_channel_username (str): Forwarded channel username.
        tg_link (str): Forwarded channel t.me link.

    Returns:
        MessageData: The extracted structured data.
    """

    raw_text = str(message.message or "")
    lang_code = detect_lang(raw_text)

    # Optional: Map language code to ts_config (you can customize this later)
    lang_to_tsconfig = {
        "en": "english",
        "ru": "russian",
        "uk": "russian",
        "de": "german",
        "fr": "french",
        "es": "spanish",
    }
    ts_config = lang_to_tsconfig.get(lang_code, "simple")

    return MessageData(
        original_message_id=message.id,
        original_channel_id=channel_id,
        channel_username=channel_username,
        date=message.date,
        message=raw_text,
        message_eng=None,
        lang_code=lang_code,
        ts_config=ts_config,
        pinned=message.pinned or False,
        views=message.views or 0,
        forwards=message.forwards or 0,
        edit_date=message.edit_date,
        url_in_message=get_url(message.entities) if message.entities else None,
        fwd_from=str(message.fwd_from) if message.fwd_from else None,
        fwd_from_date=getattr(message.fwd_from, 'date', None) if message.fwd_from else None,
        fwd_from_channel_id=getattr(
            getattr(message.fwd_from, 'from_id', None), 'channel_id', None
        ) if message.fwd_from else None,
        fwd_from_channel_username=fwd_from_channel_username,
        fwd_from_channel_link=tg_link,
        fwd_from_id=str(message.fwd_from.from_id)
        if message.fwd_from and message.fwd_from.from_id else None,
        media=json.dumps({"type": "photo"}) if isinstance(message.media, MessageMediaPhoto) else None

    )

