import unittest
import subprocess
import json
import shutil
from pathlib import Path

def add_campaign():
    subprocess.run(
        ["python3", "main.py", "campaign", "add", "test_campaign"], check=True
    )

def add_participant():
    subprocess.run(
        ["python3", "main.py", "campaign", "add_participant", "test_campaign", "3"], check=True
    )

def remove_participant():
    subprocess.run(
        ["python3", "main.py", "campaign", "remove_participant", "test_campaign", "3"], check=True
    )

def get_metadata(p):
    with p.open('r') as f:
        return json.load(f)

class CampaignTestCase(unittest.TestCase):

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
        add_campaign()
        self.assertTrue(self.campaign_path.is_dir())
        self.assertTrue(self.metadata_path.is_file())
        metadata = get_metadata(self.metadata_path)
        self.assertTrue(metadata.get('campaign_name') == 'test_campaign')

    def test_add_participant(self):
        add_campaign()
        add_participant()
        metadata = get_metadata(self.metadata_path)
        self.assertTrue(metadata.get('participants').get('3') == 'satoshi')

    def test_remove_participant(self):
        add_campaign()
        add_participant()
        remove_participant()
        metadata = get_metadata(self.metadata_path)
        self.assertEqual(None, metadata.get('participants').get('3'))
