import datetime

from telethon.tl.types import Message, PeerChannel, MessageFwdHeader, MessageMediaDocument, Document, \
    DocumentAttributeFilename, MessageEntityTextUrl

from src.message import get_telegram_link, create_message_data, get_url


def test_get_telegram_link():
    fwd_channel_username = "CoolChannelName"
    assert get_telegram_link(fwd_channel_username) == 'https://t.me/CoolChannelName'


def test_create_message_data():
    sample_message = Message(id=456, peer_id=PeerChannel(channel_id=123),
                             date=datetime.datetime(1999, 5, 1, 22, 26, 29, tzinfo=datetime.timezone.utc),
                             message='Super important message!',
                             pinned=False, noforwards=False, from_id=None,
                             fwd_from=MessageFwdHeader(
                                 date=datetime.datetime(1999, 5, 1, 22, 22, 16, tzinfo=datetime.timezone.utc),
                                 from_id=PeerChannel(channel_id=999), from_name=None,
                                 channel_post=361),
                             media=MessageMediaDocument(
                                 document=Document(
                                     id=555,
                                     access_hash=-555,
                                     file_reference=b'some binary repr',
                                     date=datetime.datetime(1999, 5, 1, 22, 22, 16, tzinfo=datetime.timezone.utc),
                                     mime_type='application/pdf', size=47617434, dc_id=2,
                                     attributes=[DocumentAttributeFilename(file_name='CoolPdfDoc.pdf')])),
                             views=4689, forwards=55,
                             entities=[MessageEntityTextUrl(offset=0, length=13, url='https://t.me/OtherCoolChannel'),
                                       MessageEntityTextUrl(offset=0, length=15, url='https://t.me/AtherCoolChannel')
                                       ],
                             edit_date=datetime.datetime(1999, 5, 1, 22, 28, 54, tzinfo=datetime.timezone.utc),
                             restriction_reason=[], ttl_period=None)

    sample_channel_id = 123
    sample_channel_username = "MyCoolChannel"
    sample_fwd_from_channel_username = "forwarded_channel"
    sample_tg_link = "https://t.me/forwarded_channel"

    result = create_message_data(
        message=sample_message,
        channel_id=sample_channel_id,
        channel_username=sample_channel_username,
        fwd_from_channel_username=sample_fwd_from_channel_username,
        tg_link=sample_tg_link
    )

    entity_urls = get_url(sample_message.entities)
    assert entity_urls == "['https://t.me/OtherCoolChannel', 'https://t.me/AtherCoolChannel']"
    assert result.message_id == 456
    assert result.channel_id == 123
    assert result.channel_name == "MyCoolChannel"
    assert result.message_date == datetime.datetime(1999, 5, 1, 22, 26, 29, tzinfo=datetime.timezone.utc)
    assert result.message_text == "Super important message!"
    assert result.message_pinned == False
    assert result.message_fwd_from == True
    assert result.message_fwd_from_date == datetime.datetime(1999, 5, 1, 22, 22, 16, tzinfo=datetime.timezone.utc)
    assert result.message_fwd_from_channel_id == 999
    assert result.message_fwd_from_channel_username == "forwarded_channel"
    assert result.message_edit_date == datetime.datetime(1999, 5, 1, 22, 28, 54, tzinfo=datetime.timezone.utc)
    assert result.message_views == 4689
    assert result.message_forwards == 55
    assert result.message_media == True
    assert result.url_in_message == "['https://t.me/OtherCoolChannel', 'https://t.me/AtherCoolChannel']"
    assert result.message_fwd_from_channel_link == sample_tg_link

