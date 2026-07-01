import asyncio
from app.database import create_tables

async def main():
    print("Creating tables...")
    await create_tables()
    print("✅ Tables created successfully!")

asyncio.run(main())