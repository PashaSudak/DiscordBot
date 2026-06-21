"""
caps_stats.py — /caps slash command.

Shows an embed listing users sorted by caps ratio (highest first).
Paginated: 10 users per page with ◀ ▶ buttons.
Buttons expire after 60 seconds.
Uses the same caps_data.json as the caps moderation module.
"""

import time
import discord
from discord import app_commands
import storage

DATA_FILE = "caps_data.json"
PAGE_SIZE = 10
BUTTON_TIMEOUT = 60  # seconds


class CapsPaginator(discord.ui.View):
    """View with left/right buttons for paginating the caps leaderboard."""

    def __init__(self, pages: list[discord.Embed], author_id: int):
        super().__init__(timeout=BUTTON_TIMEOUT)
        self.pages = pages
        self.current = 0
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the person who used the command can navigate.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = (self.current + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    async def on_timeout(self):
        self.stop()


def _build_pages(guild: discord.Guild) -> list[discord.Embed]:
    """Build a list of embed pages from caps_data.json, sorted by caps ratio descending."""
    all_data = storage.load_data(DATA_FILE, {})
    now = time.time()

    rows = []
    for uid_str, user_data in all_data.items():
        history = user_data.get("history", [])
        if not history:
            continue

        total = len(history)
        caps_count = sum(msg.get("caps", 0) for msg in history)
        ratio = caps_count / total if total > 0 else 0.0

        # Try to get the member's name
        member = guild.get_member(int(uid_str))
        name = member.display_name if member else f"Unknown ({uid_str})"

        rows.append((name, ratio, caps_count, total))

    # Sort by ratio descending
    rows.sort(key=lambda r: r[1], reverse=True)

    if not rows:
        embed = discord.Embed(
            description="No caps data available yet.",
            color=0xffb9dd,
        )
        return [embed]

    # Split into pages
    pages = []
    for i in range(0, len(rows), PAGE_SIZE):
        chunk = rows[i:i + PAGE_SIZE]
        embed = discord.Embed(
            title="Caps Leaderboard",
            description=f"Top caps users (last 50 messages each)\nPage {len(pages) + 1}/{(len(rows) - 1) // PAGE_SIZE + 1}",
            color=0xffb9dd,
        )

        for rank, (name, ratio, caps_count, total) in enumerate(chunk, start=i + 1):
            bar = "█" * int(ratio * 10) + "░" * (10 - int(ratio * 10))
            embed.add_field(
                name=f"#{rank} {name}",
                value=f"{bar} {ratio:.0%} ({caps_count}/{total})",
                inline=False,
            )

        pages.append(embed)

    return pages


def register(tree: app_commands.CommandTree):
    """Register the /caps slash command globally."""

    @tree.command(
        name="caps",
        description="Show caps usage leaderboard",
    )
    async def caps_command(interaction: discord.Interaction):
        """Display paginated caps ratio list."""
        await interaction.response.defer()

        pages = _build_pages(interaction.guild)
        view = CapsPaginator(pages, interaction.user.id)

        await interaction.followup.send(embed=pages[0], view=view)