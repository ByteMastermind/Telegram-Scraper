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
notification_group = config['notification_group']

# Connect to Telegram
client = TelegramClient('session_name', api_id, api_hash)
client.start(phone=phone)

async def send_message_to_group(group_name):
    # Search for the group by name
    entity = await client.get_entity(notification_group)
    
    message = f"An invitation link just landed to a group named {group_name}"

    # Send the message
    await client.send_message(entity, message)

async def is_invitation(message_dict, group_name):
    if message_dict.get('media') and 'MessageMediaWebPage' in message_dict['media'] and "site_name='Telegram'" in message_dict['media']:
        print(f"Invitation detected in {group_name}, message id: {message_dict['id']}.")
        return True  # Invitation detected
    return False  # No invitation detected

async def check_invitation(message_dict, group_name):
    is_message_invitation = await is_invitation(message_dict, group_name)
    if is_message_invitation:
        await send_message_to_group(group_name)

async def list_groups_and_channels():
    dialogs = await client.get_dialogs()

    # Filter for groups and channels
    groups_and_channels = [
        dialog for dialog in dialogs
        if dialog.is_group or dialog.is_channel
    ]

    if not groups_and_channels:
        print("No groups or channels found.")
        return []  # Return an empty list if no groups/channels are found

    selected_groups = []
    while True:
        print("\nSelect a group or channel to scrape (or enter 0 to finish):")
        for idx, dialog in enumerate(groups_and_channels, start=1):
            if dialog.name != notification_group:
                print(f"{idx}. {dialog.name}")

        try:
            choice = int(input("Enter the number: "))
            if choice == 0 and selected_groups:  # Finish if the user enters 0 and at least one group is selected
                break
            elif choice == 0 and not selected_groups:  # Prevent finishing if no groups are selected
                print("Please select at least one group/channel before entering 0.")
            elif 1 <= choice <= len(groups_and_channels):
                selected_group = groups_and_channels[choice - 1].entity
                if selected_group not in selected_groups:  # Prevent adding the same group multiple times
                    selected_groups.append(selected_group)
                    print(f"Added {groups_and_channels[choice - 1].name} to selection.")
                else:
                    print("This group/channel is already selected.")
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return selected_groups


async def save_message_to_json(message, filename, group_name):
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

    await check_invitation(message_dict, group_name)


async def main():
    groups = await list_groups_and_channels()

    @client.on(events.NewMessage(chats=groups))
    async def new_message_handler(event):
        # Find the group name using event.chat_id
        group_name = next((group.title for group in groups if abs(group.id) == abs(event.chat_id)), None)
        if group_name == None:
            return

        print(f"New message received in {group_name}: {event.message.text}")

        # Construct the filename using the group name
        safe_title = ''.join(c if c.isalnum() or c in ('_') else '_' for c in group_name)
        filename = f'{safe_title}_messages.json'
        await save_message_to_json(event.message, filename, group_name) 


    for group in groups:
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
                await save_message_to_json(message, filename, group.title)
            print(f"Initial messages saved to {filename}")

        print(f"Listening for new messages in {group.title}...")
    
    await client.run_until_disconnected() 

with client:
    client.loop.run_until_complete(main())