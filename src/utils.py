import re
from typing import Optional

from telethon.tl.types import DocumentAttributeFilename, Message
from telethon.utils import get_extension

from src.logging_config import get_logger
import requests
from bs4 import BeautifulSoup
import asyncio
import functools
utils_logger = get_logger("utils")



def async_retry(retries=3, delay=2, backoff=2, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            wait = delay
            while attempt < retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    utils_logger.warning(f"[Retry] Exception: {e}. Retrying {attempt}/{retries} in {wait}s")
                    await asyncio.sleep(wait)
                    wait *= backoff
            utils_logger.error(f"[Retry] Failed after {retries} attempts")
            raise
        return wrapper
    return decorator

def get_subscribers_count(channel_url: str) -> int:
    try:
        response = requests.get(channel_url)
        if response.status_code != 200:
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', class_='tgme_page_extra')

        if not div:
            return 0

        text = div.text.strip().lower()

        match = re.match(r'^([\d\s,]+)\s+(members|subscriber|subscribers)\b', text, re.IGNORECASE)
        if match:
            num = match.group(1).replace(",", "").replace(" ", "")
            return int(num)
        return 0

    except Exception as e:
        utils_logger.error(f"[!] Error in get_subscribers_count: {type(e).__name__}: {e}")
        return 0


def read_binary_file(file_path: str) -> Optional[bytes]:
    try:
        with open(file_path, "rb") as file:
            return file.read()
    except FileNotFoundError as fnf_error:
        utils_logger.error("Error reading file %s" % type(fnf_error).__name__)
        return None



def get_mime_type(message: Message) -> str:
    document = message.media.document
    extension_type = get_extension(message.media)
    return extension_type if extension_type else document.mime_type.split("/")[1]

