import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel, PeerChannel, PeerChat

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

async def scrape_and_save_messages(group):
    try:
        messages = await client.get_messages(group, limit=2000)

        messages_data = []
        for message in messages:
            # Capture basic information
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
                    'message_id': message.forward.id,
                }

            messages_data.append(message_dict)

        # Use group.title for the file name, safely handling spaces and special characters
        safe_title = ''.join(c if c.isalnum() or c in ('_') else '_' for c in group.title)
        filename = f'{safe_title}_messages.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=4)

        print(f'Successfully saved {len(messages_data)} messages to {filename}')

    except Exception as e:
        print(f"Error: {e}")


async def main():
    group = await list_groups_and_channels()
    await scrape_and_save_messages(group)

with client:
    client.loop.run_until_complete(main())
