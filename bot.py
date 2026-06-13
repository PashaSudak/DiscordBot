"""
bot.py — Discord client initialisation and event wiring.

This is the only file that touches discord.Client. It sets up intents,
registers event listeners, and delegates to the handler modules.
"""

import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from handlers.welcome import handle_member_verified
from handlers.goodbye import handle_member_left
from handlers.say import register as register_say

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True  # Required for role-change & member-remove events

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# ── Lifecycle ────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    print(f"Bot is in {len(client.guilds)} guild(s)")

    # Register /say and sync to the first guild the bot is in
    if client.guilds:
        guild = client.guilds[0]
        register_say(tree, guild.id)
        await tree.sync(guild=discord.Object(id=guild.id))
        print(f"[BOT] /say synced to guild: {guild.name} ({guild.id})")
        print("[BOT] /say is available for admins only.")
    else:
        print("[WARNING] Bot is not in any guild yet.")


# ── Role-gained welcome ─────────────────────────────────────────

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    await handle_member_verified(before, after)


# ── Early-leave goodbye ─────────────────────────────────────────

@client.event
async def on_member_remove(member: discord.Member):
    await handle_member_left(member)


# ── Launch ───────────────────────────────────────────────────────

def run():
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(TOKEN)