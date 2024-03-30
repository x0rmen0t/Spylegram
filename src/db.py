from contextlib import asynccontextmanager
from typing import List, Tuple

import aiosqlite
from pkg_resources import resource_filename

from src.message import MessageData


class Database:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self._connection = None

    @asynccontextmanager
    async def db_cursor(self):
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_name, timeout=5, isolation_level='EXCLUSIVE')
        async with self._connection.cursor() as cursor:
            try:
                yield cursor
                await self._connection.commit()
            except Exception:
                await self._connection.rollback()
                raise

    async def create_schema(self) -> None:
        with open(resource_filename(__name__, "db_schema.sql")) as schema_file:
            schema_sql = schema_file.read()
            async with self.db_cursor() as cursor:
                await cursor.executescript(schema_sql)

    async def is_channel_in_database(self, channel_name: str) -> bool:
        async with self.db_cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM channels WHERE channel_name = ?", (channel_name,)
            )
            count = await cursor.fetchone()
            return count[0] > 0

    async def save_channel_record(self, records: List[tuple]) -> None:
        async with self.db_cursor() as cursor:
            for record in records:
                await cursor.execute(
                    "INSERT OR IGNORE INTO channels (channel_id, channel_url, channel_name, channel_title, user_count, date, scam, has_link, fake) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        record.id,
                        record.channel_url,
                        record.username,
                        record.title,
                        record.participants_count,
                        record.date,
                        record.scam,
                        record.has_link,
                        record.fake,
                    ),
                )

    async def insert_document_blob(
            self,
            message_id: int,
            channel_id: int,
            channel_username: str,
            file_name,
            mime_type,
            file_blob: bytes,
    ) -> None:
        async with self.db_cursor() as cursor:
            await cursor.execute(
                "SELECT 1 FROM documents WHERE message_id = ?", (message_id,)
            )
            if await cursor.fetchone() is None:
                await cursor.execute(
                    "INSERT INTO documents (message_id, channel_id,  channel_name,file_name,mime_type, file_blob) VALUES (?, ?, ?, ?,?,?)",
                    (
                        message_id,
                        channel_id,
                        channel_username,
                        file_name,
                        mime_type,
                        file_blob,
                    ),
                )

    async def get_last_message_record(self, channel: str) -> Tuple[int, str]:
        async with self.db_cursor() as cursor:
            result = await cursor.execute(
                "SELECT message_id, channel_name FROM messages WHERE channel_name = ? ORDER BY message_id DESC LIMIT 1;",
                (channel,),
            )
            row = await result.fetchone()
            if row:
                return row
            else:
                return 0, ""

    async def update_last_processed_message_id(
            self, channel_name: str, message_id: int
    ) -> None:
        async with self.db_cursor() as cursor:
            await cursor.execute(
                "UPDATE messages SET last_processed_message_id = ? WHERE channel_name = ?",
                (message_id, channel_name),
            )

    async def save_message_record(self, message_data: MessageData) -> None:
        async with self.db_cursor() as cursor:
            insert_sql = """
                INSERT OR IGNORE INTO messages (
                    message_id, channel_id, channel_name, message_date, message_text, message_pinned,
                    message_fwd_from, message_fwd_from_date, message_fwd_from_channel_id,
                    message_fwd_from_channel_username, message_edit_date, message_views, message_forwards,
                    message_media, url_in_message, message_fwd_from_channel_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            await cursor.execute(
                insert_sql,
                (
                    message_data.message_id,
                    message_data.channel_id,
                    message_data.channel_name,
                    message_data.message_date,
                    message_data.message_text,
                    message_data.message_pinned,
                    message_data.message_fwd_from,
                    message_data.message_fwd_from_date,
                    message_data.message_fwd_from_channel_id,
                    message_data.message_fwd_from_channel_username,
                    message_data.message_edit_date,
                    message_data.message_views,
                    message_data.message_forwards,
                    message_data.message_media,
                    message_data.url_in_message,
                    message_data.message_fwd_from_channel_link,
                ),
            )

    async def is_image_in_db(self, message_id: int, photo_id: int) -> bool:
        async with self.db_cursor() as cursor:
            result = await cursor.execute(
                "SELECT id FROM images WHERE message_id = ? AND photo_id = ?",
                (message_id, photo_id),
            )
            return (await result.fetchone()) is not None

    async def save_image_blob(
            self,
            channel_id: int,
            channel_username: str,
            message_id: int,
            photo_id: int,
            image_data: bytes,
    ):
        async with self.db_cursor() as cursor:
            await cursor.execute(
                "INSERT OR IGNORE INTO images (channel_id, channel_name, message_id,photo_id, image_data) VALUES (?, ?, ?, ?, ?)",
                (channel_id, channel_username, message_id, photo_id, image_data),
            )

    async def save_reactions(
            self,
            message_id: int,
            channel_id: int,
            channel_username: str,
            emoticon,
            count: int,
    ):
        async with self.db_cursor() as cursor:
            # Check if the reaction already exists in the database
            existing_reaction = await cursor.execute(
                "SELECT id FROM reactions WHERE message_id = ? AND channel_id = ? AND emoticon = ?",
                (message_id, channel_id, emoticon),
            )

            reactions_ = await existing_reaction.fetchone()

            if reactions_ is None:
                await cursor.execute(
                    "INSERT INTO reactions (message_id, channel_id, channel_name, emoticon, emoticon_count) VALUES ("
                    "?, ?, ?, ?, ?)",
                    (message_id, channel_id, channel_username, emoticon, count),
                )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._connection is not None:
            await self._connection.close()
