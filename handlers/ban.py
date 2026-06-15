"""
ban.py — Delayed ban slash command with persistent scheduling.

Command: /delayed-ban @user [minutes]
Permission: Administrator only
Action:   Schedules a ban of the user after the specified delay (in minutes).
          Survives bot restarts via JSON persistence.
          Does not delete the user's messages.
          Reply is ephemeral (only visible to the caller).
"""

import asyncio
import time
import discord
from discord import app_commands
import storage

PENDING_BANS_FILE = "pending_bans.json"


def _load_pending():
    """Load pending bans from disk. Returns dict: str(guild_id.user_id) -> {guild_id, user_id, ban_time, delay_minutes}"""
    return storage.load_data(PENDING_BANS_FILE, {})


def _save_pending(data: dict):
    storage.save_data(PENDING_BANS_FILE, data)


async def execute_ban(guild: discord.Guild, user_id: int, delay_minutes: int):
    """Ban a user by ID. Handles errors gracefully."""
    try:
        user = await guild.fetch_member(user_id)
        if user is None:
            print(f"[BAN] User {user_id} is no longer in the guild")
            return
        await guild.ban(
            user,
            reason=f"Delayed ban — {delay_minutes} minute(s) after command",
            delete_message_seconds=0,
        )
        print(f"[BAN] Banned {user.name} (ID: {user_id}) after {delay_minutes} minute(s)")
    except discord.Forbidden:
        print(f"[BAN] ERROR: Missing permissions to ban user ID {user_id}")
    except discord.NotFound:
        print(f"[BAN] User {user_id} not found (already left?)")
    except discord.HTTPException as e:
        print(f"[BAN] ERROR: Failed to ban user ID {user_id}: {e}")


async def process_pending_bans(client: discord.Client):
    """
    Load pending bans from disk and resume them.
    Called at bot startup.
    """
    pending = _load_pending()
    now = time.time()
    to_remove = []

    for key, data in pending.items():
        remaining = data["ban_time"] - now
        if remaining <= 0:
            # Already past the ban time — execute immediately
            guild = client.get_guild(data["guild_id"])
            if guild:
                asyncio.create_task(execute_ban(guild, data["user_id"], data["delay_minutes"]))
            to_remove.append(key)
        else:
            # Reschedule
            asyncio.create_task(_delayed_ban_from_data(client, data))

    # Clean up ones we already executed
    for key in to_remove:
        del pending[key]
    if to_remove:
        _save_pending(pending)

    count = len(pending) - len(to_remove)
    if count > 0:
        print(f"[BAN] Resumed {count} pending ban(s)")


async def _delayed_ban_from_data(client: discord.Client, data: dict):
    """Wait until ban_time, then execute the ban."""
    now = time.time()
    remaining = data["ban_time"] - now
    if remaining > 0:
        await asyncio.sleep(remaining)

    guild = client.get_guild(data["guild_id"])
    if guild:
        await execute_ban(guild, data["user_id"], data["delay_minutes"])

    # Remove from pending storage
    pending = _load_pending()
    key = f"{data['guild_id']}.{data['user_id']}"
    pending.pop(key, None)
    _save_pending(pending)


def register(tree: app_commands.CommandTree):
    """Register the /delayed-ban slash command globally."""

    @tree.command(
        name="delayed-ban",
        description="Ban a user after a delay (in minutes)",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def delayed_ban_command(
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

        if minutes > 1440:  # 24 hours max sanity check
            await interaction.response.send_message(
                "❌ Delay cannot exceed 1440 minutes (24 hours).",
                ephemeral=True,
            )
            return

        # Save to persistent storage
        ban_time = time.time() + (minutes * 60)
        key = f"{interaction.guild_id}.{user.id}"
        pending = _load_pending()
        pending[key] = {
            "guild_id": interaction.guild_id,
            "user_id": user.id,
            "ban_time": ban_time,
            "delay_minutes": minutes,
        }
        _save_pending(pending)

        # Acknowledge ephemerally
        await interaction.response.send_message(
            f"⏰ {user.mention} will be banned in **{minutes} minute(s)**.",
            ephemeral=True,
        )

        # Schedule the ban in the background
        asyncio.create_task(_delayed_ban_from_data(
            interaction.client,
            pending[key],
        ))

        print(f"[BAN] Scheduled: {user.name} (ID: {user.id}) in {minutes} min")