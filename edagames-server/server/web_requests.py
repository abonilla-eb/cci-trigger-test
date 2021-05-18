import requests

import server.web_urls as web_urls


async def notify_end_game_to_web(game_id, data):
    requests.post(
        web_urls.GAME_URL,
        json=({
            'game_id': game_id,
            'data': data,
        })
    )
