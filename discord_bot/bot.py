import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user} is running uraaa!')
    print(f'bot ID: {bot.user.id}')

@bot.command(name='myid')
async def get_discord_id(ctx):
    discord_id = str(ctx.author.id)

    embed = discord.Embed(
        title='твій Discord ID',
        description=(
            f'**{discord_id}**\n\n'
            f'скопіюй цю айдішку і впиши її в налаштуваннях профілю на стайті аукціону, щоб отримувати нотифікації!'
        ),
        colour=discord.Colour.blue()
    )
    embed.set_footer(text='dating auction bot')

    await ctx.send(embed=embed)

async def send_notification(discord_id: str, message: str, lot_id: int = None):
    try:
        user = await bot.fetch_user(int(discord_id))

        embed = discord.Embed(
            title='bid notification',
            description=message,
            colour=discord.Colour.orange()
        )

        if lot_id:
            site_url = os.getenv('SITE_URL', 'http://localhost:3000')
            embed.add_field(
                name='view lot',
                value=f'[click here]({site_url}/lot/{lot_id})',
                inline=False
            )

            embed.set_footer(text='dating auction bot')

            await user.send(embed=embed)
            return True

    except discord.NotFound:
        print(f'Discord ID {discord_id} not found')
        return False
    except discord.Forbidden:
        print(f'Cannot send DM to {discord_id}')
        return False
    except Exception as e:
        print(e)
        return False


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
