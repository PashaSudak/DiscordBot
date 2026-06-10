"""
embeds.py — Discord embed and message builders.

All formatting logic for welcome/goodbye messages lives here.
Keeps the event handlers clean and makes messages easy to customise.
"""

import re
import discord
import config


def format_description(template: str, member: discord.Member) -> str:
    """Replace #channel_id -> <#channel_id> and \\n -> newlines, then substitute placeholders."""
    result = template.replace("\\n", "\n")
    result = re.sub(r'#(\d+)', lambda m: f"<#{m.group(1)}>", result)
    result = result.format(
        user=member,
        user_mention=member.mention,
        user_name=member.name,
        user_id=member.id,
    )
    return result


def build_ping_message(member: discord.Member) -> str:
    """Plain-text ping message sent *before* the embed."""
    return config.PING_MESSAGE.format(
        user=member,
        user_mention=member.mention,
        user_name=member.name,
        user_id=member.id,
    )


def build_welcome_embed(member: discord.Member) -> discord.Embed:
    """Rich embed that follows the ping message."""
    description = format_description(config.EMBED_DESCRIPTION, member)

    embed = discord.Embed(
        description=description,
        color=config.EMBED_COLOR,
    )
    embed.set_author(
        name=f"Welcome to the ✧ · Fluffy Corner · ✧ , {member.name}",
        icon_url=member.display_avatar.url,
    )
    embed.set_thumbnail(url=config.EMBED_THUMBNAIL_URL)
    embed.set_image(url=config.EMBED_BANNER_URL)
    return embed


def build_goodbye_message(member: discord.Member, seconds: int) -> str:
    """Text sent when a newly-verified member leaves within the grace window."""
    return (
        f"Oop- {member.name}, was with us for {seconds} seconds. "
        f"Bye Bye~! <:Sip:1275092435596214317>"
    )