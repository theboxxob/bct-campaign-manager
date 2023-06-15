import subprocess
import logging
import json
import os
import csv
from pathlib import Path
from json import JSONDecodeError

logger = logging.getLogger(__name__)

class CrawlerResultError(Exception):
    """Exception for errors regarding results from crawler"""

class InvalidUIDError(Exception):
    """Exceptions for when given UID is incorrect e.g. negative, for example"""

def fetch_bitcointalk_profile(uid):
    """Use a subprocess to crawl bitcointalk profile using scrapy"""
    try:
        try:
            uid = int(uid)
        except ValueError as error:
            logger.error("Uid could not be casted to integer %s", error)
        if uid >= 0:
            subprocess.run(
                ["python3", "bitcointalk_scraper/profile_crawler.py", str(uid)], check=True)
        else:
            raise InvalidUIDError("UID cannot be negative")
    except subprocess.CalledProcessError as error:
        logger.error("Error when crawling bitcointalk profile: %s", error)
        raise
    print("Fetching user profile using scrapy...")
    profile_json_path = Path('scraper_outputs/profile.json')
    if profile_json_path.is_file():
        with profile_json_path.open('r') as f:
            try:
                profile_arr = json.load(f)
            except JSONDecodeError as error:
                print(
                    "File could not be loaded as JSON. There was likely no profile with given UID.")
                logger.error(error)
                raise
            if isinstance(profile_arr, list) and len(profile_arr) == 1:
                profile = profile_arr.pop()
                if isinstance(profile, dict) and profile.get('uid') == int(uid):
                    print(f"Profile with UID {uid} fetched")
                    return profile
                raise CrawlerResultError(
                    "Crawler result did not have a profile with expected UID")
            raise CrawlerResultError("Crawler result not an array containing a profile")
    else:
        raise FileNotFoundError(
            "File with profile information was not found. Scraping may have failed.")


def validate_data_folder(path_arg):
    """Check that given data folder exists and is writeble"""
    if path_arg:
        if path_arg.is_dir():
            if os.access(path_arg, os.W_OK):
                return
            raise PermissionError("Given path not writable")
    raise FileNotFoundError("Data folder path doesn't exist or path is not a folder")
