import unittest
import time
from json import JSONDecodeError
from datetime import timedelta

from utils import fetch_bitcointalk_profile, fetch_user_posts, InvalidUIDError

class TestUtils(unittest.TestCase):

    def test_fetch_bitcointalk_profile(self):
        satoshi_profile = fetch_bitcointalk_profile(3)    
        self.assertTrue(satoshi_profile.get('name') == 'satoshi')

    def test_negative_uid_bitcointalk_profile(self):
        with self.assertRaises(InvalidUIDError):
            fetch_bitcointalk_profile(-1)

    def test_nonexistent_bitcointalk_profile(self):
        self.assertEqual(None, fetch_bitcointalk_profile(57346864567435643875687563))

    def test_fetch_posts(self):
        week = timedelta(days=7)
        now_minus_week = time.time() - week.total_seconds()
        posts = fetch_user_posts(459836, int(now_minus_week))
        self.assertTrue(isinstance(posts, list))

if __name__ == '__main__':
    unittest.main()
