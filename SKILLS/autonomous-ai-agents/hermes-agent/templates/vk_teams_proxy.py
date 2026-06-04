#!/usr/bin/env python3
"""
VK Teams Bot Proxy for Hermes Agent.

Connects VK Teams Bot API to Hermes API Server (OpenAI-compatible endpoint).
Uses long-polling for incoming messages and forwards them to Hermes.

Usage:
    python vk_teams_proxy.py --bot-token <token> --base-url <url> --hermes-url <url>
"""

import asyncio
import json
import logging
import sys
import time
import argparse
import aiohttp
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vk_teams_proxy")

# ── Configuration ────────────────────────────────────────────────────────────

BOT_TOKEN = "001.0878497284.4267979501:1000000100"
BASE_URL = "https://api.bki-okb.ru/bot/v1"
CHAT_ID = "107411@chat.agent"
HERMES_URL = "http://127.0.0.1:8642/v1/chat/completions"
POLL_TIME = 5  # seconds for long-poll wait
CONNECT_TIMEOUT = 30  # seconds
RETRY_DELAY = 3  # seconds on error
MAX_RETRIES = 10  # max consecutive retries before giving up


class VKTProxy:
    def __init__(
        self,
        bot_token: str,
        base_url: str,
        chat_id: str,
        hermes_url: str,
        poll_time: int = POLL_TIME,
    ):
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")
        self.chat_id = chat_id
        self.hermes_url = hermes_url
        self.poll_time = poll_time
        self.last_event_id = 0
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False

    # ── VK Teams API helpers ───────────────────────────────────────────────

    async def _get(self, path: str, params: dict | None = None) -> dict:
        """GET request to VK Teams API."""
        url = f"{self.base_url}{path}"
        params = params or {}
        params["token"] = self.bot_token
        async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=CONNECT_TIMEOUT)) as resp:
            data = await resp.json()
            if data.get("error"):
                raise ValueError(f"VK Teams API error: {data['error']}")
            return data

    async def _post(self, path: str, body: dict) -> dict:
        """POST request to VK Teams API."""
        url = f"{self.base_url}{path}"
        form = aiohttp.FormData()
        form.add_field("token", self.bot_token)
        for k, v in body.items():
            if isinstance(v, (list, dict)):
                form.add_field(k, json.dumps(v))
            else:
                form.add_field(k, str(v))
        async with self.session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=CONNECT_TIMEOUT)) as resp:
            data = await resp.json()
            if data.get("error"):
                raise ValueError(f"VK Teams API error: {data['error']}")
            return data

    async def send_message(self, text: str, reply_msg_id: Optional[int] = None) -> dict:
        """Send a text message via VK Teams API."""
        body = {"chatId": self.chat_id, "text": text}
        if reply_msg_id:
            body["replyMsgId"] = [reply_msg_id]
        log.info(f"Sending message to {self.chat_id}: {text[:100]}...")
        return await self._post("/messages/sendText", body)

    async def get_events(self) -> list:
        """Poll for new events via long-polling."""
        params = {
            "lastEventId": self.last_event_id,
            "pollTime": self.poll_time,
        }
        return await self._get("/events/get", params)

    # ── Hermes API helper ──────────────────────────────────────────────────

    async def ask_hermes(self, user_message: str, user_id: str) -> str:
        """Send message to Hermes and get response."""
        payload = {
            "model": "hermes-agent",
            "messages": [
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "metadata": {
                "source": "vk_teams",
                "user_id": user_id,
            },
        }
        headers = {"Content-Type": "application/json"}
        async with self.session.post(
            self.hermes_url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                raise RuntimeError(f"Hermes API error {resp.status}: {err_text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Event processing ───────────────────────────────────────────────────

    def process_event(self, event: dict):
        """Parse a VK Teams event and extract message info."""
        event_type = event.get("type", "")
        log.debug(f"Event type: {event_type}")

        if event_type == "message":
            msg = event.get("object", {})
            return {
                "type": "message",
                "msg_id": msg.get("id"),
                "user_id": msg.get("fromId"),
                "text": msg.get("text", ""),
                "chat_id": msg.get("chatId"),
            }
        elif event_type == "new_chat_member":
            return {
                "type": "member_joined",
                "user_id": event.get("object", {}).get("userId"),
                "chat_id": event.get("object", {}).get("chatId"),
            }
        elif event_type == "user_typing":
            return {
                "type": "typing",
                "user_id": event.get("object", {}).get("userId"),
                "chat_id": event.get("object", {}).get("chatId"),
            }
        else:
            return {"type": "unknown", "raw": event}

    async def handle_message(self, parsed: dict):
        """Process a single message event."""
        if parsed["type"] != "message":
            return

        user_text = parsed.get("text", "").strip()
        user_id = parsed.get("user_id", "unknown")
        msg_id = parsed.get("msg_id")

        if not user_text:
            return

        log.info(f"Message from {user_id}: {user_text[:80]}...")

        try:
            response = await self.ask_hermes(user_text, user_id)
            await self.send_message(response, reply_msg_id=msg_id)
        except Exception as e:
            error_msg = f"Ошибка при обработке запроса: {str(e)}"
            log.error(error_msg)
            await self.send_message(error_msg, reply_msg_id=msg_id)

    # ── Main loop ──────────────────────────────────────────────────────────

    async def run(self):
        """Main polling loop."""
        self.running = True
        log.info(f"Starting VK Teams proxy")
        log.info(f"  Bot token: {self.bot_token[:10]}...{self.bot_token[-4:]}")
        log.info(f"  Base URL: {self.base_url}")
        log.info(f"  Chat ID: {self.chat_id}")
        log.info(f"  Hermes URL: {self.hermes_url}")
        log.info(f"  Poll time: {self.poll_time}s")

        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)

        retry_count = 0

        try:
            while self.running:
                try:
                    events_data = await self.get_events()
                    events = events_data.get("events", [])

                    if events:
                        retry_count = 0
                        log.info(f"Received {len(events)} event(s)")

                    for event in events:
                        parsed = self.process_event(event)
                        if parsed.get("type") == "message":
                            await self.handle_message(parsed)

                    # Update lastEventId
                    if events:
                        max_id = max(e.get("id", 0) for e in events)
                        if max_id > self.last_event_id:
                            self.last_event_id = max_id

                except aiohttp.ClientError as e:
                    retry_count += 1
                    log.error(f"Network error (attempt {retry_count}/{MAX_RETRIES}): {e}")
                    if retry_count >= MAX_RETRIES:
                        log.error("Max retries reached. Restarting proxy.")
                        break
                    await asyncio.sleep(RETRY_DELAY)

                except Exception as e:
                    retry_count += 1
                    log.error(f"Unexpected error (attempt {retry_count}/{MAX_RETRIES}): {e}")
                    if retry_count >= MAX_RETRIES:
                        log.error("Max retries reached. Restarting proxy.")
                        break
                    await asyncio.sleep(RETRY_DELAY)

        finally:
            if self.session:
                await self.session.close()
            self.running = False
            log.info("VK Teams proxy stopped")

    async def stop(self):
        """Stop the proxy."""
        self.running = False


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VK Teams Bot Proxy for Hermes Agent")
    parser.add_argument("--bot-token", default=BOT_TOKEN, help="Bot token")
    parser.add_argument("--base-url", default=BASE_URL, help="VK Teams API base URL")
    parser.add_argument("--chat-id", default=CHAT_ID, help="Chat ID for messages")
    parser.add_argument("--hermes-url", default=HERMES_URL, help="Hermes API URL")
    parser.add_argument("--poll-time", type=int, default=POLL_TIME, help="Long-poll wait time (seconds)")
    args = parser.parse_args()

    proxy = VKTProxy(
        bot_token=args.bot_token,
        base_url=args.base_url,
        chat_id=args.chat_id,
        hermes_url=args.hermes_url,
        poll_time=args.poll_time,
    )

    try:
        asyncio.run(proxy.run())
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        asyncio.run(proxy.stop())


if __name__ == "__main__":
    main()
