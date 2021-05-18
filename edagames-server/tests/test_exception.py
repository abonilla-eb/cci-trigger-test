import unittest
from server.exception import GameIdException


class TestException(unittest.TestCase):

    def test_exception(self):
        self.assertEqual(str(GameIdException()), 'GAMEID_ERROR - Game_id not found')
