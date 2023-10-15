from datetime import datetime

import pytest
from telethon.sync import TelegramClient
from telethon.tl.types import ChatPhoto, Channel

from src.channel import (
    get_channel_entity,
    get_channel_info_rows,
    ChannelData,
    get_channel_username,
)
from unittest.mock import AsyncMock


class MockedClient(TelegramClient):
    # noinspection PyMissingConstructor
    def __init__(self):
        pass


@pytest.mark.asyncio
async def test_get_channel_username(mocker):
    client = MockedClient()
    mocker.patch.object(client, "get_entity", new_callable=AsyncMock)

    mock_entity = Channel(
        id=123,
        title="TestChannel",
        photo=ChatPhoto(
            photo_id=123,
            dc_id=4,
            has_video=False,
            stripped_thumb=b"\x01\x01\x01_\xb01\x01}\xaa\xaa\xaa<\xaa\xaa\xff\x00\xff\x11\x01",
        ),
        date=datetime(1999, 10, 3, 1, 7, 56),
        creator=False,
        left=True,
        broadcast=True,
        verified=True,
        megagroup=False,
        restricted=False,
        signatures=False,
        min=False,
        scam=False,
        has_link=True,
        has_geo=False,
        slowmode_enabled=False,
        call_active=False,
        call_not_empty=False,
        fake=False,
        gigagroup=False,
        noforwards=False,
        join_to_send=False,
        join_request=False,
        forum=False,
        access_hash=-123,
        username="testchannel",
        restriction_reason=[],
        admin_rights=None,
        banned_rights=None,
        default_banned_rights=None,
        participants_count=None,
        usernames=[],
    )

    client.get_entity.return_value = mock_entity
    channel_id = 123
    entity = await get_channel_entity(client, channel_id)
    username = await get_channel_username(client, channel_id)
    assert entity.id == mock_entity.id
    assert entity.title == mock_entity.title
    assert entity.username == mock_entity.username
    assert username == mock_entity.username


@pytest.mark.asyncio
async def test_get_channel_info_rows():
    # Replace with your test data
    channel_url = "https://t.me/super_channel"
    creation_date = datetime(1999, 10, 3, 1, 7, 56)
    test_channel_entity = Channel(
        id=123,
        title="TestChannel",
        photo=ChatPhoto(
            photo_id=123,
            dc_id=4,
            has_video=False,
            stripped_thumb=b"\x01\x01\x01_\xb01\x01}\xaa\xaa\xaa<\xaa\xaa\xff\x00\xff\x11\x01",
        ),
        date=datetime(1999, 10, 3, 1, 7, 56),
        creator=False,
        left=True,
        broadcast=True,
        verified=True,
        megagroup=False,
        restricted=False,
        signatures=False,
        min=False,
        scam=False,
        has_link=True,
        has_geo=False,
        slowmode_enabled=False,
        call_active=False,
        call_not_empty=False,
        fake=False,
        gigagroup=False,
        noforwards=False,
        join_to_send=False,
        join_request=False,
        forum=False,
        access_hash=-123,
        username="testchannel",
        restriction_reason=[],
        admin_rights=None,
        banned_rights=None,
        default_banned_rights=None,
        participants_count=100,
        usernames=[],
    )

    rows = get_channel_info_rows(channel_url, creation_date, test_channel_entity)

    expected_rows = [
        ChannelData(
            id=123,
            channel_url=channel_url,
            title="TestChannel",
            username="testchannel",
            participants_count=100,
            date=creation_date,
            scam=False,
            has_link=True,
            fake=False,
        )
    ]
    assert len(rows) == 1
    assert rows == expected_rows
    channel_data = rows[0]
    assert channel_data.id == test_channel_entity.id
    assert channel_data.channel_url == channel_url
    assert channel_data.title == test_channel_entity.title
    assert channel_data.username == test_channel_entity.username
    assert channel_data.participants_count == (
        test_channel_entity.participants_count or 0
    )
    assert channel_data.date == creation_date
    assert channel_data.scam == test_channel_entity.scam
    assert channel_data.has_link == test_channel_entity.has_link
    assert channel_data.fake == test_channel_entity.fake
