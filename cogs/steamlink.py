import re
import discord
import aiohttp
from discord.ext import commands
from discord.ui import View, Button

class SteamLinkButton(View):
    """Creates an interactive Steam lobby invitation button."""
    def __init__(self, lobby_url):
        super().__init__(timeout=None)
        self.lobby_url = lobby_url
        join_button = Button(label="🔗 Gaming Time!", style=discord.ButtonStyle.link, url=self.lobby_url)
        self.add_item(join_button)

class SteamLinkParser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def shorten_url(self, long_url):
        """Shortens the Steam lobby URL using TinyURL."""
        api_url = "https://tinyurl.com/api-create.php"
        params = {"url": long_url}

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as resp:
                return await resp.text() if resp.status == 200 else long_url  # Fallback if API fails

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detects Steam lobby links and responds with an embedded message and interactive button."""
        if message.author.bot:
            return

        match = re.search(r"steam://joinlobby/(\d+)/(\d+)/(\d+)", message.content)
        if match:
            game_id, lobby_id, user_id = match.groups()
            short_url = await self.shorten_url(f"steam://joinlobby/{game_id}/{lobby_id}/{user_id}")

            # Creating the embed for the Steam lobby response
            embed = discord.Embed(
                title="🎮 Steam Lobby Invite",
                description="Click the button below to join the Steam lobby!",
                color=discord.Color.blue()  # You can customize the color
            )
            embed.set_footer(text="Painwheel Is The Greatest Character!.")

            # Keep the button intact and use the embed for the message
            view = SteamLinkButton(short_url)
            await message.reply(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SteamLinkParser(bot))