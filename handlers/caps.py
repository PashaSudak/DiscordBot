"""
caps.py — Anti-caps-spam moderation.

Tracks the last 50 messages per user. If >70% of them are "caps-heavy"
(more than 50% of letters uppercase), the message is deleted and a DM is sent.

Warning tiers:
  1st offense (0 prior warnings) → DM warning only
  2nd offense (1 prior warning)  → DM + timeout 5 minutes
  3rd+ offense (2+ warnings)     → DM + timeout 1 hour

After any action the user gets a 10-message grace period where caps aren't counted.
"""

import time
import datetime
import discord
import storage

DATA_FILE = "caps_data.json"

# ── Constants ───────────────────────────────────────────────────────────────

CAPS_LETTER_THRESHOLD = 0.50   # A single message is "caps" if >50% of its letters are uppercase
CAPS_RATIO_TRIGGER = 0.70      # Action if >70% of the last 50 messages are caps
WINDOW_SIZE = 50               # Number of recent messages to consider
MIN_MESSAGES = 50              # Don't check until user has sent this many messages (total tracked)
GRACE_PERIOD = 10              # Messages after an action where caps don't count toward warnings

MUTE_5MIN = 300
MUTE_1HOUR = 3600

# Dedup: remember last 100 message IDs we've processed to avoid double-processing
_processed_ids = set()

# Prevent rapid-fire actions: after a warning/mute, skip caps checks for this user
# for ACTION_COOLDOWN seconds. Key: user_id_str, Value: unix timestamp when cooldown expires.
_action_cooldowns: dict = {}

ACTION_COOLDOWN_SECONDS = 30  # Don't take another action on the same user within 30s


def _is_duplicate(message_id: int) -> bool:
    """Check if we've already processed this message ID. Returns True if duplicate."""
    if message_id in _processed_ids:
        return True
    _processed_ids.add(message_id)
    # Keep the set from growing forever
    if len(_processed_ids) > 100:
        _processed_ids.clear()
    return False


# ── Data helpers ────────────────────────────────────────────────────────────

def _load_all():
    """Return the full caps-data dict. Structure:
    {
      "user_id_str": {
        "history": [{"caps": 0|1, "t": timestamp}, ...],   # last WINDOW_SIZE messages
        "warnings": 2,                                       # total actions taken
        "since_action": 5                                    # messages sent since last warning/mute
      }
    }
    """
    return storage.load_data(DATA_FILE, {})


def _save_all(data: dict):
    storage.save_data(DATA_FILE, data)


def _has_more_than_half_caps(text: str) -> bool:
    """Return True if more than 50% of letters in text are uppercase.
    Non-letter characters are ignored."""
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    upper = sum(1 for ch in letters if ch.isupper())
    return (upper / len(letters)) > CAPS_LETTER_THRESHOLD


# ── Main handler ────────────────────────────────────────────────────────────

async def handle_message(message: discord.Message) -> bool:
    """
    Check a message for caps abuse. Returns True if a warning/mute action was
    taken, False otherwise.
    """
    if message.author.bot:
        return False

    # Deduplicate — ignore if we already processed this message
    if _is_duplicate(message.id):
        return False

    text = message.content.strip()
    if not text:
        return False

    uid = str(message.author.id)
    is_caps = _has_more_than_half_caps(text)
    now = time.time()

    # ── Load / initialise user data ──────────────────────────────────────
    all_data = _load_all()
    user = all_data.setdefault(uid, {
        "history": [],
        "warnings": 0,
        "since_action": 0,
    })

    # ── Push this message onto rolling history ───────────────────────────
    user["history"].append({
        "caps": 1 if is_caps else 0,
        "t": now,
    })
    # Keep only the last WINDOW_SIZE entries
    if len(user["history"]) > WINDOW_SIZE:
        user["history"] = user["history"][-WINDOW_SIZE:]

    # Increment messages-since-last-action counter
    user["since_action"] += 1

    # ── Not enough data yet?  Just save and return ───────────────────────
    if len(user["history"]) < MIN_MESSAGES:
        _save_all(all_data)
        return False

    # ── Grace period: don't count caps toward warnings ───────────────────
    if user["since_action"] <= GRACE_PERIOD and user["warnings"] > 0:
        _save_all(all_data)
        return False

    # ── Action cooldown: prevent rapid successive actions ────────────────
    cooldown_until = _action_cooldowns.get(uid, 0)
    if now < cooldown_until:
        # User had an action taken within the last ACTION_COOLDOWN_SECONDS
        return False

    # ── Calculate caps ratio over the rolling window ─────────────────────
    total_in_window = len(user["history"])
    caps_in_window = sum(msg["caps"] for msg in user["history"])
    ratio = caps_in_window / total_in_window if total_in_window > 0 else 0.0

    if ratio <= CAPS_RATIO_TRIGGER:
        _save_all(all_data)
        return False  # Not enough caps — let the message through

    # ── Set action cooldown BEFORE any actual action (db write, DM, mute) ─
    _action_cooldowns[uid] = now + ACTION_COOLDOWN_SECONDS

    # ── TRIGGERED — Only delete THIS message if it is caps-heavy ─────────
    if is_caps:
        try:
            await message.delete()
            print(f"[CAPS] Deleted caps message from {message.author.name} ({ratio:.0%} caps)")
        except discord.Forbidden:
            print(f"[CAPS] Missing permissions to delete message from {message.author.name}")
        except discord.NotFound:
            pass
    else:
        # This specific message is fine, but the user's overall ratio is too high
        print(f"[CAPS] {message.author.name} at {ratio:.0%} caps — current message OK, not deleted")

    # ── Determine action based on prior warning count ────────────────────
    dm_text = f"Your CAPS usage is way too high — {ratio:.0%}\nPlease tone it down, or you might get muted if you keep it up (｡•̀ ⤙ •́ ｡ꐦ) !!!"

    user["warnings"] += 1
    user["since_action"] = 0  # Reset grace-period counter

    try:
        await message.author.send(dm_text)
        print(f"[CAPS] DM sent to {message.author.name}")
    except discord.Forbidden:
        print(f"[CAPS] Cannot DM {message.author.name} (DMs closed)")
    except discord.HTTPException as e:
        print(f"[CAPS] DM error for {message.author.name}: {e}")

    # ── Mute if this is the 2nd+ offense ─────────────────────────────────
    if user["warnings"] >= 3:
        mute_duration = MUTE_1HOUR
        reason_suffix = f"(3rd+ offense, {ratio:.0%} caps)"
    elif user["warnings"] == 2:
        mute_duration = MUTE_5MIN
        reason_suffix = f"(2nd offense, {ratio:.0%} caps)"
    else:
        mute_duration = None

    if mute_duration:
        try:
            until = discord.utils.utcnow() + datetime.timedelta(seconds=mute_duration)
            await message.author.timeout(until, reason=f"Excessive caps {reason_suffix}")
            duration_str = f"{mute_duration//60} minute(s)"
            print(f"[CAPS] Muted {message.author.name} for {duration_str}")
        except discord.Forbidden:
            print(f"[CAPS] Missing permissions to timeout {message.author.name}")
        except discord.HTTPException as e:
            print(f"[CAPS] Timeout error for {message.author.name}: {e}")

    _save_all(all_data)
    return True