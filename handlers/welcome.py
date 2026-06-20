"""
welcome.py — Handles the on_member_update event.

When a member receives the target role (verified):
  1. Records a timestamp for the goodbye tracker.
  2. Checks 1-message-per-user limit.
  3. Sends a plain-text ping + a rich embed to the target channel.
"""

import time
import discord
import config
import storage
from .embeds import build_ping_message, build_welcome_embed


async def handle_member_verified(before: discord.Member, after: discord.Member) -> bool:
    """
    Called by on_member_update when a role change is detected.
    Returns True if a welcome was sent, False otherwise.
    """
    # --- Detect that the target role was ADDED (not just present) ---
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    if config.TARGET_ROLE_ID not in (after_ids - before_ids):
        return False

    # --- 1-message-per-user guard (check BEFORE recording anything) ---
    welcomed = storage.load_welcomed_users()
    if after.id in welcomed:
        print(f"[SKIP] {after.name} (ID: {after.id}) already welcomed previously")
        return False

    welcomed.add(after.id)
    storage.save_welcomed_users(welcomed)

    # --- Record verification time (used by goodbye tracker) ---
    timestamps = storage.load_timestamps()
    timestamps[str(after.id)] = time.time()
    storage.save_timestamps(timestamps)

    # --- Resolve target channel ---
    channel = after.guild.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"[WARNING] Channel ID {config.CHANNEL_ID} not found")
        return False

    # --- Send ping + embed ---
    ping = build_ping_message(after)
    await channel.send(ping)

    embed = build_welcome_embed(after)
    await channel.send(embed=embed)

    print(f"[OK] Sent welcome to {after.name} in #{channel.name}")
    return True