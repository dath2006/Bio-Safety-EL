#!/usr/bin/env python3
"""CLI script to ingest regulatory documents into the knowledge base."""

import asyncio
import sys
from pathlib import Path

# Add agent root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import async_session_factory, init_db
from rag.ingest import run_full_ingestion


async def main() -> None:
    print("Initializing database...")
    await init_db()

    print("Running ingestion pipeline...")
    async with async_session_factory() as session:
        result = await run_full_ingestion(session, clear_existing=True)

    print("\nIngestion complete:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
