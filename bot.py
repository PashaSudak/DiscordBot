"""
bot.py — Discord client initialisation and event wiring.

This is the only file that touches discord.Client. It sets up intents,
registers event listeners, and delegates to the handler modules.
"""

import os
import asyncio
import time
import discord
from discord import app_commands
from dotenv import load_dotenv
from handlers.welcome import handle_member_verified
from handlers.goodbye import handle_member_left
from handlers.say import register as register_say
from handlers.ban import register as register_ban, process_pending_bans
from handlers.chat_revive import handle_message as chat_revive_handler, background_loop as chat_revive_loop
from handlers.caps import handle_message as caps_handler
import storage

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True       # Required for role-change & member-remove events
intents.message_content = True  # Required to read role mentions in messages

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SYNC_COOLDOWN_FILE = "last_sync_time.json"
SYNC_COOLDOWN_SECONDS = 300  # 5 minutes between syncs


def _can_sync() -> bool:
    """Check if enough time has passed since last sync (prevents 429 rate-limits)."""
    data = storage.load_data(SYNC_COOLDOWN_FILE, {"last_sync": 0})
    elapsed = time.time() - data["last_sync"]
    if elapsed < SYNC_COOLDOWN_SECONDS:
        remaining = SYNC_COOLDOWN_SECONDS - elapsed
        print(f"[BOT] Sync cooldown active — {remaining:.0f}s remaining. Skipping sync.")
        return False
    return True


def _mark_synced():
    storage.save_data(SYNC_COOLDOWN_FILE, {"last_sync": time.time()})


# ── Lifecycle ────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    print(f"Bot is in {len(client.guilds)} guild(s)")

    # Register commands
    register_say(tree)
    register_ban(tree)

    # Only sync if cooldown has passed (prevents 429 rate-limit bans)
    if _can_sync():
        try:
            await tree.sync()
            _mark_synced()
            print("[BOT] /say and /delayed-ban synced.")
        except discord.HTTPException as e:
            print(f"[BOT] Sync failed (rate-limited?): {e}")
            print("[BOT] Commands will still work after Discord refreshes them.")
    else:
        print("[BOT] Using previously synced commands.")

    # Resume any pending bans that survived a restart
    asyncio.create_task(process_pending_bans(client))
    print("[BOT] Checking for pending bans...")

    # Start chat revive background loop (toggles role mentionable state every 60s)
    asyncio.create_task(chat_revive_loop(client))
    print("[BOT] Chat revive rate-limiter started.")


# ── Role-gained welcome ─────────────────────────────────────────

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    await handle_member_verified(before, after)


# ── Early-leave goodbye ─────────────────────────────────────────

@client.event
async def on_member_remove(member: discord.Member):
    await handle_member_left(member)


# ── Message-based moderation (caps + chat revive) ──────────────

@client.event
async def on_message(message: discord.Message):
    # Run caps check first (may delete the message)
    await caps_handler(message)
    # Then run chat revive check
    await chat_revive_handler(message)


# ── Launch ───────────────────────────────────────────────────────

def run():
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(TOKEN)
