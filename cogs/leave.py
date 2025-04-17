import discord
from discord.ext import commands
from db.database import get_connection

class LeaveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def leave(self, ctx):
        """Allows the user to delete their registration (not history) after a second approval."""
        conn = get_connection()
        cursor = conn.cursor()

        # Check if the user is registered
        cursor.execute("SELECT username FROM players WHERE discord_id = ?", (str(ctx.author.id),))
        player = cursor.fetchone()

        if not player:  # If no player is found, exit early
            embed = discord.Embed(
                title="❌ Not Registered",
                description="You are not registered yet. Use `!fb register` to join the FightBack system!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            conn.close()
            return

        username = player[0]

        # Send approval prompt as an embed
        prompt_embed = discord.Embed(
            title="⚠️ Confirm Leave Request",
            description=(
                f"Are you sure you want to **leave the FightBack system** and delete your registration, **{username}**?\n\n"
                "Type `yes` to confirm or `no` to cancel within 60 seconds."
            ),
            color=discord.Color.orange()
        )
        prompt_embed.set_footer(text="This will not delete your match history.")
        await ctx.send(embed=prompt_embed)

        def check(msg):
            return msg.author.id == ctx.author.id and msg.channel == ctx.channel and msg.content.lower() in ["yes", "no"]

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
        except:
            timeout_embed = discord.Embed(
                title="⌛ Timeout",
                description="You took too long to respond. Your leave request was cancelled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=timeout_embed)
            conn.close()
            return

        if msg.content.lower() == "no":
            cancel_embed = discord.Embed(
                title="❌ Leave Cancelled",
                description="Your registration was not deleted.",
                color=discord.Color.red()
            )
            await ctx.send(embed=cancel_embed)
            conn.close()
            return

        if msg.content.lower() == "yes":  # User confirms deletion
            cursor.execute("DELETE FROM players WHERE discord_id = ?", (str(ctx.author.id),))
            conn.commit()

            confirm_embed = discord.Embed(
                title="✅ Registration Deleted",
                description=f"Your FightBack registration has been removed, **{username}**.\n"
                            "You can rejoin anytime using `!fb register`.",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirm_embed)

        conn.close()

    @leave.error
    async def leave_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb leave` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaveCog(bot))