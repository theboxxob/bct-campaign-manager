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

class ScrapingError(Exception):
    """Exception for errors that occur during scraping"""

class InvalidUIDError(Exception):
    """Exceptions for when given UID is incorrect e.g. negative"""

class InvalidTimestampError(Exception):
    """Exceptions for when given timestamp is incorrect e.g. doesn't represent an int"""

def try_uid_to_int(uid):
    """Convert UID string (representing int) and test validity"""
    try:
        uid = int(uid)
        if uid < 0:
            raise InvalidUIDError("UID cannot be negative")
        return uid
    except ValueError as error:
        raise InvalidUIDError("UID could not be converted to int") from error

def try_timestamp_to_int(timestamp):
    """Convert timestamp to an integer"""
    try:
        return int(timestamp)
    except ValueError as error:
        raise InvalidTimestampError("Timestamp could not be converted to int") from error

def scrape_profile(uid):
    try:
        uid = try_uid_to_int(uid)
        subprocess.run(
            ["python3", "bitcointalk_scraper/profile_crawler.py", str(uid)], check=True)
    except subprocess.CalledProcessError as error:
        logger.error("Error when scraping bitcointalk profile, uid: %s, error: %s", uid, error)
        raise ScrapingError("Something went wrong during Scraping") from error

def scrape_posts(uid, start_timestamp):
    try:
        uid = try_uid_to_int(uid)
        start_timestamp = try_timestamp_to_int(start_timestamp)
        subprocess.run(
            ["python3", "bitcointalk_scraper/posts_crawler.py",
                str(uid), str(start_timestamp)], check=True)
    except subprocess.CalledProcessError as error:
        logger.error(
            "Error when scraping bitcointalk user posts, uid: %s, timestamp: %s, error: %s",
            uid, start_timestamp, error)
        raise ScrapingError("Something went wrong during Scraping") from error

def fetch_bitcointalk_profile(uid):
    """Use a subprocess to crawl bitcointalk profile using scrapy"""
    try:
        print("Fetching user profile using scrapy...")
        scrape_profile(uid)
    except InvalidUIDError as error:
        logger.error("Problem with UID when fetching profile: %s", error)
        raise
    except ScrapingError as error:
        logger.error(error)
        raise
    profile_json_path = Path('scraper_outputs/profile.json')
    if profile_json_path.is_file():
        with profile_json_path.open('r') as f:
            file_contents = f.read()
            if not file_contents:
                return None
            profile_arr = json.loads(file_contents)
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


def fetch_user_posts(uid, start_timestamp):
    """Use a subprocess to crawl bitcointalk user posts that were made after a certain
    point in time (start_timestamp)"""
    try:
        print(f"Fetching posts for user {uid} that were made after {start_timestamp}")
        scrape_posts(uid, start_timestamp)
    except InvalidUIDError as error:
        logger.error("Invalid UID %s", error)
        raise
    except InvalidTimestampError as error:
        logger.error("Invalid timestamp %s", error)
        raise
    except ScrapingError as error:
        logger.error(error)
        raise
    posts_json_path = Path('scraper_outputs/posts.json')
    if posts_json_path.is_file():
        with posts_json_path.open('r') as f:
            try:
                file_contents = f.read()
                if not file_contents:
                    return []
                posts_arr = json.loads(file_contents)
            except JSONDecodeError as error:
                logger.error(error)
                raise
            if isinstance(posts_arr, list):
                result = []
                for post in posts_arr:
                    result.append({
                        'datetime_utc': post.get('datetime_utc'),
                        'link': post.get('link')
                    })
                return result
            raise CrawlerResultError("Crawler reult not an array containing posts")
    else:
        raise FileNotFoundError("File with posts was not found. Scraping may have failed.")


def validate_data_folder(path_arg):
    """Check that given data folder exists and is writeble"""
    if path_arg:
        if path_arg.is_dir():
            if os.access(path_arg, os.W_OK):
                return
            raise PermissionError("Given path not writable")
    raise FileNotFoundError("Data folder path doesn't exist or path is not a folder")
