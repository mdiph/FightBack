import discord
from discord.ext import commands
from discord.ui import View, Button
from db.database import get_connection

class MyHistoryPaginator(View):
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

class MyHistoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)  # Cooldown: 1 use per 60 seconds per user
    async def myhistory(self, ctx):
        """View only your matches with button-based pagination."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM players WHERE discord_id = ?", (str(ctx.author.id),))
        player = cursor.fetchone()

        if not player:
            embed = discord.Embed(
                title="❌ Not Registered",
                description="You are not registered. Please use `!fb register` to join the FightBack system before viewing your match history.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        cursor.execute("""
            SELECT m.id, 
                   COALESCE(p1.username, '[Left Player]') AS winner_name,
                   COALESCE(p2.username, '[Left Player]') AS loser_name,
                   m.winner_score, m.loser_score, m.timestamp,
                   m.winner_points_gained, m.loser_points_lost
            FROM matches m
            LEFT JOIN players p1 ON m.winner_id = p1.discord_id
            LEFT JOIN players p2 ON m.loser_id = p2.discord_id
            WHERE m.winner_id = ? OR m.loser_id = ?
            ORDER BY m.timestamp DESC
        """, (str(ctx.author.id), str(ctx.author.id)))

        matches = cursor.fetchall()
        conn.close()

        if not matches:
            embed = discord.Embed(
                title="📭 No Match History",
                description="You haven't played any matches yet.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        matches_per_page = 5
        embeds = []

        for i in range(0, len(matches), matches_per_page):
            page_matches = matches[i:i + matches_per_page]
            page_number = len(embeds) + 1
            total_pages = (len(matches) - 1) // matches_per_page + 1

            embed = discord.Embed(
                title=f"📜 My Match History - Page {page_number}/{total_pages}",
                description=f"Displaying match history for {ctx.author.mention}.",
                color=0x00ffcc
            )

            for match in page_matches:
                match_id, winner_name, loser_name, winner_score, loser_score, timestamp, points_gained, points_lost = match
                embed.add_field(
                    name=f"🆔 Match ID: {match_id}",
                    value=(
                        f"🏆 Winner: **{winner_name}** (+{points_gained})\n"
                        f"💔 Loser: **{loser_name}** (-{abs(points_lost)})\n"
                        f"📊 Score: {winner_score} - {loser_score}\n"
                        f"🕒 Date: {timestamp}"
                    ),
                    inline=False
                )

            embed.set_footer(text="Use ◀️ and ▶️ to navigate pages.")
            embeds.append(embed)

        view = MyHistoryPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @myhistory.error
    async def myhistory_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb myhistory` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MyHistoryCog(bot))