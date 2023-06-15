import unittest
from json import JSONDecodeError

from utils import fetch_bitcointalk_profile, InvalidUIDError

class TestUtils(unittest.TestCase):

    def test_fetch_bitcointalk_profile(self):
        satoshi_profile = fetch_bitcointalk_profile(3)    
        self.assertTrue(satoshi_profile.get('name') == 'satoshi')

    def test_negative_uid_bitcointalk_profile(self):
        with self.assertRaises(InvalidUIDError):
            fetch_bitcointalk_profile(-1)

    def test_nonexistent_bitcointalk_profile(self):
        with self.assertRaises(JSONDecodeError):
            fetch_bitcointalk_profile(57346864567435643875687563)

if __name__ == '__main__':
    unittest.main()
