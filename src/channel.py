import datetime
from collections import namedtuple
from typing import Union, List

from telethon import TelegramClient, hints

from src.logging_config import get_logger
from src.utils import get_subscribers_count

channel_logger = get_logger("channel")

ChannelData = namedtuple(
    "ChannelData",
    [
        "original_channel_id",
        "channel_url",
        "title",
        "username",
        "participants_count",
        "date",
        "scam",
        "verified",
        "has_link",
        "fake",
    ],
)


async def get_channel_entity(
        client: TelegramClient, channel: hints.EntitiesLike
) -> hints.Entity:
    """
    :param channel: link or name  or channel id of telegram channel
    :type client: object

    :return Channel(id=1817024988, title='Anonymous', photo=ChatPhoto(photo_id=5895695577541360306, dc_id=4, has_video=False,
    stripped_thumb=b'\x01\x08\x08_\xb1O\xe7}\xa7\x7f\xef<\xccm\xf6\xff\x00\xf5QE\x14\x01'),
                    date=datetime.datetime(2022, 10, 3, 1, 7, 56, tzinfo=datetime.timezone.utc), creator=False, left=True,
                    broadcast=True, verified=True, megagroup=False, restricted=False, signatures=False, min=False, scam=False,
                    has_link=True, has_geo=False, slowmode_enabled=False, call_active=False, call_not_empty=False, fake=False,
                    gigagroup=False, noforwards=False, join_to_send=False, join_request=False, forum=False,
                    access_hash=-6047356602663149385, username='ANONM0S', restriction_reason=[], admin_rights=None,
                    banned_rights=None, default_banned_rights=None, participants_count=None, usernames=[]
                    )
    """
    try:
        return await client.get_entity(channel)
    except (TypeError, ValueError) as e:
        channel_logger.error(
            "Error occurred when trying to get entity information %s" % type(e).__name__
        )


async def get_channel_username(
        client: TelegramClient, channel_id: int
) -> Union[str, None]:
    try:
        entity = await get_channel_entity(client, channel_id)
        return entity.username
    except (TypeError, ValueError) as e:
        channel_logger.error(
            "Error occurred when trying to retrieve username by channel id %s %s"
            % (channel_id, type(e).__name__)
        )
        return None


def get_channel_info_rows(channel_url: str, creation_date: datetime.datetime, entity) -> List[ChannelData]:
    return [ChannelData(
        original_channel_id=entity.id,
        channel_url=channel_url,
        username=entity.username,
        title=entity.title,
        participants_count=get_subscribers_count(channel_url),
        date=creation_date,
        scam=getattr(entity, "scam", False),
        verified=getattr(entity, "verified", False),
        has_link=bool(entity.username),
        fake=getattr(entity, "fake", False)
    )]
