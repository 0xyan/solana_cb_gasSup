from fastapi import FastAPI, Request
import logging
from datetime import datetime
import uvicorn
from acc_list import TRACKED_TOKENS
from dotenv import load_dotenv
import requests
import os

load_dotenv(override=True)

contract = "59L2oxymiQQ9Hvhh92nt8Y7nDYjsauFkdb3SybdnsG6h"

logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[logging.FileHandler("token_transfers.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
app = FastAPI()

processed_txs = {}


# Add Telegram sending function
def send_telegram_message(message):
    token_tg = os.getenv("TELEGRAM_TOKEN")
    id_tg = os.getenv("TELEGRAM_ID")

    url = f"https://api.telegram.org/bot{token_tg}/sendMessage"
    params = {
        "chat_id": id_tg,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")


async def check_wallet_tokens(wallet_address):
    """Check if wallet holds any tokens from our tracking list"""
    try:
        helius_url = (
            f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
        )

        payload = {
            "jsonrpc": "2.0",
            "id": "my-id",
            "method": "getAssetsByOwner",
            "params": {"ownerAddress": wallet_address, "page": 1, "limit": 1000},
        }

        response = requests.post(
            helius_url, headers={"Content-Type": "application/json"}, json=payload
        )

        data = response.json()

        if "result" in data:
            assets = data["result"]["items"]
            for asset in assets:
                if asset["id"] in TRACKED_TOKENS:
                    return (
                        True,
                        TRACKED_TOKENS[asset["id"]],
                    )  # Return tuple (True, token_name)

        return False, None

    except Exception as e:
        logger.error(f"Error checking wallet tokens: {str(e)}")
        return False, None


@app.post("/")
async def webhook(request: Request):
    try:
        data = await request.json()

        if isinstance(data, list):
            for event in data:
                await process_event(event)
        else:
            await process_event(data)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


async def process_event(event):
    try:
        if not event.get("nativeTransfers"):
            return

        tx_signature = event.get("signature")
        if tx_signature in processed_txs:
            return

        processed_txs[tx_signature] = datetime.now()

        for transfer in event["nativeTransfers"]:
            from_address = transfer.get("fromUserAccount")

            if from_address != contract:
                continue

            to_address = transfer.get("toUserAccount")

            # Now we get both the boolean and token name
            has_tracked_tokens, token_name = await check_wallet_tokens(to_address)

            if has_tracked_tokens:
                transfer_info = (
                    f"\n{'='*50}\n"
                    f"NEW WALLET WITH TRACKED TOKEN DETECTED!\n"
                    f"Token Found: {token_name}\n"
                    f"Wallet: {to_address}\n"
                    f"Transaction: {tx_signature}\n"
                    f"Timestamp: {datetime.now()}\n"
                    f"{'='*50}"
                )

                logger.warning(transfer_info)

                message = (
                    f"🔍 <b>Tracked Token Found by Gas Supplier!</b>\n\n"
                    f"Token: <b>{token_name}</b>\n"
                    f"Wallet: <code>{to_address}</code>\n"
                    f"<a href='https://solscan.io/tx/{tx_signature}'>View Transaction</a>"
                )

                send_telegram_message(message)

    except Exception as e:
        logger.error(f"Error in process_event: {str(e)}", exc_info=True)


@app.get("/")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Server starting on port 8000...")
    print(f"Monitoring outgoing transfers from gas supplier: {contract}")
    print(f"Tracking tokens: {list(TRACKED_TOKENS.values())}")
    uvicorn.run(app, host="0.0.0.0", port=8004)
