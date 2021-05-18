import asyncio
from fastapi import WebSocket
import json
import jwt
from uvicorn.config import logger

import server.constants as websocket_events
from .environment import JWT_TOKEN_KEY

from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        self.connections = {}

    async def connect(self, websocket: WebSocket, token: str):
        encoded_token = token.encode()
        try:
            user_to_connect = jwt.decode(
                encoded_token,
                JWT_TOKEN_KEY,
                algorithms=["HS256"],
            )
        except jwt.exceptions.InvalidTokenError:
            await websocket.close()
            return
        await websocket.accept()
        client = user_to_connect.get('user')
        self.connections[client] = websocket
        await self.notify_user_list_changed()
        return client

    async def broadcast(self, event: str, data: Dict):
        await self.bulk_send(self.connections.keys(), event, data)

    async def bulk_send(self, clients: List[str], event: str, data: Dict):
        for client in clients:
            asyncio.create_task(self._send(
                self.connections.get(client),
                event,
                data,
            ))

    async def send(self, client: str, event: str, data: Dict):
        await self._send(
            self.connections.get(client),
            event,
            data,
        )

    async def _send(self, client_ws: WebSocket, event: str, data: Dict):
        logger.info(f'[Websocket] Send: Event: {event}, data: {data}')
        try:
            await client_ws.send_text(json.dumps({
                'event': event,
                'data': data,
            }))
        except Exception as e:
            logger.info(str(e))

    async def remove_user(self, user):
        try:
            del self.connections[user]
            await self.notify_user_list_changed()
        except KeyError as e:
            logger.info('[Websocket]exception {}'.format(e))

    async def notify_user_list_changed(self):
        logger.info('[Websocket]Users {}'.format(list(self.connections.keys())))
        await self.broadcast(
            websocket_events.EVENT_LIST_USERS,
            {
                'users': list(self.connections.keys()),
            },
        )


manager = ConnectionManager()
