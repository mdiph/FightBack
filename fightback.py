import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from db.database import setup_database

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set bot intents
intents = discord.Intents.all()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!fb ', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ FightBack Bot is online as {bot.user}')
    setup_database()

# Load cogs asynchronously with console logs
initial_extensions = [
    'cogs.register',
    'cogs.system',
    'cogs.manual',
    'cogs.match',
    'cogs.stats',
    'cogs.leaderboard',
    'cogs.history',
    'cogs.myhistory',
    'cogs.steamlink',
    'cogs.reset',
    'cogs.leave'
]

async def main():
    async with bot:
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
                print(f'✅ Loaded cog: {extension}')
            except Exception as e:
                print(f'❌ Failed to load cog: {extension} - Error: {e}')
        
        print("🚀 All cogs loaded successfully. Bot is starting...")
        await bot.start(TOKEN)

asyncio.run(main())