from aiohttp import web

from discord_bot.bot import send_notification


async def handle_notify(request):
    try:
        data = await request.json()
        discord_id = data.get('discord_id')
        message = data.get('message')
        lot_id = data.get('lot_id')

        if not discord_id or not message:
            return web.json_response({
                'status': 'error', 'message': 'missing required fields'},
            status=400)

        success = await send_notification(discord_id, message, lot_id)

        return web.json_response({'status': 'ok' if success else 'failed', "discord_id": discord_id})

    except Exception as e:
        return web.json_response({
            'status': 'error',
            'message': str(e),
        },   status=500)

def create_app():
    app = web.Application()
    app.add_routes([web.post('/notify', handle_notify)])
    return app
