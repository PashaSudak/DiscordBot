"""
console.py — Asynchronous console command reader.

Runs as a background task while the bot is running.
Commands:
  say [text]    Send [text] to the configured channel.
  help          Show available commands.
  exit          Gracefully shut down the bot.
"""

import asyncio
import sys
import discord
import config


async def listen(client: discord.Client):
    """
    Read commands from stdin and execute them.
    Spawned as a background task from bot.py on_ready.
    """
    loop = asyncio.get_running_loop()

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        line = line.strip()
        if not line:
            continue

        if line.startswith("say "):
            text = line[4:].strip()
            if text:
                await _do_say(client, text)
        elif line == "help":
            _print_help()
        elif line == "exit":
            print("[CONSOLE] Shutting down...")
            await client.close()
            break
        else:
            print(f"[CONSOLE] Unknown command: {line}. Type 'help' for available commands.")


async def _do_say(client: discord.Client, text: str):
    """Send a plain text message to the configured channel."""
    channel = client.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"[CONSOLE] ERROR: Channel ID {config.CHANNEL_ID} not found")
        return
    await channel.send(text)
    print(f"[CONSOLE] ✅ Sent: {text}")


def _print_help():
    print("── Console Commands ──")
    print("  say [text]    Send a message to the configured channel")
    print("  help          Show this help")
    print("  exit          Shut down the bot")
    print("─────────────────────")