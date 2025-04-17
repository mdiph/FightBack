from discord.ext import commands
import discord
from discord.ui import View, Button

class PaginationView(View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current = 0
        self.total = len(embeds)

        # Buttons for navigation
        self.prev_button = Button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
        self.next_button = Button(label="Next ▶️", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page

        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    async def update_message(self, interaction):
        embed = self.embeds[self.current]
        page_number = self.current + 1
        total_pages = self.total
        embed.title = f"📊 FightBack Point & Rank System - Page {page_number}/{total_pages}"
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_page(self, interaction):
        if self.current > 0:
            self.current -= 1
            await self.update_message(interaction)

    async def next_page(self, interaction):
        if self.current < self.total - 1:
            self.current += 1
            await self.update_message(interaction)


class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)  # Cooldown: 1 use per 60 seconds per user
    async def system(self, ctx):
        """Displays the FightBack ranking and point system with pagination."""

        # First embed: Ranks & Point Requirements
        embed1 = discord.Embed(
            title="📊 FightBack Point & Rank System - Page (1/4)",
            description="A competitive ranking structure to reward skillful players!",
            color=0x00ffcc
        )
        embed1.add_field(
            name="🏆 **Ranks & Point Requirements**",
            value=(
                "🔱 **Platinum**: 100+ points\n"
                "🥇 **Gold**: 51 - 99 points\n"
                "🥈 **Silver**: 25 - 50 points\n"
                "🥉 **Bronze**: 0 - 24 points"
            ),
            inline=False
        )

        # Second embed: Match Point Logic
        embed2 = discord.Embed(
            title="📊 FightBack Point & Rank System - Page (2/4)",
            description="A competitive ranking structure to reward skillful players!",
            color=0x00ffcc
        )
        embed2.add_field(
            name="⚔️ **Match Point Logic**",
            value=(
                "- **Base Points**:\n"
                "   - Winner gains **+5** points.\n"
                "   - Loser loses **-3** points.\n\n"
                "- **Adjusted by Rank Difference**:\n"
                "   - If the **winner is higher-ranked**, they gain **less**.\n"
                "   - If the **winner is lower-ranked**, they gain **more**.\n"
                "   - Losers also lose **more or less** depending on rank gap.\n\n"
                "- **Examples**:\n"
                "   - 🥈 Silver beats 🥉 Bronze ➝ Standard +4/-2\n"
                "   - 🥇 Gold beats 🔱 Platinum ➝ Bonus! +9/-9\n"
                "   - 🔱 Platinum beats 🥈 Silver ➝ Reduced: +3/-1"
            ),
            inline=False
        )

        # Third embed: Match Rules and Tie Information
        embed3 = discord.Embed(
            title="📊 FightBack Point & Rank System - Page (3/4)",
            description="A competitive ranking structure to reward skillful players!",
            color=0x00ffcc
        )
        embed3.add_field(
            name="✅ **Match Rules**",
            value=(
                "- Matches must end **5-X** (winner must score 5).\n"
                "- Loser must score **less than 5**.\n"
                "- Losing player must **approve the match**.\n"
                "- All matches have a **30-second cooldown** per user.\n\n"
                "- **In case of a tie** (both players score 5), the match will be **invalid**.\n"
                "- Repeated failure to approve matches may result in a **temporary suspension** from matchmaking."
            ),
            inline=False
        )

        # Fourth embed: Registration Reminder & Footer
        embed4 = discord.Embed(
            title="📊 FightBack Point & Rank System - Page (4/4)",
            description="A competitive ranking structure to reward skillful players!",
            color=0x00ffcc
        )
        embed4.add_field(
            name="🔔 **New Players**",
            value="Make sure to register first with `!fb register` to start playing!",
            inline=False
        )
        embed4.set_footer(text="🔥 Keep competing to reach Platinum! So you can be the greatest Painwheel!")

        # All embeds to be used in pagination
        embeds = [embed1, embed2, embed3, embed4]

        # Create the pagination view
        view = PaginationView(embeds)

        # Send the first embed with pagination buttons
        await ctx.send(embed=embeds[0], view=view)

    @system.error
    async def system_error(self, ctx, error):
        """Handles cooldown errors by notifying the user of remaining time."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown Active",
                description=f"Please wait **{round(error.retry_after, 2)} seconds** before using `!fb system` again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemCog(bot))