import discord
import time
from discord.ext import commands
from db.database import get_connection

class MatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.match_cooldowns = {}

    def calculate_rank(self, points):
        if points >= 100:
            return "🔱 Platinum"
        elif points >= 50:
            return "🥇 Gold"
        elif points >= 25:
            return "🥈 Silver"
        else:
            return "🥉 Bronze"

    def get_rank_value(self, rank):
        return {"🥉 Bronze": 1, "🥈 Silver": 2, "🥇 Gold": 3, "🔱 Platinum": 4}.get(rank, 1)

    @commands.command()
    async def match(self, ctx, winner: discord.Member, loser: discord.Member, winner_score: int, loser_score: int):
        """Records a match with rank-based point system using embedded responses."""
        if winner == loser:
            embed = discord.Embed(
                title="❌ Invalid Match",
                description="Winner and loser cannot be the same person.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        max_score = 5
        if winner_score != max_score or loser_score >= max_score:
            embed = discord.Embed(
                title="❌ Invalid Score",
                description=f"The winner must have exactly {max_score} points, and the loser must have less.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if winner_score == loser_score:
            embed = discord.Embed(
                title="❌ Invalid Match",
                description="The score cannot be the same for both players.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        cooldown_time = 30
        current_time = time.time()

        if ctx.author.id in self.match_cooldowns:
            last_time = self.match_cooldowns[ctx.author.id]
            if current_time - last_time < cooldown_time:
                remaining = int(cooldown_time - (current_time - last_time))
                embed = discord.Embed(
                    title="⏳ Cooldown Active",
                    description=f"Please wait **{remaining} seconds** before submitting another match.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return

        self.match_cooldowns[ctx.author.id] = current_time

        conn = get_connection()
        cursor = conn.cursor()

        # Get both players' points and rank
        cursor.execute("SELECT points, rank FROM players WHERE discord_id = ?", (str(winner.id),))
        winner_data = cursor.fetchone()
        cursor.execute("SELECT points, rank FROM players WHERE discord_id = ?", (str(loser.id),))
        loser_data = cursor.fetchone()

        if not winner_data or not loser_data:
            embed = discord.Embed(
                title="❌ Registration Required",
                description="Both players must be registered using `!fb register`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        winner_points, winner_rank = winner_data
        loser_points, loser_rank = loser_data

        winner_rank_value = self.get_rank_value(winner_rank)
        loser_rank_value = self.get_rank_value(loser_rank)
        rank_difference = abs(winner_rank_value - loser_rank_value)

        # Points calculation
        base_gain = 5
        base_loss = 3

        if winner_rank_value == loser_rank_value:
            gain = base_gain
            loss = base_loss
        elif winner_rank_value > loser_rank_value:
            gain = max(base_gain - rank_difference, 1)
            loss = base_loss
        else:
            gain = base_gain + (rank_difference * 2)
            loss = base_loss + (rank_difference * 2)

        # Ask for match approval
        expected_responder = loser.id if ctx.author.id == winner.id else winner.id
        embed = discord.Embed(
            title="⚔️ Match Approval Required",
            description=(
                f"{self.bot.get_user(expected_responder).mention}, do you approve this match submitted by {ctx.author.mention}?\n"
                f"🏆 **Winner:** {winner.mention} ({winner_score})\n"
                f"💔 **Loser:** {loser.mention} ({loser_score})\n\n"
                "**Type `approve` or `cancel` within 60 seconds.**"
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author.id == expected_responder and m.channel == ctx.channel and m.content.lower() in ["approve", "cancel"]

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
        except:
            embed = discord.Embed(
                title="⌛ Timeout",
                description="Match approval timed out.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        if msg.content.lower() == "cancel":
            embed = discord.Embed(
                title="❌ Match Cancelled",
                description="The match was not recorded.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        embed = discord.Embed(
            title="✅ Match Approved",
            description=f"Match successfully recorded by {msg.author.mention}!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        # Update points and rank
        new_winner_points = winner_points + gain
        new_loser_points = max(loser_points - loss, 0)

        new_winner_rank = self.calculate_rank(new_winner_points)
        new_loser_rank = self.calculate_rank(new_loser_points)

        try:
            cursor.execute("UPDATE players SET points = ?, rank = ? WHERE discord_id = ?", (new_winner_points, new_winner_rank, str(winner.id)))
            cursor.execute("UPDATE players SET points = ?, rank = ? WHERE discord_id = ?", (new_loser_points, new_loser_rank, str(loser.id)))

            cursor.execute("""
                INSERT INTO matches (winner_id, loser_id, winner_score, loser_score, approved, winner_points_gained, loser_points_lost)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (str(winner.id), str(loser.id), winner_score, loser_score, gain, loss))

            conn.commit()

            cursor.execute("SELECT last_insert_rowid()")
            match_id = cursor.fetchone()[0]

            embed = discord.Embed(
                title="🏅 Match Recorded",
                description=f"🆔 **Match ID:** `{match_id}`\n"
                            f"🏆 {winner.mention} gained **{gain} points** → Total: **{new_winner_points}** ({new_winner_rank})\n"
                            f"💔 {loser.mention} lost **{loss} points** → Total: **{new_loser_points}** ({new_loser_rank})",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            conn.rollback()
            await ctx.send(f"❌ An error occurred while recording the match: `{str(e)}`")
        finally:
            conn.close()

    @match.error
    async def match_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "⚠️ Incomplete command.\n"
                "Usage: `!fb match @winner @loser <winner_score> <loser_score>`\n"
                "Example: `!fb match @Ryu @Ken 5 3`"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Invalid input. Make sure to mention users and use numbers for the scores.")
        else:
            await ctx.send("❌ An unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(MatchCog(bot))
