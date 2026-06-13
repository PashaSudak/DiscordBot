"""
say.py — Discord command handler for forwarding messages.

When a user types "say [text]" in the designated admin channel,
the bot forwards [text] to the configured public channel (general).
"""

import discord
import config


async def handle_message(message: discord.Message) -> bool:
    """
    Check if the message is a 'say' command from the admin channel.
    Returns True if handled, False otherwise.
    """
    # Ignore bot's own messages
    if message.author.bot:
        return False

    # Only accept commands from the designated admin channel
    if message.channel.id != config.ADMIN_CHANNEL_ID:
        return False

    content = message.content.strip()

    if not content.startswith("say "):
        return False

    text = content[4:].strip()
    if not text:
        # No text after "say "
        await message.add_reaction("❌")
        return True

    # Send to the public target channel (general)
    target = message.guild.get_channel(config.CHANNEL_ID)
    if target is None:
        await message.add_reaction("❌")
        print(f"[SAY] ERROR: Target channel {config.CHANNEL_ID} not found")
        return True

    await target.send(text)
    await message.add_reaction("✅")
    print(f"[SAY] {message.author.name} → #{target.name}: {text}")
    return True