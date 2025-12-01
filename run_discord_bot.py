import os
import django
import asyncio
from aiohttp import web

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DatingAuction.settings')
django.setup()

from discord_bot.bot import bot
from discord_bot.server import create_app


async def main():
    # start aiohttp server
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5005)
    await site.start()
    print("HTTP server running on port 5005")

    # start discord bot
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == '__main__':
    asyncio.run(main())
