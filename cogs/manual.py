import discord
from discord.ext import commands
from discord.ui import View, Button

class ManualPaginator(View):
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

class FBManual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)  # Cooldown: 1 use per 60 seconds per user
    async def manual(self, ctx):
        """Shows the full manual for the FightBack bot with detailed descriptions."""

        embeds = []

        # Embed 1: Registration and Setup
        embed1 = discord.Embed(
            title="📘 FightBack Bot - Command Manual (1/4)",
            description="**Get started with FightBack!**",
            color=discord.Color.blue()
        )
        embed1.add_field(
            name="📝 Register",
            value=(
                "`!fb register [name]` - Register yourself as a player with a custom name.\n"
                "- **Required before participating in matches or leaderboards.**"
            ),
            inline=False
        )
        embed1.add_field(
            name="✏️ Edit Name",
            value="`!fb editname [new_name]` - Update your registered display name while keeping past records intact.",
            inline=False
        )
        embed1.add_field(
            name="❌ Leave",
            value=(
                "`!fb leave` - Delete your registration (but keep match history intact).\n"
                "- Includes a confirmation step."
            ),
            inline=False
        )
        embed1.set_footer(text="🔥 Ready to play? Start by registering your name!")
        embeds.append(embed1)

        # Embed 2: Matches and Points
        embed2 = discord.Embed(
            title="📘 FightBack Bot - Command Manual (2/4)",
            description="**Submit matches and track your points!**",
            color=discord.Color.blue()
        )
        embed2.add_field(
            name="⚔️ Record Match",
            value=(
                "`!fb match [winner] [loser] [winner_score] [loser_score]` - Submit a ranked match.\n"
                "- Winner **must score exactly 5 points**.\n"
                "- **Loser must approve** within 60 seconds.\n"
                "- Cooldown: 30 seconds between submissions."
            ),
            inline=False
        )
        embed2.add_field(
            name="⚙️ Point System",
            value=(
                "- **Base Points:** Winner gains **+5**, loser loses **-3**.\n"
                "- **Rank Differences:** Points adjusted based on rank.\n"
                "  - 🥉 **Bronze beats Gold:** Big upset → Bonus points!\n"
                "  - 🥇 **Gold beats Silver:** Standard gain/loss.\n"
                "  - 🔱 **Platinum beats Bronze:** Reduced points."
            ),
            inline=False
        )
        embed2.set_footer(text="🔢 Play fair! and try Painwheel!")
        embeds.append(embed2)

        # Embed 3: Match History and Rankings
        embed3 = discord.Embed(
            title="📘 FightBack Bot - Command Manual (3/4)",
            description="**Review your match history and track ranks!**",
            color=discord.Color.blue()
        )
        embed3.add_field(
            name="📜 Match History",
            value=(
                "`!fb history` - View all recorded matches.\n"
                "- Includes match ID, scores, and timestamps.\n"
                "- Pagination enabled (5 matches per page)."
            ),
            inline=False
        )
        embed3.add_field(
            name="🗂️ My Match History",
            value=(
                "`!fb myhistory` - View only your matches.\n"
                "- Includes timestamps and match outcomes.\n"
                "- Pagination enabled with cooldown."
            ),
            inline=False
        )
        embed3.add_field(
            name="🏆 Leaderboard",
            value=(
                "`!fb leaderboard` - See player rankings by total points.\n"
                "- Includes names, points, and rank icons.\n"
                "- Pagination enabled (10 players per page)."
            ),
            inline=False
        )
        embed3.set_footer(text="📊 Keep climbing the leaderboard!")
        embeds.append(embed3)

        # Embed 4: Ranks, Reset, and Utility Commands
        embed4 = discord.Embed(
            title="📘 FightBack Bot - Command Manual (4/4)",
            description="**Ranks, reset, and utility commands.**",
            color=discord.Color.blue()
        )
        embed4.add_field(
            name="🔢 Stats",
            value=(
                "`!fb stats` - Check your current points, rank, and progress.\n"
                "- Includes match history via pagination."
            ),
            inline=False
        )
        embed4.add_field(
            name="🔄 Reset",
            value=(
                "`!fb reset` - **Admin-only command** to reset all rankings and match history.\n"
                "- Use with caution! This action is irreversible."
            ),
            inline=False
        )
        embed4.add_field(
            name="📚 Manual",
            value=(
                "`!fb manual` - View this command list anytime.\n"
                "- Useful for new players!"
            ),
            inline=False
        )
        embed4.set_footer(text="🔥 Use these commands to stay ahead in FightBack!")
        embeds.append(embed4)

        view = ManualPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)

    @manual.error
    async def manual_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb manual` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FBManual(bot))