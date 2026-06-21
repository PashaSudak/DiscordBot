"""
chat_revive.py — Rate-limits pings on the "chat revive" role.

Rules:
  - The role is set to NOT mentionable after a ping.
  - After 12 hours the role is set back to mentionable.
  - If someone tries to ping while it's not mentionable → send embed warning.
  - Don't delete any messages.
  - Warning is rate-limited to once per 30 minutes.
"""

import asyncio
import time
import datetime
import discord
from discord import app_commands
import storage

CHAT_REVIVE_ROLE_ID = 1275073147439157336
COOLDOWN_SECONDS = 12 * 3600       # 12 hours
WARNING_COOLDOWN_SECONDS = 1800    # 30 minutes
CHECK_INTERVAL = 60                # Check role mentionable status every 60s

DATA_FILE = "chat_revive_cooldown.json"


def _timestamp() -> str:
    """Return a human-readable timestamp for log messages."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_data():
    """Returns: {last_ping_time: float, last_warning_time: float}"""
    data = storage.load_data(DATA_FILE, {})
    if "last_ping_time" not in data:
        data["last_ping_time"] = 0.0
    if "last_warning_time" not in data:
        data["last_warning_time"] = 0.0
    return data


def _save_data(data: dict):
    storage.save_data(DATA_FILE, data)


async def update_role_mentionable(guild: discord.Guild, mentionable: bool):
    """Set the chat revive role's mentionable attribute."""
    role = guild.get_role(CHAT_REVIVE_ROLE_ID)
    if role is None:
        print(f"[{_timestamp()}] [CHAT_REVIVE] ⚠️ Role ID {CHAT_REVIVE_ROLE_ID} not found in guild '{guild.name}' ({guild.id})")
        return
    if role.mentionable == mentionable:
        return  # Already in the desired state

    state_str = "mentionable ✅" if mentionable else "not mentionable ❌"
    try:
        await role.edit(mentionable=mentionable, reason="Chat revive cooldown")
        print(f"[{_timestamp()}] [CHAT_REVIVE] 🔄 Role '@{role.name}' ({role.id}) in '{guild.name}' → {state_str}")
    except discord.Forbidden:
        print(f"[{_timestamp()}] [CHAT_REVIVE] ⛔ Missing 'Manage Roles' permission to edit '@{role.name}' in '{guild.name}'")
    except discord.HTTPException as e:
        print(f"[{_timestamp()}] [CHAT_REVIVE] ❌ HTTP error editing '@{role.name}' in '{guild.name}': {e}")


async def background_loop(client: discord.Client):
    """
    Background task that runs every CHECK_INTERVAL seconds.
    Checks if the cooldown has expired and sets role mentionable accordingly.
    """
    await asyncio.sleep(5)  # Wait a moment for the client to be fully ready
    print(f"[{_timestamp()}] [CHAT_REVIVE] 🟢 Background loop started (checking every {CHECK_INTERVAL}s)")

    while True:
        try:
            data = _load_data()
            now = time.time()
            last_ping = data["last_ping_time"]
            elapsed = now - last_ping
            cooldown_expired = elapsed >= COOLDOWN_SECONDS

            if last_ping == 0:
                # No ping has ever happened — role should be mentionable
                for guild in client.guilds:
                    role = guild.get_role(CHAT_REVIVE_ROLE_ID)
                    if role and not role.mentionable:
                        print(f"[{_timestamp()}] [CHAT_REVIVE] ℹ️ No ping history — making '@{role.name}' mentionable in '{guild.name}'")
                        await update_role_mentionable(guild, True)
            else:
                remaining = COOLDOWN_SECONDS - elapsed
                for guild in client.guilds:
                    role = guild.get_role(CHAT_REVIVE_ROLE_ID)
                    if role is None:
                        continue

                    if cooldown_expired and not role.mentionable:
                        print(f"[{_timestamp()}] [CHAT_REVIVE] ⏰ Cooldown expired ({COOLDOWN_SECONDS/3600:.0f}h passed) — making '@{role.name}' mentionable in '{guild.name}'")
                        await update_role_mentionable(guild, True)
                    elif not cooldown_expired and role.mentionable:
                        print(f"[{_timestamp()}] [CHAT_REVIVE] 🔒 Cooldown active — {remaining/3600:.1f}h remaining — making '@{role.name}' NOT mentionable in '{guild.name}'")
                        await update_role_mentionable(guild, False)

        except Exception as e:
            print(f"[{_timestamp()}] [CHAT_REVIVE] ❌ Background loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


async def handle_message(message: discord.Message) -> bool:
    """
    Check if a message pings the chat revive role.
    Returns True if handled (warning sent), False otherwise.
    """
    if message.author.bot:
        return False

    role = message.guild.get_role(CHAT_REVIVE_ROLE_ID)
    if role is None:
        return False

    if role not in message.role_mentions:
        return False

    now = time.time()
    data = _load_data()
    last_ping = data["last_ping_time"]
    last_warning = data["last_warning_time"]
    elapsed = now - last_ping

    if elapsed >= COOLDOWN_SECONDS:
        # Cooldown expired → role should be mentionable already.
        # Reset cooldown timer and set role back to not mentionable.
        data["last_ping_time"] = now
        _save_data(data)
        await update_role_mentionable(message.guild, False)
        print(f"[{_timestamp()}] [CHAT_REVIVE] 🔔 Ping used by {message.author.name} in #{message.channel.name} — {COOLDOWN_SECONDS/3600:.0f}h cooldown started")
        return False  # Let the message through

    # Cooldown NOT expired → warn the user
    warning_elapsed = now - last_warning
    if warning_elapsed < WARNING_COOLDOWN_SECONDS:
        print(f"[{_timestamp()}] [CHAT_REVIVE] 🔇 Warning suppressed for {message.author.name} (30min cooldown, {WARNING_COOLDOWN_SECONDS - warning_elapsed:.0f}s remaining)")
        return True

    remaining_hours = (COOLDOWN_SECONDS - elapsed) / 3600
    remaining_hours = max(remaining_hours, 0)

    embed = discord.Embed(
        description=(
            "Please don't ping chat revive too often. ♡\n"
            f"Next available ping in **{remaining_hours:.1f} hours**. 𐔌՞. .՞𐦯"
        ),
        color=0xffb9dd,
    )

    try:
        await message.channel.send(embed=embed)
        print(f"[{_timestamp()}] [CHAT_REVIVE] ⚠️ Warning sent to {message.author.name} in #{message.channel.name} ({remaining_hours:.1f}h remaining)")
        data["last_warning_time"] = now
        _save_data(data)
    except discord.Forbidden:
        print(f"[{_timestamp()}] [CHAT_REVIVE] ⛔ Missing permissions to send warning in #{message.channel.name}")

    return True


def register(tree: app_commands.CommandTree):
    """No slash commands to register — runs via on_message + background loop."""
    pass