import pytest

from src.utils import read_binary_file, get_mime_type, get_document_name
import datetime

from telethon.tl.types import (
    DocumentAttributeFilename,
    Message,
    PeerChannel,
    MessageMediaDocument,
    Document,
)


def test_read_existing_file():
    file_path = "xor-icon.png"

    result = read_binary_file(file_path)
    assert result is not None
    assert isinstance(result, bytes)


def test_read_non_existing_file():
    file_path = "non_existent_file.png"
    result = read_binary_file(file_path)
    assert result is None


mime_type_test_cases = [
    ("image/png", ".png"),
    ("image/jpeg", ".jpg"),
    ("image/gif", ".gif"),
    ("image/svg+xml", ".svg"),
    ("application/pdf", ".pdf"),
    ("application/vnd.ms-excel", ".xls"),
    ("application/zip", ".zip"),
    ("application/sql", "sql"),
    ("text/plain", ".txt"),
    ("text/csv", ".csv"),
    ("text/html", ".html"),
    ("video/mp4", ".mp4"),
]


@pytest.mark.parametrize("mime_type, expected", mime_type_test_cases)
def test_get_mime_type(mime_type, expected):
    message = Message(
        id=666,
        peer_id=PeerChannel(channel_id=666666),
        date=datetime.datetime(1999, 5, 1, 22, 26, 29, tzinfo=datetime.timezone.utc),
        message="Some very important message",
        media=MessageMediaDocument(
            nopremium=False,
            spoiler=False,
            document=Document(
                id=123,
                access_hash=-123,
                file_reference=b'\x02h\xea\x8dI\x00\x00\x03ze\x06\xc2k\x84\x9e\x891"\xfa r\x87\xbbM\xb4\xe7}\xe6\x99',
                date=datetime.datetime(
                    1999, 5, 1, 22, 22, 16, tzinfo=datetime.timezone.utc
                ),
                mime_type=mime_type,
                size=47617434,
                dc_id=2,
                attributes=[DocumentAttributeFilename(file_name="whatever.png")],
            ),
        ),
    )

    result = get_mime_type(message)
    assert result == expected


document_name_test_cases = [
    ("clever_name", "clever_name"),
    ("", ""),
    (".", "."),
]


@pytest.mark.parametrize("doc_name, expected", document_name_test_cases)
def test_get_document_name(doc_name, expected):
    message = Message(
        id=666,
        peer_id=PeerChannel(channel_id=666666),
        date=datetime.datetime(1999, 5, 1, 22, 26, 29, tzinfo=datetime.timezone.utc),
        message="Some very important message",
        media=MessageMediaDocument(
            nopremium=False,
            spoiler=False,
            document=Document(
                id=123,
                access_hash=-123,
                file_reference=b'\x02h\xea\x8dI\x00\x00\x03ze\x06\xc2k\x84\x9e\x891"\xfa r\x87\xbbM\xb4\xe7}\xe6\x99',
                date=datetime.datetime(
                    1999, 5, 1, 22, 22, 16, tzinfo=datetime.timezone.utc
                ),
                mime_type="whatever_mime_type",
                size=47617434,
                dc_id=2,
                attributes=[DocumentAttributeFilename(file_name=doc_name)],
            ),
        ),
    )

    result = get_document_name(message)
    assert result == expected
