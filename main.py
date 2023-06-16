"""Bitcointalk Campaign Manager entry point"""
import logging
from pathlib import Path

from core import add_campaign, add_participant, remove_participant, add_round, end_round, round_to_csv

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--data_folder', type=Path, help=
        'Folder where campaign related date is saved. '
        'By default the current path.')
    subparsers = arg_parser.add_subparsers(dest='command', required=True,
                                        help="choose resource to work on")

    campaign_parser = subparsers.add_parser('campaign', help='campaign related actions')
    campaign_common_args = argparse.ArgumentParser(add_help=False)
    campaign_common_args.add_argument('campaign_name', help='name of the campaign')
    campaign_subparser = campaign_parser.add_subparsers(dest='action', required=True)

    add_campaign_subparser = campaign_subparser.add_parser('add', parents=[campaign_common_args])
    add_campaign_subparser.set_defaults(func=add_campaign)

    add_participant_subparser = campaign_subparser.add_parser(
        'add_participant', parents=[campaign_common_args])
    add_participant_subparser.add_argument('uid', type=int, help="bitcointalk uid of participant")
    add_participant_subparser.set_defaults(func=add_participant)

    remove_participant_subparser = campaign_subparser.add_parser(
        'remove_participant', parents=[campaign_common_args])
    remove_participant_subparser.add_argument(
        'uid', type=int, help="bitcointalk uid of participant")
    remove_participant_subparser.set_defaults(func=remove_participant)

    round_parser = subparsers.add_parser('round', help='round related actions')
    round_common_args = argparse.ArgumentParser(add_help=False)
    round_common_args.add_argument('campaign_name', help='name of the campaign')
    round_common_args.add_argument('round_number', type=int, help='number of the round')
    round_subparser = round_parser.add_subparsers(dest='action', required=True)

    add_round_subparser = round_subparser.add_parser('add', parents=[round_common_args])
    add_round_subparser.set_defaults(func=add_round)
    add_round_subparser.add_argument('--round_start', type=int, help=
        'timestamp of when round started (seconds since epoch). '
        'Current time used if not provided.')

    end_round_subparser = round_subparser.add_parser('end', parents=[round_common_args])
    end_round_subparser.set_defaults(func=end_round)

    round_csv_subparser = round_subparser.add_parser('round_to_csv', parents=[round_common_args])
    round_csv_subparser.set_defaults(func=round_to_csv)

    ns = arg_parser.parse_args()
    ns.func(ns)
    