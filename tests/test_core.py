import unittest
import subprocess
import json
import shutil
from pathlib import Path

from core import add_campaign, add_participant, remove_participant

class Namespace:
    """Class to mimic argparse namespace"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_metadata(p):
    """Load the file containing campaign metadata as JSON and return it"""
    with p.open('r') as f:
        return json.load(f)


class CampaignTestCase(unittest.TestCase):
    """Tests campaign related commands"""
    def setUp(self):
        self.campaign_path = Path('campaigns/test_campaign')
        self.metadata_path = self.campaign_path / 'metadata.json'
        if self.campaign_path.is_dir():
            self.fail(
                "test_campaign already exists... aborting incase it contains something important")

    def tearDown(self):
        if self.campaign_path.is_dir():
            shutil.rmtree(self.campaign_path)

    def test_add_campaign(self):
        """Test adding campaign"""
        ns = Namespace(campaign_name='test_campaign', data_folder=None)
        add_campaign(ns)
        self.assertTrue(self.campaign_path.is_dir())
        self.assertTrue(self.metadata_path.is_file())
        metadata = get_metadata(self.metadata_path)
        self.assertTrue(metadata.get('campaign_name') == 'test_campaign')

    def test_add_participant(self):
        """Test adding participant to campaign"""
        ns = Namespace(campaign_name='test_campaign', uid=3, data_folder=None)
        add_campaign(ns)
        add_participant(ns)
        metadata = get_metadata(self.metadata_path)
        self.assertTrue(metadata.get('participants').get('3') == 'satoshi')

    def test_remove_participant(self):
        """Test removing participant from campaign"""
        ns = Namespace(campaign_name='test_campaign', uid=3, data_folder=None)
        add_campaign(ns)
        add_participant(ns)
        remove_participant(ns)
        metadata = get_metadata(self.metadata_path)
        self.assertEqual(None, metadata.get('participants').get('3'))
