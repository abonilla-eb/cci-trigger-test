import json
from typing import Dict

from server.connection_manager import manager
from server.websockets import (
    notify_user_list_to_client,
)
from server.grpc_adapter import GRPCAdapterFactory
from server.utilities_server_event import ServerEvent, make_challenge
from server.redis import save_string, get_string

from server.constants import (
    LIST_USERS,  # name_event
    ASK_CHALLENGE,
    ACCEPT_CHALLENGE,
    MOVEMENTS,
    ABORT_GAME,
    PREFIX_CHALLENGE,  # prefix
    PREFIX_GAME,
    PREFIX_TURN_TOKEN,
    PREFIX_LOG,
    CHALLENGE_ID,
    BOARD_ID,  # search in request
    TURN_TOKEN,
    OPPONENT,
    EMPTY_PLAYER,  # game_over
    GAME_NAME,  # dict.get values
    PLAYERS,
)


class ListUsers(ServerEvent):
    def __init__(self, response, client):
        super().__init__(response, client)
        self.name_event = LIST_USERS

    async def run(self):
        users = list(manager.connections.keys())
        await notify_user_list_to_client(self.client, users)


class Challenge(ServerEvent):
    def __init__(self, response, client):
        super().__init__(response, client)
        self.name_event = ASK_CHALLENGE

    async def run(self):
        challenged = await self.search_value(OPPONENT)
        await make_challenge([self.client, challenged])


class AcceptChallenge(ServerEvent):
    def __init__(self, response, client):
        super().__init__(response, client)
        self.name_event = ACCEPT_CHALLENGE

    async def run(self):
        challenge_id = await self.search_value(CHALLENGE_ID)
        if challenge_id is not None:
            game_data = await get_string(
                f'{PREFIX_CHALLENGE}{challenge_id}',
                self.client,
                CHALLENGE_ID,
            )
            if game_data is not None:
                await self.start_game(json.loads(game_data))

    async def start_game(self, game_data: Dict):
        adapter = await GRPCAdapterFactory.get_adapter(game_data.get(GAME_NAME))
        data_received = await adapter.create_game(game_data.get(PLAYERS))
        save_string(
            f'{PREFIX_GAME}{data_received.game_id}',
            json.dumps(game_data),
        )
        await self.move(data_received, game_data.get(GAME_NAME))


class Movements(ServerEvent):
    def __init__(self, response, client):
        super().__init__(response, client)
        self.name_event = MOVEMENTS

    async def run(self):
        turn_token = await self.search_value(TURN_TOKEN)
        game_id = await self.search_value(BOARD_ID)
        redis_game_id = await get_string(
            f'{PREFIX_TURN_TOKEN}{game_id}',
            self.client,
            TURN_TOKEN,
        )
        if redis_game_id == turn_token:
            game = await get_string(
                f'{PREFIX_GAME}{game_id}',
                self.client,
                BOARD_ID,
            )
            if game is not None:
                await self.execute_action(json.loads(game), game_id)

    async def execute_action(self, game_data: dict, game_id: str):
        adapter = await GRPCAdapterFactory.get_adapter(game_data.get(GAME_NAME))
        data_received = await adapter.execute_action(
            game_id,
            self.response
        )
        await self.log_action(data_received)
        if data_received.current_player == EMPTY_PLAYER:
            await self.game_over(data_received, game_data)
        else:
            await self.move(data_received, game_data.get(GAME_NAME))

    async def log_action(self, data):
        save_string(
            f'{PREFIX_LOG}{data.game_id}',
            json.dumps({
                "turn": data.current_player,
                "data": data.play_data,
            })
        )


class AbortGame(ServerEvent):
    def __init__(self, response, client):
        super().__init__(response, client)
        self.name_event = ABORT_GAME

    async def run(self):
        turn_token_received = await self.search_value(TURN_TOKEN)
        game_id = await self.search_value(BOARD_ID)
        turn_token_saved = await get_string(
            f'{PREFIX_TURN_TOKEN}{game_id}',
            self.client,
            TURN_TOKEN,
        )
        if turn_token_received == turn_token_saved:
            game = await get_string(
                f'{PREFIX_LOG}{game_id}',
                self.client,
                BOARD_ID,
            )
            if game is not None:
                await self.end_game(json.loads(game), game_id)

    async def end_game(self, game: dict, game_id: str):
        adapter = await GRPCAdapterFactory.get_adapter(game.get(GAME_NAME))
        data_received = await adapter.end_game(game_id)
        await self.game_over(data_received, game)
