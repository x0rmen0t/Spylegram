import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, Union

from telethon import TelegramClient
from telethon.errors import ChannelPrivateError
from telethon.tl.types import (Message, MessageEntityTextUrl,
                               MessageEntityUnknown, MessageEntityUrl,
                               MessageService, PeerChannel)

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

TypeMessageEntity = Union[MessageEntityUnknown, MessageEntityUrl]


@dataclass
class MessageData:
    message_id: int
    channel_id: int
    channel_name: str
    message_date: Optional[datetime] = None
    message_pinned: bool = False
    message_views: int = 0
    message_forwards: int = 0
    message_media: bool = False
    message_text: Optional[str] = None
    message_edit_date: Optional[datetime] = None
    url_in_message: Optional[str] = None
    message_fwd_from: bool = False
    message_fwd_from_date: Optional[datetime] = None
    message_fwd_from_channel_id: Optional[int] = None
    message_fwd_from_channel_username: Optional[str] = None
    message_fwd_from_channel_link: Optional[str] = None


async def get_first_message_date(
    client: TelegramClient, channel_url: str
) -> Union[datetime, str]:
    """We count channel creation date by the 1st service message posted in the channel;
    If None then we take creation date from channel entity
    """
    async for message in client.iter_messages(channel_url, reverse=True, limit=1):
        if isinstance(message, MessageService):
            return message.date
        else:
            return ""


async def get_last_message_id(client: TelegramClient, channel: str) -> int:
    async for message in client.iter_messages(channel, limit=1):
        return message.id


def get_url(message_entity: Optional[List["TypeMessageEntity"]]) -> str:
    list_of_entities = []
    for entity in message_entity:
        if isinstance(entity, MessageEntityTextUrl):
            list_of_entities.append( entity.url)
    return str(list_of_entities)


def get_telegram_link(fwd_channel_username: str) -> str:
    return f"https://t.me/{fwd_channel_username}"


async def get_fwd_channel_username(client: TelegramClient, message: Message) -> Tuple[str, str] | Tuple[None, None]:  # type: ignore
    if isinstance(message.fwd_from.from_id, PeerChannel):
        try:
            entity = await client.get_entity(message.fwd_from.from_id.channel_id)
            tg_link = get_telegram_link(entity.username)
            return entity.username, tg_link
        except ChannelPrivateError as e:
            logging.warning(
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
    fwd_from_channel_username: str,
    tg_link: str,
) -> MessageData:
    """
    Create a MessageData object from a Telegram message.

    Args:
        message (Message obj): The Telegram message to create data from.
        channel_id (int): The ID of the Telegram channel.
        channel_username (str): The username of the Telegram channel.
        fwd_from_channel_username (str): The username of the forwarded channel (if any).
        tg_link (str): The link to the forwarded channel (if any).

    Returns:
        MessageData: A MessageData object representing the message.
    """
    return MessageData(
        message_id=message.id,
        channel_id=channel_id,
        channel_name=channel_username,
        message_date=message.date,
        message_text=str(message.message),
        message_pinned=message.pinned,
        message_fwd_from=bool(message.fwd_from),
        message_fwd_from_date=message.fwd_from.date if message.fwd_from else None,
        message_fwd_from_channel_id=message.fwd_from.from_id.channel_id
        if message.fwd_from and message.fwd_from.from_id else None,
        message_fwd_from_channel_username=fwd_from_channel_username,
        message_edit_date=message.edit_date if message.edit_date else None,
        message_views=message.views,
        message_forwards=message.forwards,
        message_media=bool(message.media),
        url_in_message=get_url(message.entities) if message.entities else None,
        message_fwd_from_channel_link=tg_link if message.fwd_from else None,
    )
