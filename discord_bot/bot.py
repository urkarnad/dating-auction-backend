import os
import discord
from discord.ext import commands
from flask import Flask, request
import threading

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@app.route("/notify", methods=["POST"])
def notify():
    data = request.json
    user_id = data.get("user_id")
    lot_name = data.get("lot_name")
    new_bid = data.get("new_bid")

    async def send_dm():
        user = await bot.fetch_user(user_id)
        await user.send(f"Твою ставку на лот '{lot_name}' перебили! Нова ставка: {new_bid} ")

    bot.loop.create_task(send_dm())
    return {"status": "ok"}


def run_flask():
    app.run(host="0.0.0.0", port=5001)


threading.Thread(target=run_flask).start()

bot.run(TOKEN)
