"""
say.py — Slash command for forwarding messages to general chat.

Command: /say [text]
Permission: Administrator only
Action:   Sends [text] to the configured public channel (general).
"""

import discord
from discord import app_commands
import config


def register(tree: app_commands.CommandTree, guild_id: int):
    """Register the /say slash command on the command tree."""

    @tree.command(
        name="say",
        description="Send a message to the general channel",
        guild=discord.Object(id=guild_id),
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def say_command(interaction: discord.Interaction, text: str):
        """Forward `text` to the configured public channel."""

        target = interaction.guild.get_channel(config.CHANNEL_ID)
        if target is None:
            await interaction.response.send_message(
                f"❌ Target channel (ID: {config.CHANNEL_ID}) not found.",
                ephemeral=True,
            )
            return

        await target.send(text)
        await interaction.response.send_message(
            f"✅ Sent to #{target.name}",
            ephemeral=True,
        )
        print(f"[SAY] {interaction.user.name} → #{target.name}: {text}")