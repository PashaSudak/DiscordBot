"""
say.py — Slash command for sending messages.

Command: /say [text]
Permission: Administrator only
Action:   Sends [text] in the same channel where the command was used.
Works in every guild the bot is in.
"""

import discord
from discord import app_commands


def register(tree: app_commands.CommandTree):
    """Register the /say slash command globally (all guilds)."""

    @tree.command(
        name="say",
        description="Send a message in this channel",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def say_command(interaction: discord.Interaction, text: str):
        """Send `text` in the same channel the command was used in."""
        await interaction.response.send_message(text)
        print(f"[SAY] {interaction.user.name} → #{interaction.channel.name}: {text}")