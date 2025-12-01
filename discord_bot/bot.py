import discord
from discord.ext import commands
import os
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


@bot.command(name='link')
async def link_account(ctx, user_id: str):
    # usage: !link <your_user_id>
    discord_id = str(ctx.author.id)

    # call Django API to save discord_id

    embed = discord.Embed(
        title="Акаунт прив'язано",
        description=f"Ваш Discord акаунт успішно прив'язано!\nВаш Discord ID: {discord_id}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command(name='unlink')
async def unlink_account(ctx):
    # !unlink
    discord_id = str(ctx.author.id)

    embed = discord.Embed(
        title="Акаунт відв'язано",
        description="Ваш Discord акаунт успішно відв'язано від профілю",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)


@bot.command(name='myid')
async def get_my_id(ctx):
    discord_id = str(ctx.author.id)

    embed = discord.Embed(
        title="Ваш Discord ID",
        description=f"**{discord_id}**\n\nВикористайте цей ID для прив'язки акаунту",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


async def send_notification(discord_id: str, message: str):
    try:
        user = await bot.fetch_user(int(discord_id))

        embed = discord.Embed(
            title="Вашу ставку перебили!",
            description=message,
            color=discord.Color.orange()
        )
        embed.set_footer(text="Зробіть нову ставку, щоб піти на побачення!")

        await user.send(embed=embed)
        return True
    except discord.NotFound:
        print(f"Користувача з ID {discord_id} не знайдено")
        return False
    except discord.Forbidden:
        print(f"Не можу надіслати повідомлення користувачу {discord_id}")
        return False
    except Exception as e:
        print(f"Помилка при відправці повідомлення: {e}")
        return False


if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    bot.run(TOKEN)