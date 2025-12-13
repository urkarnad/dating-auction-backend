import asyncio
import os
from dotenv import load_dotenv
import django
from aiohttp import web

from discord_bot.bot import bot
from discord_bot.server import create_app


load_dotenv()

print("Starting bot script...")
print(f"Discord token exists: {bool(os.getenv('DISCORD_BOT_TOKEN'))}")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DatingAuction.settings")
django.setup()

async def main():
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5005)
    await site.start()
    print('http server running on port 5005')

    print('starting discord bot...')
    await bot.start(os.getenv('DISCORD_BOT_TOKEN'))


if __name__ == '__main__':
    asyncio.run(main())
