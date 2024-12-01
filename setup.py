import json

def setup_config():
    print("Telegram Scraper Setup")

    # Collecting basic configuration details
    api_id = input("Enter your API ID: ").strip()
    api_hash = input("Enter your API Hash: ").strip()
    phone = input("Enter your phone number (with country code): ").strip()
    notification_group = input("Enter the name of the group you want to send notifications to: ")

    # Configuration data
    config_data = {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone': phone,
        'notification_group': notification_group,
    }

    # Save to config.json
    with open('config.json', 'w', encoding='utf-8') as config_file:
        json.dump(config_data, config_file, ensure_ascii=False, indent=4)

    print("\nConfiguration saved to config.json")

if __name__ == "__main__":
    setup_config()