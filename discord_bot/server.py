from aiohttp import web
from .bot import send_notification
import asyncio

async def handle_notify(request):
    data = await request.json()
    discord_id = data.get("discord_id")
    message = data.get("message")

    await send_notification(discord_id, message)
    return web.json_response({"status": "ok"})

def create_app():
    app = web.Application()
    app.add_routes([web.post('/notify', handle_notify)])
    return app
