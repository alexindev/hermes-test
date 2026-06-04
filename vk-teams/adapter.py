"""
VK Teams platform adapter for Hermes Gateway.
Uses requests (not aiohttp) — required for corporate api.bki-okb.ru deployments.
Supports: text messages, file/image sending, chat routing by skill.
"""
import asyncio
import os
import threading
import time
import requests
from pathlib import Path

from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)
from gateway.config import Platform, PlatformConfig
from gateway.session import SessionSource


def _load_env():
    """Load .env from HERMES_HOME if vars not already in environment."""
    if os.getenv('VKTEAMS_BOT_TOKEN'):
        return
    hermes_home = Path(os.getenv('HERMES_HOME', '/opt/data'))
    env_path = hermes_home / '.env'
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path, override=False)
        except Exception:
            pass


def _get_chat_skill(chat_id: str) -> str | None:
    """Return skill name for a given chat_id from env vars.

    Reads VKTEAMS_CHAT_<sanitized_chat_id>_SKILL where sanitized means
    all non-alphanumeric characters replaced with underscores.
    Example: 107890@chat.agent -> VKTEAMS_CHAT_107890_chat_agent_SKILL
    """
    sanitized = ''.join(c if c.isalnum() else '_' for c in chat_id)
    return os.getenv(f'VKTEAMS_CHAT_{sanitized}_SKILL') or None


class VKTeamsAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform('vkteams'))
        extra = config.extra or {}
        self.token = os.getenv('VKTEAMS_BOT_TOKEN') or extra.get('token', '')
        self.base_url = (
            os.getenv('VKTEAMS_BASE_URL')
            or extra.get('base_url', 'https://api.icq.net/bot/v1')
        ).rstrip('/')
        self.bot_mention = (
            os.getenv('VKTEAMS_BOT_MENTION')
            or extra.get('bot_mention', '')
        )
        self.poll_time = int(os.getenv('VKTEAMS_POLL_TIME', '30'))
        self._last_event_id = 0
        self._poll_thread = None
        self._running = False

    # ── HTTP helpers ──────────────────────────────────────────────────────

    def _get(self, method, **params):
        params['token'] = self.token
        try:
            resp = requests.get(
                f'{self.base_url}/{method}',
                params=params,
                timeout=self.poll_time + 10,
            )
            return resp.json()
        except Exception as e:
            print(f'[VKTeams] GET {method} error: {e}')
            return {}

    def _post_text(self, chat_id, text, reply_msg_id=None):
        params = {'token': self.token, 'chatId': chat_id, 'text': text}
        if reply_msg_id:
            params['replyMsgId'] = reply_msg_id
        try:
            resp = requests.get(
                f'{self.base_url}/messages/sendText',
                params=params,
                timeout=10,
            )
            return resp.json()
        except Exception as e:
            print(f'[VKTeams] sendText error: {e}')
            return {}

    def _send_file(self, chat_id, file_path=None, file_id=None, caption=None, reply_msg_id=None):
        """Send a file to a chat.

        Two modes per VK Teams Bot API:
        - file_path: upload new file via POST /messages/sendFile (multipart/form-data)
        - file_id:   resend already uploaded file via GET /messages/sendFile

        Returns dict with keys: ok, msgId, fileId (only on upload).
        """
        params = {'token': self.token, 'chatId': chat_id}
        if caption:
            params['caption'] = caption
        if reply_msg_id:
            params['replyMsgId'] = reply_msg_id

        # ── Resend by fileId (cheap, no upload) ───────────────────────────
        if file_id:
            try:
                params['fileId'] = file_id
                resp = requests.get(
                    f'{self.base_url}/messages/sendFile',
                    params=params,
                    timeout=10,
                )
                data = resp.json()
                if data.get('ok'):
                    print(f'[VKTeams] sendFile(fileId) OK -> {chat_id}')
                else:
                    print(f'[VKTeams] sendFile(fileId) error: {data}')
                return data
            except Exception as e:
                print(f'[VKTeams] sendFile(fileId) exception: {e}')
                return {'ok': False, 'error': str(e)}

        # ── Upload new file ───────────────────────────────────────────────
        if not file_path:
            return {'ok': False, 'error': 'file_path or file_id required'}

        file_path = Path(file_path)
        if not file_path.exists():
            print(f'[VKTeams] sendFile: file not found: {file_path}')
            return {'ok': False, 'error': f'file not found: {file_path}'}

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f)}
                resp = requests.post(
                    f'{self.base_url}/messages/sendFile',
                    params=params,
                    files=files,
                    timeout=60,
                )
            data = resp.json()
            if data.get('ok'):
                print(f'[VKTeams] sendFile OK: {file_path.name} -> {chat_id} (fileId={data.get("fileId")})')
            else:
                print(f'[VKTeams] sendFile error: {data}')
            return data
        except Exception as e:
            print(f'[VKTeams] sendFile exception: {e}')
            return {'ok': False, 'error': str(e)}

    # ── Polling loop ──────────────────────────────────────────────────────

    def _poll_loop(self):
        print(f'[VKTeams] Polling started — {self.base_url}')
        while self._running:
            try:
                data = self._get(
                    'events/get',
                    lastEventId=self._last_event_id,
                    pollTime=self.poll_time,
                )
                for event in data.get('events', []):
                    event_id = event.get('eventId', 0)
                    if event_id > self._last_event_id:
                        self._last_event_id = event_id
                    self._dispatch(event)
            except Exception as e:
                print(f'[VKTeams] Poll error: {e}')
                time.sleep(5)

    def _dispatch(self, event):
        if event.get('type') != 'newMessage':
            return

        payload = event.get('payload', {})
        text = payload.get('text', '').strip()
        chat_id = payload.get('chat', {}).get('chatId', '')
        from_user = payload.get('from', {})
        user_id = from_user.get('userId', '')
        user_name = (
            from_user.get('firstName', '') + ' ' + from_user.get('lastName', '')
        ).strip() or None
        msg_id = payload.get('msgId', '')

        # ── Chat routing ──────────────────────────────────────────────────
        allowed_chats = os.getenv('VKTEAMS_ALLOWED_CHATS', '').strip()
        allowed_list = [c.strip() for c in allowed_chats.split(',')] if allowed_chats else []

        if allowed_list:
            if chat_id in allowed_list:
                # Allowed chat — respond to any message, no mention required
                if self.bot_mention:
                    text = text.replace(self.bot_mention, '').strip()
            else:
                # Not in allowed list — only respond if bot is mentioned
                if not self.bot_mention or self.bot_mention not in text:
                    return
                text = text.replace(self.bot_mention, '').strip()
        else:
            # No allowed_chats configured — require mention everywhere
            if not self.bot_mention or self.bot_mention not in text:
                return
            text = text.replace(self.bot_mention, '').strip()

        if not text:
            return

        # ── Skill routing by chat ─────────────────────────────────────────
        skill = _get_chat_skill(chat_id)

        source = SessionSource(
            platform=Platform('vkteams'),
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
        )
        msg_event = MessageEvent(
            text=text,
            message_type=MessageType.TEXT,
            source=source,
            raw_message=event,
            message_id=msg_id,
            reply_to_message_id=msg_id,
            auto_skill=skill,
        )
        asyncio.run_coroutine_threadsafe(
            self.handle_message(msg_event),
            self._loop,
        )

    # ── BasePlatformAdapter interface ─────────────────────────────────────

    async def connect(self) -> bool:
        self._loop = asyncio.get_event_loop()
        self._running = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True
        )
        self._poll_thread.start()
        self._mark_connected()
        print(f'[VKTeams] Connected — token {self.token[:10]}...')
        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
        self._mark_disconnected()
        print('[VKTeams] Disconnected')

    async def send_document(self, chat_id, file_path, caption=None, file_name=None, reply_to=None, metadata=None, **kwargs):
        """Override base fallback — actually upload file via VK Teams API."""
        result = self._send_file(
            chat_id,
            file_path=file_path,
            caption=caption,
            reply_msg_id=reply_to,
        )
        return SendResult(
            success=result.get('ok', False),
            message_id=str(result.get('msgId', '')),
        )

    async def send_image_file(self, chat_id, image_path, caption=None, reply_to=None, metadata=None, **kwargs):
        """Override base fallback — actually upload image via VK Teams API."""
        result = self._send_file(
            chat_id,
            file_path=image_path,
            caption=caption,
            reply_msg_id=reply_to,
        )
        return SendResult(
            success=result.get('ok', False),
            message_id=str(result.get('msgId', '')),
        )

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        """Send text or file to chat.

        If metadata contains 'file_path', uploads and sends as file.
        If metadata contains 'file_id', resends already uploaded file.
        Otherwise sends as plain text (chunked if needed).
        """
        file_path = None
        file_id = None
        if isinstance(metadata, dict):
            file_path = metadata.get('file_path')
            file_id = metadata.get('file_id')

        # ── File send ─────────────────────────────────────────────────────
        if file_path or file_id:
            caption = str(content) if content else None
            data = self._send_file(
                chat_id,
                file_path=file_path,
                file_id=file_id,
                caption=caption,
                reply_msg_id=reply_to,
            )
            return SendResult(
                success=data.get('ok', False),
                message_id=str(data.get('msgId', '')),
            )

        # ── Text send (chunked) ───────────────────────────────────────────
        max_len = 4000
        text = str(content)
        chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
        msg_id = None
        for chunk in chunks:
            data = self._post_text(chat_id, chunk, reply_msg_id=reply_to)
            if data.get('ok'):
                msg_id = data.get('msgId')
        return SendResult(success=bool(msg_id), message_id=str(msg_id or ''))

    async def get_chat_info(self, chat_id):
        return {'name': chat_id, 'type': 'group'}


# ── Plugin registration ───────────────────────────────────────────────────


def check_requirements() -> bool:
    _load_env()
    return bool(os.getenv('VKTEAMS_BOT_TOKEN'))


def validate_config(config) -> bool:
    _load_env()
    extra = getattr(config, 'extra', {}) or {}
    return bool(os.getenv('VKTEAMS_BOT_TOKEN') or extra.get('token'))


def _env_enablement() -> dict | None:
    _load_env()
    token = os.getenv('VKTEAMS_BOT_TOKEN', '').strip()
    base_url = os.getenv('VKTEAMS_BASE_URL', 'https://api.bki-okb.ru/bot/v1').strip()
    if not token:
        return None
    seed = {'token': token, 'base_url': base_url}
    home = os.getenv('VKTEAMS_HOME_CHANNEL', '').strip()
    if home:
        seed['home_channel'] = {'chat_id': home, 'name': 'Home'}
    mention = os.getenv('VKTEAMS_BOT_MENTION', '').strip()
    if mention:
        seed['bot_mention'] = mention
    return seed


def register(ctx):
    ctx.register_platform(
        name='vkteams',
        label='VK Teams',
        adapter_factory=lambda cfg: VKTeamsAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        required_env=['VKTEAMS_BOT_TOKEN'],
        install_hint='pip install requests  # already available',
        env_enablement_fn=_env_enablement,
        cron_deliver_env_var='VKTEAMS_HOME_CHANNEL',
        allowed_users_env='VKTEAMS_ALLOWED_USERS',
        allow_all_env='VKTEAMS_ALLOW_ALL_USERS',
        max_message_length=4000,
        platform_hint=(
            'You are chatting via VK Teams corporate messenger. '
            'Respond in the same language the user writes in. '
            'Keep responses concise and clear.'
        ),
        emoji='💬',
    )
