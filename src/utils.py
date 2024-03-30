from typing import Optional

from telethon.tl.types import DocumentAttributeFilename, Message
from telethon.utils import get_extension

from src.logging_config import get_logger
import requests
from bs4 import BeautifulSoup

utils_logger = get_logger("utils")


def clean_subscribers_count(subscribers_str: str) -> int:
    subscribers = subscribers_str.replace('subscribers', "").replace(" ", "")
    return int(subscribers)


def clean_group_members_count(members_str: str) -> int:
    members_count = members_str.split(",")[0]
    cleaned_members_count = members_count.replace("members", "").replace(" ", "")
    return int(cleaned_members_count)


def get_subscribers_count(channel_url: str) -> str:
    response = requests.get(channel_url)
    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            div_element = soup.find('div', class_='tgme_page_extra')

            if div_element:
                subscriber_info = div_element.text.strip()
                return subscriber_info
        except Exception as e:
            utils_logger.error(
                "Exception %s occurred during retrieving channel's memeber count from html" % type(e).__name__)


def read_binary_file(file_path: str) -> Optional[bytes]:
    try:
        with open(file_path, "rb") as file:
            return file.read()
    except FileNotFoundError as fnf_error:
        utils_logger.error("Error reading file %s" % type(fnf_error).__name__)
        return None


def callback_photo(current: int, total: int) -> None:
    # logger.info('Downloaded', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))
    percentage = (current / total) * 100
    utils_logger.info("Photo downloaded %d out of %d bytes: %.2f%%", current, total, percentage)


def callback_document(current: int, total: int) -> None:
    # logger.info('Downloaded', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))
    percentage = (current / total) * 100
    utils_logger.info("Document downloaded %d out of %d bytes: %.2f%%", current, total, percentage)


def get_mime_type(message: Message) -> str:
    document = message.media.document
    extension_type = get_extension(message.media)
    return extension_type if extension_type else document.mime_type.split("/")[1]


def get_document_name(message: Message) -> str:
    document = message.media.document
    document_attributes_list = document.attributes
    if len(document_attributes_list) > 1:
        for attr in document_attributes_list:
            if isinstance(attr, DocumentAttributeFilename):
                return attr.file_name

    if isinstance(document.attributes[0], DocumentAttributeFilename):
        return document.attributes[0].file_name

    return f"{message.id}"
