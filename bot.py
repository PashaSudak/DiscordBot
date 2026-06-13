"""
bot.py — Discord client initialisation and event wiring.

This is the only file that touches discord.Client. It sets up intents,
registers event listeners, and delegates to the handler modules.
"""

import os
import discord
from dotenv import load_dotenv
from handlers.welcome import handle_member_verified
from handlers.goodbye import handle_member_left
from handlers.say import handle_message as say_handler

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True       # Required for role-change & member-remove events
intents.message_content = True  # Required to read message content

client = discord.Client(intents=intents)


# ── Lifecycle ────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


# ── Role-gained welcome ─────────────────────────────────────────

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    await handle_member_verified(before, after)


# ── Early-leave goodbye ─────────────────────────────────────────

@client.event
async def on_member_remove(member: discord.Member):
    await handle_member_left(member)


# ── Discord "say" command (admin channel → general) ─────────────

@client.event
async def on_message(message: discord.Message):
    await say_handler(message)


# ── Launch ───────────────────────────────────────────────────────

def run():
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(TOKEN)