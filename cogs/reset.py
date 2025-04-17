import discord
from discord.ext import commands, tasks
from db.database import get_connection
import datetime

class ResetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_reset_task.start()  # Start the automatic monthly reset task

    def cog_unload(self):
        self.auto_reset_task.cancel()  # Stop the automatic reset task when the cog is unloaded

    @tasks.loop(time=datetime.time(hour=0, minute=0))  # Runs daily at midnight
    async def auto_reset_task(self):
        """Automatically resets the leaderboard, match history, and player data on the 1st of every month."""
        if datetime.datetime.now().day == 1:  # Only reset on the 1st of the month
            await self.reset_database()

    @commands.command()
    async def reset(self, ctx):
        """Manually resets the leaderboard, match history, and player data with user confirmation."""
        # Your Discord user ID
        authorized_user_id = "215296697704644608"

        # Check if the command author is the authorized user
        if str(ctx.author.id) != authorized_user_id:
            embed = discord.Embed(
                title="❌ Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"⚠️ Unauthorized attempt by user: {ctx.author.id}")
            return

        # Request confirmation
        embed = discord.Embed(
            title="⚠️ Confirm Reset",
            description="Are you sure you want to reset the **leaderboard, match history, and player data**?\n\n"
                        "Type `yes` to confirm or `no` to cancel within 60 seconds.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ["yes", "no"]

        try:
            confirmation = await self.bot.wait_for("message", timeout=60.0, check=check)
        except TimeoutError:
            embed = discord.Embed(
                title="⌛ Timeout",
                description="You took too long to respond. The reset operation was cancelled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if confirmation.content.lower() == "no":
            embed = discord.Embed(
                title="❌ Reset Cancelled",
                description="The reset operation has been cancelled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if confirmation.content.lower() == "yes":
            print(f"✅ Manual reset command approved by authorized user: {ctx.author.id}")  # Debug message
            try:
                await self.reset_database()
                embed = discord.Embed(
                    title="✅ Database Reset",
                    description="The **leaderboard, match history, and player data** have been successfully reset.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                print(f"❌ Error in manual reset command: {e}")
                embed = discord.Embed(
                    title="❌ Reset Failed",
                    description="An error occurred during the reset. Please check the logs for more details.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)

    async def reset_database(self):
        """Clears leaderboard, match history, and resets all players to 0 points and Bronze rank."""
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Drop and recreate matches table to reset match_id counter
            cursor.execute("DROP TABLE IF EXISTS matches")
            cursor.execute("""
                CREATE TABLE matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    winner_id TEXT NOT NULL,
                    loser_id TEXT NOT NULL,
                    winner_score INTEGER NOT NULL,
                    loser_score INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved BOOLEAN DEFAULT 0,
                    winner_points_gained INTEGER DEFAULT 0,
                    loser_points_lost INTEGER DEFAULT 0
                )
            """)
            print("✅ Matches table dropped and recreated!")

            # Reset leaderboard: all players start at 0 points and Bronze rank
            cursor.execute("UPDATE players SET points = 0, rank = 'Bronze'")
            print("✅ Leaderboard reset: All players set to 0 points and Bronze rank!")

            conn.commit()  # Save changes
            print("✅ Database changes successfully committed.")  # Debug confirmation

            # Send notification in the channel
            channel = self.bot.get_channel(1361559595490873415)  # Replace with your channel ID
            if channel:
                embed = discord.Embed(
                    title="🚨 Leaderboard Reset",
                    description=(
                        "@skullgirls **The leaderboard and match history have been reset!**\n"
                        "A new season has begun. Good luck and happy gaming!"
                    ),
                    color=discord.Color.gold()
                )
                await channel.send(embed=embed)
                print("📢 Notification sent successfully.")
            else:
                print("⚠️ Channel ID not found!")

        except Exception as e:
            print(f"❌ Error in reset_database function: {e}")
        finally:
            conn.close()

    @auto_reset_task.before_loop
    async def before_auto_reset_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ResetCog(bot))