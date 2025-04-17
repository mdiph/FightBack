from discord.ext import commands
import discord
from db.database import get_connection

class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx, *, name: str = None):
        """Registers a user with a name, enforcing a 20-character limit."""
        if not name:
            embed = discord.Embed(
                title="❌ Registration Failed",
                description="Please provide a name for registration.\nExample: `!fb register YourName`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if len(name) > 20:
            embed = discord.Embed(
                title="❌ Name Too Long",
                description="Your name exceeds the **20-character limit**. Please choose a shorter name.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO players (discord_id, username) VALUES (?, ?)",
                (str(ctx.author.id), name)
            )
            conn.commit()
            embed = discord.Embed(
                title="✅ Registration Successful",
                description=f"You are now registered as **{name}**!",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Discord: {ctx.author}")
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(
                title="❌ Registration Failed",
                description="You are already registered.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        finally:
            conn.close()

    @commands.command()
    async def editname(self, ctx, *, new_name: str = None):
        """Allows users to edit their registered name with a 20-character limit."""
        if new_name is None:
            embed = discord.Embed(
                title="❌ Name Change Failed",
                description="Please provide a new name.\nExample: `!fb editname NewName`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if len(new_name) > 20:
            embed = discord.Embed(
                title="❌ Name Too Long",
                description="Your new name exceeds the **20-character limit**. Please choose a shorter name.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE players SET username = ? WHERE discord_id = ?",
            (new_name, str(ctx.author.id))
        )
        if cursor.rowcount == 0:
            embed = discord.Embed(
                title="❌ Name Change Failed",
                description="You're not registered yet.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            conn.commit()
            embed = discord.Embed(
                title="✅ Name Updated",
                description=f"Your name has been changed to **{new_name}**.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        conn.close()

async def setup(bot):
    await bot.add_cog(RegisterCog(bot))