import json

def setup_config():
    print("Telegram Scraper Setup")
    api_id = input("Enter your API ID: ").strip()
    api_hash = input("Enter your API Hash: ").strip()
    phone = input("Enter your phone number (with country code): ").strip()

    config_data = {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone': phone
    }

    # Save to config.json
    with open('config.json', 'w', encoding='utf-8') as config_file:
        json.dump(config_data, config_file, ensure_ascii=False, indent=4)

    print("Configuration saved to config.json")

if __name__ == "__main__":
    setup_config()
