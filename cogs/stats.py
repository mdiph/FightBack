import discord
from discord.ext import commands
from discord.ui import View, Button
from db.database import get_connection


class StatsPaginator(View):
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


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def stats(self, ctx):
        """Display the user's rank, points, progress, and match history (only available with pagination)."""
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch player's rank and points
        cursor.execute("SELECT username, points FROM players WHERE discord_id = ?", (str(ctx.author.id),))
        player = cursor.fetchone()

        if not player:
            conn.close()
            embed = discord.Embed(
                title="❌ Stats Lookup Failed",
                description="You are not registered yet. Please register first using `!fb register YourName`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        username, points = player
        rank = self.get_rank(points)
        next_rank_points = self.get_next_rank_points(rank)

        # Fetch match history
        cursor.execute("""
            SELECT m.id, p1.username, p2.username, m.winner_score, m.loser_score, m.timestamp,
                   m.winner_points_gained, m.loser_points_lost
            FROM matches m
            JOIN players p1 ON m.winner_id = p1.discord_id
            JOIN players p2 ON m.loser_id = p2.discord_id
            WHERE m.winner_id = ? OR m.loser_id = ?
            ORDER BY m.timestamp DESC
        """, (str(ctx.author.id), str(ctx.author.id)))
        matches = cursor.fetchall()
        conn.close()

        # Embed for rank and points
        rank_embed = discord.Embed(
            title=f"🏅 {username}'s Rank",
            color=discord.Color.blue()
        )
        rank_embed.add_field(name="Current Rank", value=f"**{rank}**", inline=False)
        rank_embed.add_field(name="Current Points", value=f"**{points}**", inline=False)
        if rank != "Platinum":
            rank_embed.add_field(
                name="Points for Next Rank",
                value=f"{next_rank_points - points} points to **{self.get_next_rank_name(rank)}**",
                inline=False
            )
        else:
            rank_embed.add_field(name="Points for Next Rank", value="🎉 Max rank achieved!", inline=False)

        rank_embed.set_footer(text="🔹 Use the ▶️ button to view your match history. (Try Painwheel!)")

        # If no matches, send only rank embed
        if not matches:
            rank_embed.set_footer(text="❌ No match history found.")
            await ctx.send(embed=rank_embed)
            return

        embeds = [rank_embed]

        # Embed for paginated matches (5 matches per page)
        matches_per_page = 5
        total_pages = max((len(matches) - 1) // matches_per_page + 1, 1)  # Ensure at least 1 page

        for i in range(0, len(matches), matches_per_page):
            page_matches = matches[i:i + matches_per_page]
            page_number = len(embeds)  # Page starts at index 1
            paginated_embed = discord.Embed(
                title=f"📜 Match History - Page {page_number}/{total_pages}",
                description=f"Displaying match history for {ctx.author.mention}.",
                color=0x00ffcc
            )
            for match in page_matches:
                match_id, winner_name, loser_name, winner_score, loser_score, timestamp, points_gained, points_lost = match
                paginated_embed.add_field(
                    name=f"🆔 Match ID: {match_id}",
                    value=(f"🏆 Winner: **{winner_name}** (+{points_gained})\n"
                           f"💔 Loser: **{loser_name}** (-{abs(points_lost)})\n"
                           f"📊 Score: {winner_score} - {loser_score}\n"
                           f"🕒 Date: {timestamp}"),
                    inline=False
                )
            paginated_embed.set_footer(text="Use ◀️ and ▶️ to navigate pages.")
            embeds.append(paginated_embed)

        # Send rank embed first, then attach pagination for history
        view = StatsPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @stats.error
    async def stats_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb stats` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)


    def get_rank(self, points):
        """Determine the player's rank based on their points."""
        if points >= 100:
            return "Platinum"
        elif points >= 50:
            return "Gold"
        elif points >= 25:
            return "Silver"
        else:
            return "Bronze"

    def get_next_rank_points(self, rank):
        """Determine the points required for the next rank."""
        if rank == "Platinum":
            return 100  # Max rank achieved
        elif rank == "Gold":
            return 100
        elif rank == "Silver":
            return 50
        else:
            return 25

    def get_next_rank_name(self, rank):
        """Return the name of the next rank."""
        if rank == "Bronze":
            return "Silver"
        elif rank == "Silver":
            return "Gold"
        elif rank == "Gold":
            return "Platinum"
        else:
            return "Max Rank"

async def setup(bot):
    await bot.add_cog(StatsCog(bot))