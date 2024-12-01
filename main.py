import requests
import os
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

API_KEY = os.getenv("HELIUS_API_KEY")
WEBHOOK_URL = "http://54.79.31.7:8004"
GAS_SUPPLIER_CONTRACT = "59L2oxymiQQ9Hvhh92nt8Y7nDYjsauFkdb3SybdnsG6h"


def register_webhook():
    url = f"https://api.helius.xyz/v0/webhooks?api-key={API_KEY}"
    payload = {
        "webhookURL": WEBHOOK_URL,
        "transactionTypes": ["TRANSFER"],
        "accountAddresses": [GAS_SUPPLIER_CONTRACT],
        "webhookType": "enhanced",
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Successfully registered webhook for gas supplier contract")
        return True, response.json()
    else:
        print(f"Failed to create webhook: {response.status_code} - {response.text}")
        return False, None


if __name__ == "__main__":
    print("Starting webhook registration...")
    print(f"Using API key: {API_KEY[:4]}...{API_KEY[-4:]}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Monitoring gas supplier contract: {GAS_SUPPLIER_CONTRACT}")

    status, response = register_webhook()

    if status:
        print("\nWebhook registration successful!")
    else:
        print("\nWebhook registration failed!")
