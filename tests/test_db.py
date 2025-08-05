import pytest
from datetime import datetime
from src.db import DatabaseManager

class DummyChannel:
    def __init__(self):
        self.id = 123456789
        self.channel_url = "https://t.me/testchannel"
        self.username = "testchannel"
        self.title = "Test Channel"
        self.participants_count = 999
        self.date = datetime.utcnow()
        self.scam = False
        self.has_link = True
        self.fake = False

@pytest.mark.asyncio
async def test_db():
    db = DatabaseManager()
    async with db:
        await db.create_schema()

        await db.save_channel_record([DummyChannel()])
        exists = await db.is_channel_in_database("testchannel")
        assert exists is True
