"""Entry point for: python -m app.mcp"""
import asyncio
from .server import main

asyncio.run(main())
