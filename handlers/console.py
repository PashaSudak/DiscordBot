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
    Works with Render's Web Shell (connects to container stdin/stdout).
    """
    loop = asyncio.get_running_loop()
    print("[CONSOLE] Ready. Type 'help' for commands.", flush=True)

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            # EOF (stdin closed / Web Shell disconnected)
            print("[CONSOLE] stdin closed, stopping listener.")
            break
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
            print("[CONSOLE] Shutting down...", flush=True)
            await client.close()
            break
        else:
            print(f"[CONSOLE] Unknown command: {line}. Type 'help' for available commands.", flush=True)


async def _do_say(client: discord.Client, text: str):
    """Send a plain text message to the configured channel."""
    channel = client.get_channel(config.CHANNEL_ID)
    if channel is None:
        print(f"[CONSOLE] ERROR: Channel ID {config.CHANNEL_ID} not found", flush=True)
        return
    await channel.send(text)
    print(f"[CONSOLE] ✅ Sent: {text}", flush=True)


def _print_help():
    print("── Console Commands ──")
    print("  say [text]    Send a message to the configured channel")
    print("  help          Show this help")
    print("  exit          Shut down the bot")
    print("─────────────────────")