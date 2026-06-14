"""
ban.py — Delayed ban slash command.

Command: /ban @user [minutes]
Permission: Administrator only
Action:   Schedules a ban of the user after the specified delay (in minutes).
          Does not delete the user's messages.
          Reply is ephemeral (only visible to the caller).
"""

import asyncio
import discord
from discord import app_commands


# Store pending ban tasks so they can be tracked (optional)
_pending_bans: dict = {}

def register(tree: app_commands.CommandTree):
    """Register the /ban slash command globally."""

    @tree.command(
        name="ban",
        description="Ban a user after a delay (in minutes)",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def ban_command(
        interaction: discord.Interaction,
        user: discord.Member,
        minutes: int,
    ):
        """Ban `user` after `minutes` minutes. Admin only."""

        if minutes <= 0:
            await interaction.response.send_message(
                "❌ Delay must be a positive number of minutes.",
                ephemeral=True,
            )
            return

        # Acknowledge ephemerally
        await interaction.response.send_message(
            f"⏰ {user.mention} will be banned in **{minutes} minute(s)**.",
            ephemeral=True,
        )

        # Schedule the ban in the background
        asyncio.create_task(_delayed_ban(interaction.guild, user, minutes))


async def _delayed_ban(guild: discord.Guild, user: discord.Member, delay_minutes: int):
    """Wait for the delay, then ban the user without deleting messages."""

    delay_seconds = delay_minutes * 60
    await asyncio.sleep(delay_seconds)

    try:
        await guild.ban(
            user,
            reason=f"Delayed ban — {delay_minutes} minute(s) after command",
            delete_message_seconds=0,  # Do NOT delete their messages
        )
        print(f"[BAN] Banned {user.name} (ID: {user.id}) after {delay_minutes} minute(s)")
    except discord.Forbidden:
        print(f"[BAN] ERROR: Missing permissions to ban {user.name}")
    except discord.HTTPException as e:
        print(f"[BAN] ERROR: Failed to ban {user.name}: {e}")