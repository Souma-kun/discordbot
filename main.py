import discord
from discord.ext import commands
import json
import os
from keep_alive import keep_alive  # Keep-alive module for uptime

# Bot configuration
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Channels and roles configuration
restricted_channels = [
    1179736032401424427,  # Replace with the ID of your first restricted channel
    1179743603493453865,  # Replace with the ID of another restricted channel
]
excluded_roles = [
    1179737910447185920,  # Replace with the ID of your moderator role
]

# Load or initialize the user message history
if os.path.exists("user_last_message.json"):
    try:
        with open("user_last_message.json", "r") as f:
            user_last_message = json.load(f)
    except json.JSONDecodeError:
        print("Invalid JSON format. Recreating the file.")
        user_last_message = {}
else:
    user_last_message = {}

def serialize_key(user_id, channel_id):
    """Convert the tuple (user_id, channel_id) into a string."""
    return f"{user_id}_{channel_id}"

def deserialize_key(key):
    """Convert the serialized string back into a tuple (user_id, channel_id)."""
    user_id, channel_id = key.split('_')
    return int(user_id), int(channel_id)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await initialize_message_history()

async def initialize_message_history():
    """Populate the user_last_message dictionary from recent channel history."""
    print("Initializing message history...")
    for channel_id in restricted_channels:
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"Channel with ID {channel_id} not found.")
            continue

        # Fetch recent messages from the channel
        recent_messages = [
            msg async for msg in channel.history(limit=100)
        ]

        # Process messages and store the last message for each user
        for message in recent_messages:
            if not message.author.bot:
                key = serialize_key(message.author.id, channel.id)
                user_last_message[key] = message.id

    # Save the history to a file
    with open("user_last_message.json", "w") as f:
        json.dump(user_last_message, f)
    print("Message history initialized.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if the message is in a restricted channel
    if message.channel.id in restricted_channels:
        # Check if the user has an excluded role
        if any(role.id in excluded_roles for role in message.author.roles):
            return  # Allow message without restriction

        user_id = message.author.id
        channel_id = message.channel.id
        key = serialize_key(user_id, channel_id)

        # Retrieve the user's last message ID for this channel
        if key in user_last_message:
            last_message_id = user_last_message[key]
        else:
            last_message_id = None

        # Fetch the latest messages in the channel
        recent_messages = [
            msg async for msg in message.channel.history(limit=50)
        ]

        # Filter messages to only include those after the user's last message
        if last_message_id:
            messages_after_last = [
                msg for msg in recent_messages if msg.id > last_message_id
            ]
        else:
            messages_after_last = recent_messages

        # Count messages from other users
        other_user_messages = [
            msg for msg in messages_after_last if msg.author.id != user_id
        ]

        if len(other_user_messages) < 8:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, you need to wait until 8 other trade ads are sent before posting again.",
                delete_after=10,
            )
            return

        # Update the user's last message ID for this channel
        user_last_message[key] = message.id

        # Save the updated history to the file
        with open("user_last_message.json", "w") as f:
            json.dump(user_last_message, f)

    # Allow the bot to process other commands
    await bot.process_commands(message)

# Keep-alive section
keep_alive()

# Run the bot
bot.run("MTMzMDEyNDYxODMwMzkzMDM4MA.GUL8kG.p_-BMmR-Jx6G3VQbAxzsygqAVkkF4ytq8Orkzw")
