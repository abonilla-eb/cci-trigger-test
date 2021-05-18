import server.constants as websocket_events
from server.connection_manager import manager
from typing import Dict, List


async def notify_challenge_to_client(
    client: str,
    opponent: str,
    challenge_id: str,
):
    await manager.send(
        client,
        websocket_events.EVENT_SEND_CHALLENGE,
        {
            'opponent': opponent,
            'challenge_id': challenge_id,
        },
    )


async def notify_error_to_client(client: str, error: str):
    await manager.send(
        client,
        websocket_events.EVENT_SEND_ERROR,
        {
            'Error': error,
        },
    )


async def notify_your_turn(client: str, data: Dict):
    await manager.send(
        client,
        websocket_events.EVENT_SEND_YOUR_TURN,
        data,
    )


async def notify_user_list_to_client(client: str, users: List[str]):
    await manager.send(
        client,
        websocket_events.EVENT_LIST_USERS,
        {
            'users': users,
        },
    )


async def notify_end_game_to_client(players: List[str], data: Dict):
    for client in players:
        await manager.send(
            client,
            websocket_events.EVENT_GAME_OVER,
            data,
        )


async def notify_feedback(client, feedback):
    await manager.send(
        client,
        websocket_events.EVENT_FEEDBACK,
        feedback,
    )
