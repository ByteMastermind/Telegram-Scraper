import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel, PeerChannel, PeerChat
from telethon import events

# Load configuration from config.json
def load_config():
    with open('config.json', 'r', encoding='utf-8') as config_file:
        return json.load(config_file)

config = load_config()
api_id = config['api_id']
api_hash = config['api_hash']
phone = config['phone']

# Connect to Telegram
client = TelegramClient('session_name', api_id, api_hash)
client.start(phone=phone)

async def list_groups_and_channels():
    dialogs = await client.get_dialogs()

    # Filter for groups and channels (including broadcast channels)
    groups_and_channels = [
        dialog for dialog in dialogs
        if dialog.is_group or dialog.is_channel
    ]

    if not groups_and_channels:
        print("No groups or channels found.")
        return None

    print("Select a group or channel to scrape:")
    for idx, dialog in enumerate(groups_and_channels, start=1):
        print(f"{idx}. {dialog.name}")

    # Get user input and handle out-of-range errors
    choice = int(input("Enter the number of the group or channel: ")) - 1
    if 0 <= choice < len(groups_and_channels):
        return groups_and_channels[choice].entity
    else:
        print("Invalid choice. Please try again.")
        return await list_groups_and_channels()


def save_message_to_json(message, filename):
    """Appends a new message to the JSON file."""
    try:
        # Load existing messages from the file
        with open(filename, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
    except FileNotFoundError:
        messages_data = []

    # Capture basic information (same as before)
    message_dict = {
        'id': message.id,
        'date': str(message.date),
        'sender_id': message.sender_id,
        'text': message.text,
        'message_type': type(message).__name__,
        'media': str(message.media) if message.media else None,
        'is_private': message.is_private,
        'reply_to_msg_id': message.reply_to_msg_id,
        'via_bot_id': message.via_bot_id,
        'sticker': str(message.sticker) if message.sticker else None,
        'poll': str(message.poll) if message.poll else None,
        'geo': str(message.geo) if message.geo else None,
        'entities': [entity.to_dict() for entity in message.entities] if message.entities else [],
    }

    # If the message is forwarded, add forward details
    if message.forward:
        message_dict['forwarded_from'] = {
            'sender_id': message.forward.sender_id,
            'date': str(message.forward.date),
            # 'message_id': message.forward.id,
        }

    messages_data.append(message_dict)

    # Save updated messages to the file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(messages_data, f, ensure_ascii=False, indent=4)



async def main():
    group = await list_groups_and_channels()

    # Use group.title for the file name
    safe_title = ''.join(c if c.isalnum() or c in ('_') else '_' for c in group.title)
    filename = f'{safe_title}_messages.json'

    # Initial scrape to populate the JSON file (only once)
    try:
        print('here')
        # Check if the file exists and load existing messages
        with open(filename, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
            print(f"Loaded {len(messages_data)} existing messages from {filename}")
    except FileNotFoundError:
        messages_data = []
        print(f"Scraping initial messages from {group.title}...")
        async for message in client.iter_messages(group, limit=2000):
            save_message_to_json(message, filename)
        print(f"Initial messages saved to {filename}")

    @client.on(events.NewMessage(chats=group))
    async def new_message_handler(event):
        print(f"New message received in {group.title}: {event.message.text}")
        save_message_to_json(event.message, filename)

    print(f"Listening for new messages in {group.title}...")
    await client.run_until_disconnected() 

with client:
    client.loop.run_until_complete(main())