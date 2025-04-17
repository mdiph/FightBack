import discord
from discord.ext import commands
from discord.ui import View, Button
from db.database import get_connection

class PaginationView(View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current = 0
        self.total = len(embeds)

        self.prev_button = Button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
        self.next_button = Button(label="Next ▶️", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page

        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    async def update_message(self, interaction):
        embed = self.embeds[self.current]
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page(self, interaction):
        if self.current > 0:
            self.current -= 1
            await self.update_message(interaction)

    async def next_page(self, interaction):
        if self.current < self.total - 1:
            self.current += 1
            await self.update_message(interaction)

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)  # Cooldown: 1 use per 60 seconds per user
    async def leaderboard(self, ctx):
        """Display the full leaderboard with pagination."""
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT username, points 
                FROM players 
                ORDER BY points DESC
            """)
            leaderboard = cursor.fetchall()
        except Exception as e:
            embed = discord.Embed(
                title="❌ Leaderboard Error",
                description=f"An error occurred while fetching the leaderboard:\n```{e}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        conn.close()

        if not leaderboard:
            embed = discord.Embed(
                title="📭 Empty Leaderboard",
                description="No players found yet. Be the first to register and climb to the top!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        players_per_page = 10
        embeds = []

        for i in range(0, len(leaderboard), players_per_page):
            page_players = leaderboard[i:i + players_per_page]
            page_number = len(embeds) + 1
            total_pages = (len(leaderboard) - 1) // players_per_page + 1

            embed = discord.Embed(
                title=f"🏆 FightBack Leaderboard - Page {page_number}/{total_pages}",
                description="**The ultimate fight for glory begins!**\nKeep on hating, Painwheel still the greatest!!.",
                color=0xf1c40f  # Gold
            )
            embed.set_thumbnail(url="https://gamesline.net/wp-content/uploads/2013/12/painwheel-grin-1024x751.jpg")  # Trophy/icon

            def get_rank_icon(points):
                if points >= 100:
                    return "🔱 Platinum"
                elif points >= 50:
                    return "🥇 Gold"
                elif points >= 25:
                    return "🥈 Silver"
                else:
                    return "🥉 Bronze"

            for rank, (username, points) in enumerate(page_players, start=i + 1):
                place_icon = ""
                if rank == 1:
                    place_icon = "👑"
                elif rank == 2:
                    place_icon = "🥈"
                elif rank == 3:
                    place_icon = "🥉"
                elif rank <= 10:
                    place_icon = "🔥"
                else:
                    place_icon = "🎯"

                player_rank = get_rank_icon(points)
                embed.add_field(
                    name=f"{place_icon} #{rank} - {username}",
                    value=f"**Rank:** {player_rank}\n**Points:** `{points}`",
                    inline=False
                )

            embed.set_footer(text="Use ◀️ ▶️ to scroll. Skullgirls Time!. 💪")
            embeds.append(embed)

        view = PaginationView(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @leaderboard.error
    async def leaderboard_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb leaderboard` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))