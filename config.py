# ─── Public Bot Configuration ───────────────────────────────────
# This file is committed to GitHub. All settings here are public.
# Only DISCORD_TOKEN stays secret in the .env file.

# Role ID that triggers the welcome message
TARGET_ROLE_ID = 1275073147481358454

# Channel ID where messages are sent (general chat)
CHANNEL_ID = 1275073148370292748

# Channel ID where "say" commands are accepted (admin channel)
ADMIN_CHANNEL_ID = 1515451112046465105

# Plain text message that pings the user
# Available placeholders: {user.mention}, {user.name}, {user.id}
PING_MESSAGE = "{user.mention} just joined! Hellyo~! ♡"

# Embed description — supports emojis (<:name:id>), channel mentions (#channel_id), and \n for newlines
# Available placeholders: {user.mention}, {user.name}, {user.id}
EMBED_DESCRIPTION = "<:Happy:1275091838759469138> Grab your roles in #1275073147875622914\n\n<:Finger:1277935593367802007> Make sure to follow the #1275073147875622913\n\n<:Wink:1300100664290181202> Enjoy your stay and have fun ♡"

# Decorative thumbnail image (top-right corner of embed)
EMBED_THUMBNAIL_URL = "https://i.imgur.com/QfIZXUD.jpeg"

# Large banner image (bottom of embed)
EMBED_BANNER_URL = "https://i.imgur.com/krvxCEX.png"

# Embed accent color (hex format, e.g. 0xFFC7EF for pink)
EMBED_COLOR = 0xFFC7EF

# Leave grace period in seconds (if a verified member leaves within this time, bot sends a goodbye)
LEAVE_GRACE_SECONDS = 120