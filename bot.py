"""
bot.py — Discord client initialisation and event wiring.

This is the only file that touches discord.Client. It sets up intents,
registers event listeners, and delegates to the handler modules.
"""

import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv
from handlers.welcome import handle_member_verified
from handlers.goodbye import handle_member_left
from handlers.say import register as register_say
from handlers.ban import register as register_ban, process_pending_bans

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

    # Register commands globally (appears in all guilds, may take up to 1 hour)
    register_say(tree)
    register_ban(tree)
    await tree.sync()
    print("[BOT] /say and /delayed-ban registered globally for all guilds.")
    print("[BOT] It may take up to 1 hour to appear in all servers.")
    print("[BOT] Both commands are available for admins only.")

    # Resume any pending bans that survived a restart
    asyncio.create_task(process_pending_bans(client))
    print("[BOT] Checking for pending bans...")


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