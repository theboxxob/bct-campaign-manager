import json
import logging
import os
import time
import csv

from pathlib import Path
from datetime import datetime

from utils import validate_data_folder, fetch_bitcointalk_profile, fetch_user_posts, CrawlerResultError

logger = logging.getLogger(__name__)

PARTICIPANTS_KEY = 'participants'
CAMPAIGN_NAME_KEY = 'campaign_name'
UID_KEY = 'uid'
PAYMENT_ADDRESS_KEY = 'payment_address'

class MetadataError(Exception):
    """Represents errors regarding metadata of campaigns or rounds"""


class NoSuchRoundError(Exception):
    """Represent error that occurs when a round doesn't exist
    and program may misbehave if exception not raised"""


def read_metadata(data_folder, campaign_name):
    """Reads campaign metadata from the metadata.json
    file in the campaign folder."""
    metadata_path = campaign_metadata_path(data_folder, campaign_name)
    with metadata_path.open('r') as f:
        try:
            metadata = json.load(f)
            if (isinstance(metadata, dict) and
                CAMPAIGN_NAME_KEY in metadata and
                    metadata.get(CAMPAIGN_NAME_KEY) == campaign_name):
                return metadata
            raise MetadataError("Campaign metadata file contains incorrect data")
        except json.JSONDecodeError as error:
            logger.error("Error loading metadata as JSON %s", error)
            raise


def write_metadata(data_folder, campaign_name, json_string):
    """Write campaign metadata to the metadata.json file at campaign folder"""
    metadata_path = campaign_metadata_path(data_folder, campaign_name)
    with metadata_path.open('w') as f:
        print(f"Writing campaign {campaign_name} data to file...")
        f.write(json_string)
        print("Campaign data written to file")


def read_round_data(campaign_path, round_number):
    """Read round information from the round.json file at round folder"""
    round_path = round_metadata_path(campaign_path, round_number)
    with round_path.open('r') as f:
        try:
            round_dict = json.load(f)
            if (isinstance(round_dict, dict) and
                'round_number' in round_dict and
                    round_dict.get('round_number') == round_number):
                return round_dict
            raise MetadataError("Round metadata file contains incorrect data")
        except json.JSONDecodeError as error:
            logger.error("Error loading round as JSON %s", error)
            raise


def write_round_data(campaign_path, round_number, json_string):
    """Write round data to the round.json file at round folder"""
    round_path = round_metadata_path(campaign_path, round_number)
    with round_path.open('w') as f:
        print(f"Writing round {round_number} data to file...")
        f.write(json_string)
        print("Round data written to file")


def data_folder_path(path_arg):
    """Get path of data folder given commandline arg with may be None"""
    if path_arg:
        try:
            validate_data_folder(path_arg)
            return path_arg
        except (PermissionError, FileNotFoundError) as error:
            logger.error(error)
            raise
    path = Path('./campaigns')
    if not path.exists():
        os.makedirs(Path('./campaigns'))
    validate_data_folder(path)
    return path


def campaign_folder_path(path, campaign_name):
    """Get Path of campaign with given path and campaign name"""
    if campaign_exists(path, campaign_name):
        return path / campaign_name
    raise FileNotFoundError("The folder for campaign was not found.")


def campaign_metadata_path(path, campaign_name):
    """Get path of campaign metadata file if it exists"""
    campaign_path = path / campaign_name
    if campaign_path.exists():
        return campaign_path / 'metadata.json'
    raise FileNotFoundError("The folder for campaign was not found.")


def round_folder_path(campaign_path, round_number):
    """Return path of round if round exists"""
    round_path = campaign_path / str(round_number)
    if round_path.is_dir():
        return round_path
    raise FileNotFoundError("The folder for the round was not found.")


def round_metadata_path(campaign_path, round_number):
    """Get path of campaign metadata file if it exists"""
    round_folder = campaign_path / str(round_number)
    if round_folder.exists():
        return round_folder / 'round.json'
    raise FileNotFoundError("The folder for round was not found.")


def campaign_exists(path, campaign_name):
    """Check that campaign with given path and campaign name exists"""
    return (path / campaign_name).is_dir()


def campaign_has_participants(path, campaign_name):
    """Check if campaign metadata file has the participants key"""
    campaign_metadata = read_metadata(path, campaign_name)
    if PARTICIPANTS_KEY in campaign_metadata:
        if isinstance(campaign_metadata.get(PARTICIPANTS_KEY), dict):
            return True
        raise MetadataError('Campaign metadata participants item not a dict')
    return False


def campaign_participants(path, campaign_name):
    """Returns campaign participant ids from metadata"""
    try:
        metadata_file = campaign_metadata_path(path, campaign_name)
        with metadata_file.open() as f:
            metadata = json.load(f)
            if campaign_has_participants(path, campaign_name):
                return metadata.get(PARTICIPANTS_KEY)
            return {}
    except FileNotFoundError as error:
        logger.error(error)


def round_exists(campaign_path, round_number):
    """Check that round with given path and round number exists"""
    return (campaign_path / str(round_number)).is_dir()


def round_has_ended(campaign_path, round_number):
    """Check if a round has ended or not"""
    if round_exists(campaign_path, round_number):
        round_dict = read_round_data(campaign_path, round_number)
        if (ended := round_dict.get('ended')) is not None:
            return ended
        raise MetadataError("Round did not have 'ended' attribute for some reason")
    raise NoSuchRoundError


def round_has_participants(campaign_path, round_number):
    """Check if round has any participants
    e.g. if campaign had any participants when round was created"""
    round_metadata = read_round_data(campaign_path, round_number)
    if PARTICIPANTS_KEY in round_metadata:
        if isinstance(round_metadata.get(PARTICIPANTS_KEY), dict):
            return True
        raise MetadataError('Round metadata participants item is not a dict')
    return False


def round_participant_ids(campaign_path, round_number):
    """Returns round participant ids from metadata"""
    try:
        metadata_file = round_metadata_path(campaign_path, round_number)
        with metadata_file.open() as f:
            metadata = json.load(f)
            if round_has_participants(campaign_path, round_number):
                return metadata.get(PARTICIPANTS_KEY).keys()
            return []
    except FileNotFoundError as error:
        logger.error(error)


def set_current_round(data_folder, campaign_name, current_round):
    """Set current round to campaign metadata"""
    metadata = read_metadata(data_folder, campaign_name)
    metadata['current_round'] = current_round
    write_metadata(data_folder, campaign_name, json.dumps(metadata))


def initialize_round_participants(data_folder, campaign_name, start_time, known_start_info):
    """Get participants from campaign metadata and add them to the round
    as participants"""
    if campaign_has_participants(data_folder, campaign_name):
        participants = campaign_participants(data_folder, campaign_name)
        results = {}
        for participant in participants.values():
            uid = participant.get(UID_KEY)
            payment_address = participant.get(PAYMENT_ADDRESS_KEY)
            results[uid] = fill_round_participant_info(
                uid, payment_address, start_time, known_start_info)
        return results
    return {}


def fill_round_participant_info(profile_id, payment_address, start_time, known_start_info):
    profile = fetch_bitcointalk_profile(profile_id)
    return {
        UID_KEY: profile.get(UID_KEY),
        'name': profile.get('name'),
        'rank': profile.get('rank'),
        PAYMENT_ADDRESS_KEY: payment_address,
        'start_time': start_time,
        'known_start_info': known_start_info,
        'start_post_count': profile.get('post_count') if known_start_info else 'unknown',
        'start_activity': profile.get('activity') if known_start_info else 'unknown',
        'start_merit': profile.get('merit') if known_start_info else 'unknown',
    }


def finalize_round_participants(participants):
    """Go through each participant in the round and update info and
    calculate difference from start"""
    profiles = map(fetch_bitcointalk_profile, participants.keys())
    for profile in profiles:
        uid = str(profile.get(UID_KEY))
        round_participant = participants.get(uid)
        known_start_info = round_participant.get('known_start_info')
        posts = fetch_user_posts(uid, round_participant.get('start_time'))
        print(f"Calculating posts for {profile.get('name')}...")
        participants[uid]['end_post_count'] = profile.get('post_count')
        participants[uid]['end_activity'] = profile.get('activity')
        participants[uid]['end_merit'] = profile.get('merit')

        participants[uid]['post_count_difference'] = (
            int(participants[uid]['end_post_count']) -
            int(participants[uid]['start_post_count'])
        ) if known_start_info else 'unknown'

        participants[uid]['activity_gained'] = (
            int(participants[uid]['end_activity']) -
            int(participants[uid]['start_activity'])
        ) if known_start_info else 'unknown'

        participants[uid]['merit_gained'] = (
            int(participants[uid]['end_merit']) -
            int(participants[uid]['start_merit'])
        ) if known_start_info else 'unknown'

        participants[uid]['posts_made'] = len(posts)
        print("Done")
    return participants


def add_campaign(args):
    """Add a new campaign"""
    path = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    campaign_folder = path / campaign_name
    if not campaign_folder.exists():
        print(f"Adding a campaign with name {campaign_name}")
        os.makedirs(campaign_folder)
        metadata = {
            CAMPAIGN_NAME_KEY: campaign_name,
            PARTICIPANTS_KEY: dict()
        }
        write_metadata(path, campaign_name, json.dumps(metadata))
        print("Campaign added and metadata written to the campaign folder")
    else:
        print("Campaign folder already exists")


def add_payment_address(args):
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    str_uid = str(args.uid)
    payment_address = args.payment_address
    if campaign_exists(data_folder, campaign_name):
        campaign_metadata = read_metadata(data_folder, campaign_name)
        if str_uid in campaign_metadata[PARTICIPANTS_KEY]:
            campaign_metadata[PARTICIPANTS_KEY][str_uid][PAYMENT_ADDRESS_KEY] = payment_address
            write_metadata(data_folder, campaign_name, json.dumps(campaign_metadata))
        else:
            print('User not in campaign')
    else:
        print('Given campaign not found')


def add_round_payment_address(args):
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    round_number = args.round_number
    str_uid = str(args.uid)
    payment_address = args.payment_address
    campaign_path = campaign_folder_path(data_folder, campaign_name)
    if campaign_exists(data_folder, campaign_name):
        if not round_exists(campaign_path, round_number):
            print('Given round not found... aborting')
            return
        campaign_metadata = read_metadata(data_folder, campaign_name)
        round_metadata = read_round_data(campaign_path, round_number)
        campaign_participants = campaign_metadata[PARTICIPANTS_KEY]
        round_participants = round_metadata[PARTICIPANTS_KEY]
        if str_uid not in campaign_participants:
            print(f'Participant {str_uid} not found in campaign... aborting')
            return
        if str_uid not in round_participants:
            print(f'Participant {str_uid} not found in given round... aborting')
            return
        campaign_participants[str_uid][PAYMENT_ADDRESS_KEY] = payment_address
        round_participants[str_uid][PAYMENT_ADDRESS_KEY] = payment_address
        campaign_metadata[PARTICIPANTS_KEY] = campaign_participants
        round_metadata[PARTICIPANTS_KEY] = round_participants
        write_metadata(data_folder, campaign_name, json.dumps(campaign_metadata))
        write_round_data(campaign_path, round_number, json.dumps(round_metadata))
    else:
        print('Given campaign not found... aborting')


def add_round(args):
    """Add a new round"""
    path = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    if not campaign_exists(path, campaign_name):
        print("Campaign with given name doesn't exist")
        return
    campaign = campaign_folder_path(path, campaign_name)
    round_number = args.round_number
    known_start_info = False
    if not round_exists(campaign, round_number):
        print(f"Adding round number {round_number}")
        round_folder = campaign / str(round_number)
        os.makedirs(round_folder)
        if not (round_start := args.round_start):
            known_start_info = True
            round_start = int(time.time())
        if campaign_has_participants(path, campaign_name):
            new_round = {
                CAMPAIGN_NAME_KEY: campaign_name,
                'round_number': round_number,
                'ended': False,
                'round_start': round_start,
                'round_start_utc': datetime.utcfromtimestamp(round_start).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),
                PARTICIPANTS_KEY: initialize_round_participants(
                    path, campaign_name, round_start, known_start_info)
            }
            write_round_data(campaign, round_number, json.dumps(new_round))
            print("Round added and written to the campaign folder")
        else:
            print("Campaign doesn't have participants")
    else:
        print("Round already exists")


def end_round(args):
    """End an existing round"""
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    if not campaign_exists(data_folder, campaign_name):
        print("Campaign with given name does not exist")
        return
    campaign_path = campaign_folder_path(data_folder, campaign_name)
    round_number = args.round_number
    if round_exists(campaign_path, round_number):
        now = time.time()
        round_dict = read_round_data(campaign_path, round_number)
        if round_has_ended(campaign_path, round_number):
            print("Round has already ended")
            return
        print(f"Ending round {round_number} and calculating posts...")
        round_dict['ended'] = True
        round_dict['round_end'] = int(now)
        round_dict['round_end_utc'] = datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%SZ")
        if round_has_participants(campaign_path, round_number):
            round_dict[PARTICIPANTS_KEY] = finalize_round_participants(
                round_dict.get(PARTICIPANTS_KEY))
        else:
            print("No participants to count posts for")
        write_round_data(campaign_path, round_number, json.dumps(round_dict))
    else:
        print("No such round... aborting")


def add_participant(args):
    """Add a participant to campaign"""
    path = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    uid = args.uid
    payment_address = args.payment_address
    if campaign_exists(path, campaign_name):
        metadata = read_metadata(path, campaign_name)
        print("Adding participant...")
        if PARTICIPANTS_KEY not in metadata:
            metadata[PARTICIPANTS_KEY] = dict()
        if str(uid) not in metadata[PARTICIPANTS_KEY]:
            try:
                profile = fetch_bitcointalk_profile(uid)
                print(f"Adding participant {uid}...")
                participant = dict()
                participant['name'] = profile.get('name')
                participant[PAYMENT_ADDRESS_KEY] = payment_address if payment_address else None
                metadata["participants"][str(uid)] = participant
            except (FileNotFoundError, CrawlerResultError) as error:
                logger.error(error)
                raise
            write_metadata(path, campaign_name, json.dumps(metadata))
            print("Participant added")
        else:
            print("Participant with given UID already exists")
    else:
        logger.error("Campaign with given name doesn't exist.")


def add_round_participant(args):
    """Add a participant to a round"""
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    payment_address = args.payment_address
    uid = args.uid
    campaign_path = campaign_folder_path(data_folder, campaign_name)
    if campaign_exists(data_folder, campaign_name):
        campaign_metadata = read_metadata(data_folder, campaign_name)
        round_number = args.round_number
        str_uid = str(uid)
        if round_exists(campaign_path, round_number):
            print("Adding participant to round (and campaign if not already present)")
            round_metadata = read_round_data(campaign_path, round_number)
            if PARTICIPANTS_KEY not in campaign_metadata:
                campaign_metadata[PARTICIPANTS_KEY] = dict()
            if PARTICIPANTS_KEY not in round_metadata:
                round_metadata[PARTICIPANTS_KEY] = dict()
            if str_uid in round_metadata[PARTICIPANTS_KEY]:
                print("Participant already found in given round")
                return
            else:
                current_time = int(time.time())
                round_participant = fill_round_participant_info(uid, payment_address, current_time, True)
                username = round_participant.get('name')
                round_metadata[PARTICIPANTS_KEY][str_uid] = round_participant
                write_round_data(campaign_path, round_number, json.dumps(round_metadata))
                print(f"{username} added to round")
            if str_uid in campaign_metadata[PARTICIPANTS_KEY]:
                print("Participant already found in campaign. Doing nothing.")
            else:
                participant = dict()
                participant['name'] = username
                participant[PAYMENT_ADDRESS_KEY] = payment_address if payment_address else None
                campaign_metadata[PARTICIPANTS_KEY][str_uid] = username
                write_metadata(data_folder, campaign_name, json.dumps(campaign_metadata))
                print(f"{username} added to campaign")
        else:
            print("Given round number doesn't exist... aborting")
    else:
        print("Campaign with given name doesn't exist... aborting")


def remove_participant(args):
    """Remove a participant from campaign"""
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    uid = args.uid
    if campaign_exists(data_folder, campaign_name):
        metadata = read_metadata(data_folder, campaign_name)
        if PARTICIPANTS_KEY in metadata:
            if str(uid) in metadata[PARTICIPANTS_KEY]:
                print(f"Deleting participant with uid {uid}")
                del metadata[PARTICIPANTS_KEY][str(uid)]
                write_metadata(data_folder, campaign_name, json.dumps(metadata))
                print("Participant deleted")
            else:
                print("Participant with given UID is not a part of the campaign")
        else:
            print("No participants in the campaign")


def round_to_csv(args):
    """Convert round JSON to csv"""
    data_folder = data_folder_path(args.data_folder)
    campaign_name = args.campaign_name
    if campaign_exists(data_folder, campaign_name):
        campaign_path = campaign_folder_path(data_folder, campaign_name)
        round_number = args.round_number
        if round_exists(campaign_path, round_number):
            print("Writing round data to csv...")
            round_data = read_round_data(campaign_path, round_number)
            round_folder = round_folder_path(campaign_path, round_number)
            with (round_folder / 'round.csv').open('w', newline='') as f:
                csv_writer = csv.writer(f, delimiter=';')
                csv_writer.writerow(
                    ['round_number', 'ended', 'round_start',
                        'round_end', 'round_start_utc', 'round_end_utc'])
                csv_writer.writerow([
                    round_data.get('round_number'),
                    round_data.get('ended'),
                    round_data.get('round_start'),
                    round_data.get('round_end'),
                    round_data.get('round_start_utc'),
                    round_data.get('round_end_utc')
                ])
                if PARTICIPANTS_KEY in round_data:
                    participants = round_data[PARTICIPANTS_KEY].values()
                    if len(participants) > 0:
                        csv_writer.writerow(['Participants'])
                        csv_writer.writerow(next(iter(participants)).keys())
                        for item in participants:
                            csv_writer.writerow(item.values())
            print("Done")
        else:
            print("Round does not exist")
    else:
        print("Campaign does not exist")
