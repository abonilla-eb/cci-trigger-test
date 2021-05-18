import json
import redis
from redis.exceptions import DataError
from uvicorn.config import logger

from .environment import REDIS_HOST, REDIS_LOCAL_PORT
from server.websockets import (
    notify_error_to_client,
    notify_feedback,
)

from typing import Dict


r = redis.Redis(host=REDIS_HOST, port=REDIS_LOCAL_PORT, db=0, charset="utf-8", decode_responses=True)


def append_to_stream(key: str, data: Dict):
    try:
        parsed_data = {k: json.dumps(v) if type(v) == dict else v for k, v in data.items()}
        r.xadd(key, parsed_data)
    except TypeError as e:
        logger.error(f'Error while parsing data: {e}')
    except redis.RedisError as e:
        logger.error(f'Error while writing stream to Redis: {e}')


def save_string(key, value, expire=None):
    try:
        r.set(key, value, ex=expire)
    except DataError as e:
        logger.error(e)


async def get_string(key, client, caller='id'):
    try:
        data = r.get(key)
        if data is None:
            await notify_feedback(
                client,
                f'{caller} not found',
            )
        return data
    except DataError as e:
        logger.error(e)
        await notify_error_to_client(
            client,
            f'DataError in {caller}, send a str',
        )
