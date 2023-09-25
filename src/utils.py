from telethon.tl.types import DocumentAttributeFilename, Message
from telethon.utils import get_extension
from src.logging_config import logger


def read_binary_file(file_path: str) -> bytes | None:
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except FileNotFoundError as fnf_error:
        logger.error("Error reading file %s" % type(fnf_error).__name__)
        return None


def callback_photo(current: int, total: int) -> None:
    #logger.info('Downloaded', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))
    percentage = (current / total) * 100
    logger.info('Downloaded %d out of %d bytes: %.2f%%', current, total, percentage)

def callback_document(current: int, total: int) -> None:
    #logger.info('Downloaded', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))
    percentage = (current / total) * 100
    logger.info('Downloaded %d out of %d bytes: %.2f%%', current, total, percentage)


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
