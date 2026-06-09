import os
import json
import time
import re
import discord
from dotenv import load_dotenv
import config

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

TARGET_ROLE_ID = config.TARGET_ROLE_ID
CHANNEL_ID = config.CHANNEL_ID
PING_MESSAGE_TEMPLATE = config.PING_MESSAGE
EMBED_DESCRIPTION = config.EMBED_DESCRIPTION
EMBED_THUMBNAIL_URL = config.EMBED_THUMBNAIL_URL
EMBED_BANNER_URL = config.EMBED_BANNER_URL
EMBED_COLOR = config.EMBED_COLOR
LEAVE_GRACE_SECONDS = config.LEAVE_GRACE_SECONDS

intents = discord.Intents.default()
intents.members = True  # Required to listen for member updates & member removal

DATA_FILE = "welcomed_users.json"
TIMESTAMPS_FILE = "verification_timestamps.json"


def load_json(path: str, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f)


client = discord.Client(intents=intents)

welcomed_users: set = set(load_json(DATA_FILE, []))

# user_id -> unix timestamp of when they got the target role
verification_timestamps: dict = load_json(TIMESTAMPS_FILE, {})


def save_welcomed():
    save_json(DATA_FILE, list(welcomed_users))


def save_timestamps():
    save_json(TIMESTAMPS_FILE, verification_timestamps)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")
    print(f"Target role ID: {TARGET_ROLE_ID}")
    print(f"Channel ID: {CHANNEL_ID}")
    print(f"Ping template: {PING_MESSAGE_TEMPLATE}")
    print(f"Embed description: {EMBED_DESCRIPTION}")
    print(f"Embed thumbnail: {EMBED_THUMBNAIL_URL}")
    print(f"Embed banner: {EMBED_BANNER_URL}")
    print(f"Already welcomed {len(welcomed_users)} user(s)")
    print(f"Tracking {len(verification_timestamps)} verification timestamp(s)")


def format_description(template: str, after: discord.Member) -> str:
    """Replace #channel_id with channel mentions and \\n with newlines."""

    result = template.replace("\\n", "\n")
    result = re.sub(r'#(\d+)', lambda m: f"<#{m.group(1)}>", result)
    result = result.format(
        user=after,
        user_mention=after.mention,
        user_name=after.name,
        user_id=after.id,
    )
    return result


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Fires when a member's profile or roles change."""

    before_role_ids = {role.id for role in before.roles}
    after_role_ids = {role.id for role in after.roles}
    added_role_ids = after_role_ids - before_role_ids

    if TARGET_ROLE_ID not in added_role_ids:
        return

    # Record verification timestamp
    verification_timestamps[str(after.id)] = time.time()
    save_timestamps()

    # Check 1-message limit
    if after.id in welcomed_users:
        print(f"[SKIP] {after.name} (ID: {after.id}) already welcomed previously")
        return

    welcomed_users.add(after.id)
    save_welcomed()

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"[WARNING] Channel ID {CHANNEL_ID} not found")
        return

    # 1) Plain text ping
    ping_text = PING_MESSAGE_TEMPLATE.format(
        user=after,
        user_mention=after.mention,
        user_name=after.name,
        user_id=after.id,
    )
    await channel.send(ping_text)

    # 2) Embed
    description = format_description(EMBED_DESCRIPTION, after)
    embed = discord.Embed(
        description=description,
        color=EMBED_COLOR,
    )
    embed.set_author(
        name=f"Welcome to the ✧ · Fluffy Corner · ✧ , {after.name}",
        icon_url=after.display_avatar.url,
    )
    embed.set_thumbnail(url=EMBED_THUMBNAIL_URL)
    embed.set_image(url=EMBED_BANNER_URL)

    await channel.send(embed=embed)
    print(f"[OK] Sent welcome to {after.name} in #{channel.name}")


@client.event
async def on_member_remove(member: discord.Member):
    """Fires when a member leaves the server."""

    user_id_str = str(member.id)

    # Check if they verified (have a timestamp)
    verified_at = verification_timestamps.get(user_id_str)
    if verified_at is None:
        return  # Never verified, ignore

    # Calculate how long they stayed
    elapsed = time.time() - verified_at

    # Clean up stored data
    verification_timestamps.pop(user_id_str, None)
    save_timestamps()

    # Only care if they leave within the grace period
    if elapsed > LEAVE_GRACE_SECONDS:
        return

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"[WARNING] Channel ID {CHANNEL_ID} not found for leave message")
        return

    seconds = int(elapsed)
    message = f"Oop- {member.name}, was with us for {seconds} seconds. Bye Bye~! <:Sip:1275092435596214317>"
    await channel.send(message)
    print(f"[OK] {member.name} left after {seconds}s — sent goodbye")


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(TOKEN)