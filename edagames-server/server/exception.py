from server.constants import GAMEIDERROR


class GameIdException(Exception):
    code = GAMEIDERROR
    message = 'Game_id not found'

    def __str__(self):
        return '{code} - {message}'.format(
            code=self.code,
            message=self.message
        )
