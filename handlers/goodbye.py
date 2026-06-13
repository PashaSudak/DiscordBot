"""
goodbye.py — Handles the on_member_remove event.

When a verified member leaves the server within the grace window (2 minutes),
sends a goodbye message to the target channel.
"""

import time
import discord
import config
import storage
from .embeds import build_goodbye_message


async def handle_member_left(member: discord.Member) -> bool:
    """
    Called by on_member_remove when a member leaves.
    Returns True if a goodbye was sent, False otherwise.
    """
    uid = str(member.id)

    timestamps = storage.load_timestamps()
    verified_at = timestamps.get(uid)
    if verified_at is None:
        return False  # never verified → nothing to do

    elapsed = time.time() - verified_at

    # Clean up the timestamp regardless of whether we send a goodbye
    timestamps.pop(uid, None)
    storage.save_timestamps(timestamps)

    # Only send goodbye if they left within the grace period
    if elapsed > config.LEAVE_GRACE_SECONDS:
        return False

    channel = member.guild.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"[WARNING] Channel ID {config.CHANNEL_ID} not found for goodbye")
        return False

    seconds = int(elapsed)
    message = build_goodbye_message(member, seconds)
    await channel.send(message)

    print(f"[OK] {member.name} left after {seconds}s — sent goodbye")
    return True