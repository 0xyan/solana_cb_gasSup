import requests
import os
from dotenv import load_dotenv
import json

# Force reload environment variables
load_dotenv(override=True)

API_KEY = os.getenv("HELIUS_API_KEY")
WEBHOOK_URL = "https://736b-171-97-216-9.ngrok-free.app"
GAS_SUPPLIER_CONTRACT = "59L2oxymiQQ9Hvhh92nt8Y7nDYjsauFkdb3SybdnsG6"


def get_existing_webhooks():
    url = f"https://api.helius.xyz/v0/webhooks?api-key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(
            f"\nWarning: Could not fetch existing webhooks (Status: {response.status_code})"
        )
        return []  # Return empty list if we can't get webhooks

    try:
        webhooks = response.json()
        if isinstance(webhooks, list):
            print(f"\nFound {len(webhooks)} existing webhooks")
            return webhooks
        else:
            print("\nWarning: Unexpected response format from Helius API")
            return []

    except Exception as e:
        print(f"Error processing webhooks: {str(e)}")
        return []


def delete_webhook(webhook_id):
    url = f"https://api.helius.xyz/v0/webhooks/{webhook_id}?api-key={API_KEY}"
    response = requests.delete(url)
    print(f"Deleted webhook {webhook_id}: {response.status_code}")


def register_webhook():
    # Try to get existing webhooks, but continue even if it fails
    existing = get_existing_webhooks()

    if existing:  # Only try to delete if we successfully got existing webhooks
        for webhook in existing:
            if isinstance(webhook, dict) and webhook.get("webhookURL") == WEBHOOK_URL:
                print(
                    f"Deleting webhook {webhook['webhookID']} matching URL: {WEBHOOK_URL}"
                )
                delete_webhook(webhook["webhookID"])

    # Create new webhook
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
    print(
        f"Using API key: {API_KEY[:4]}...{API_KEY[-4:]}"
    )  # Show first/last 4 chars of API key
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Monitoring gas supplier contract: {GAS_SUPPLIER_CONTRACT}")

    status, response = register_webhook()

    if status:
        print("\nWebhook registration successful!")
    else:
        print("\nWebhook registration failed!")
