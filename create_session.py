import sys

from telethon.sync import TelegramClient
import asyncio
import os
from dotenv import load_dotenv

from src.logging_config import logger

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
SESSION_NAME = "snooper"


async def main() -> None:
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

    client = await init_telegram_client(os.getenv("SESSION_NAME"), os.getenv("PHONE"), int(os.getenv("API_ID")),
                                        os.getenv("API_HASH"))


if __name__ == "__main__":
    asyncio.run(main())
