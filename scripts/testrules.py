#!/usr/bin/env python3

# Copyright (C) 2023 Apple Inc. All Rights Reserved.

from enum import Enum
from itertools import chain

import argparse
import json
import os
import requests
import sys


class Keys(str, Enum):
    APP_VERSION = "appVersion"
    BUNDLE_ID = "bundleId"
    LOCALE = "locale"
    LOCATION = "location"
    MAX_PLAYERS = "maxPlayers"
    MIN_PLAYERS = "minPlayers"
    PLATFORM = "platform"
    SECOND_IN_QUEUE = "secondsInQueue"


def get_request(test_input):
    """Return test_input if dict, if list then return first object, else raise"""

    match test_input:
        case dict():
            return test_input
        case list():
            return test_input[0]
        case _:
            raise Exception(f"Expected dict or list but found {type(test_input)}")


def to_gameCenterMatchmakingTestPlayerProperties(
    request_ordinal, player_ordinal, player_properties
):
    """Return a gameCenterMatchmakingTestPlayerProperties dict"""

    # An inline test player property object is comprised of an id for the player.
    # The ids are in the sequence of "r1_p1", "r1_p2", etc, for the first request,
    # and "r2_p1", "r2_p2", for the second requests, and so on. This is to allow
    # for a request to include properties for more than one player.
    # See https://developer.apple.com/documentation/appstoreconnectapi/gamecentermatchmakingtestplayerpropertyinlinecreate
    player_id = f"r{request_ordinal}_p{player_ordinal}"
    properties_list = [
        {"key": item[0], "value": json.dumps(item[1])}
        for item in player_properties.items()
        if item[0] not in [k.value for k in Keys]
    ]

    return {
        "type": "gameCenterMatchmakingTestPlayerProperties",
        "id": f"${{{player_id}}}",
        "attributes": {"properties": properties_list, "playerId": player_id},
    }


def to_gameCenterMatchmakingTestRequests(
    request_ordinal, request_dict, player_properties
):
    """Return a dict for the request"""

    request_name = f"r{request_ordinal}"
    matchmaking_player_properties = [
        {
            "type": "gameCenterMatchmakingTestPlayerProperties",
            "id": f"${{r{request_ordinal}_p{i + 1}}}",
        }
        for i in range(0, len(player_properties))
    ]

    player_count = len(player_properties)
    request = {
        "type": "gameCenterMatchmakingTestRequests",
        "id": f"${{{request_name}}}",
        "attributes": {
            "requestName": request_name,
            Keys.APP_VERSION: request_dict.get(Keys.APP_VERSION, "1.0.0"),
            Keys.BUNDLE_ID: request_dict.get(Keys.BUNDLE_ID, "com.example.mygame"),
            Keys.LOCALE: request_dict.get(Keys.LOCALE, "EN-US"),
            Keys.LOCATION: request_dict.get(
                Keys.LOCATION, {"latitude": 0, "longitude": 0}
            ),
            Keys.PLATFORM: request_dict.get(Keys.PLATFORM, "IOS"),
            "playerCount": player_count,
            Keys.SECOND_IN_QUEUE: request_dict.get(Keys.SECOND_IN_QUEUE, 0),
        },
        "relationships": {
            "matchmakingPlayerProperties": {"data": matchmaking_player_properties}
        },
    }

    if request_dict.get(Keys.MIN_PLAYERS):
        request["attributes"][Keys.MIN_PLAYERS] = request_dict.get(Keys.MIN_PLAYERS)

    if request_dict.get(Keys.MAX_PLAYERS):
        request["attributes"][Keys.MAX_PLAYERS] = request_dict.get(Keys.MAX_PLAYERS)

    return request


def to_matchmakingPlayerProperties(request_ordinal, player_properties):
    """Return a list of player props"""

    return [
        to_gameCenterMatchmakingTestPlayerProperties(
            request_ordinal, i + 1, player_properties[i]
        )
        for i in range(0, len(player_properties))
    ]


def to_matchmakingRequest(request_ordinal):
    # A matchmakingRequest object is comprised of an id for the request unique within
    # the context of the /v1/gameCenterMatchmakingRuleSetTests end point. The request ids
    # are in the sequence of "r1", "r2", "r3", etc.
    # See https://developer.apple.com/documentation/appstoreconnectapi/gamecentermatchmakingtestrequest
    return {
        "type": "gameCenterMatchmakingTestRequests",
        "id": f"${{r{request_ordinal}}}",
    }


def to_matchmaking_request_tuple(request_ordinal, test_input):
    """Return a tuple of the request_ordinal(0), request (1), test requests (2), and list of player properties (3)."""

    request_dict = get_request(test_input)
    player_props_list = test_input if type(test_input) == list else [test_input]

    return (
        request_ordinal,
        to_matchmakingRequest(request_ordinal),
        to_gameCenterMatchmakingTestRequests(
            request_ordinal, request_dict, player_props_list
        ),
        to_matchmakingPlayerProperties(request_ordinal, player_props_list),
    )


def verify_input(test_input):
    if not type(test_input) is list:
        raise Exception(f"Input must be list. Found {type(test_input)}")

    for object in test_input:
        match object:
            case dict():
                pass
            case list():
                verify_input_list_of_object(object)
            case _:
                raise Exception(f"Object must be list of objects or an object. Found {type(object)}")
    return


def verify_input_list_of_object(test_input):
    if not type(test_input) is list:
        raise Exception(f"Input must be list. Found {type(test_input)}")

    for object in test_input:
        if not type(object) is dict:
            raise Exception(f"Input must be list of dict. Found {type(object)} in list")

def main():
    url = "https://api.appstoreconnect.apple.com/v1/gameCenterMatchmakingRuleSetTests"

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Test your matchmaking rules using the App Store Connect API /v1/gameCenterMatchmakingRuleSetTests endpoint",
        epilog="""
        See https://developer.apple.com/documentation/appstoreconnectapi/test_a_rule_set.

        The input is a JSON string representing an array of objects. Each object represents a request
        where the name/value pairs are either request level properties or custom player properties.
        The request properties that can be set from the input are:

        appVersion      - default '1.0'
        bundleId        - default 'com.example.mygame'
        locale          - default 'EN-US'
        location        - default {"latitude": 0, "longitude": 0}
        maxPlayers      - no default
        minPlayers      - no default
        platform        - default 'IOS'
        secondsInQueue  - default 0

        See https://developer.apple.com/documentation/appstoreconnectapi/gamecentermatchmakingtestrequestinlinecreate/attributes

        Other input request object names are assumed to be custom player properties.

        A input array object can also be an array of objects representing a request with invited players
        where each object is the player properties. The first object representing the requesting player
        accepts request level properties.
        """,
    )
    parser.add_argument(
        "-a",
        "--auth",
        default=os.environ.get("ASC_API_TOKEN"),
        help="ASC API JWT authentication token (default: ASC_API_TOKEN environment variable)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        type=bool,
        action=argparse.BooleanOptionalAction,
        help="enable debug logging",
    )
    parser.add_argument(
        "-i",
        "--rulesetid",
        default=os.environ.get("RULESET_ID"),
        required=False,
        help="Rule set id (default: RULESET_ID environment variable)",
    )
    parser.add_argument(
        "-u", "--url", default=url, help=f"Test API url (default: {url})"
    )
    args = parser.parse_args()

    url = args.url
    authentication_token = args.auth
    rule_id = args.rulesetid

    test_input = json.load(sys.stdin)
    verify_input(test_input)

    matchmaking_request_tuples = [
        to_matchmaking_request_tuple(i + 1, test_input[i])
        for i in range(0, len(test_input))
    ]
    matchmaking_requests = [t[1] for t in matchmaking_request_tuples]
    included_gameCentearMatchmakingTestRequests = [
        t[2] for t in matchmaking_request_tuples
    ]
    included_gameCenterMatchmakingTestPlayerProperties = list(
        chain.from_iterable([t[3] for t in matchmaking_request_tuples])
    )
    included = (
        included_gameCentearMatchmakingTestRequests
        + included_gameCenterMatchmakingTestPlayerProperties
    )

    if args.debug:
        print("### Input")
        print(json.dumps(test_input, indent=4))

    headers = {"Authorization": authentication_token}
    content = {
        "data": {
            "type": "gameCenterMatchmakingRuleSetTests",
            "attributes": {},
            "relationships": {
                "matchmakingRuleSet": {
                    "data": {"type": "gameCenterMatchmakingRuleSets", "id": rule_id}
                },
                "matchmakingRequests": {"data": matchmaking_requests},
            },
        },
        "included": included,
    }

    if args.debug:
        print(f"### POST {url}")
        print("### Content")
        print(json.dumps(content, indent=4))

    response = requests.post(url=url, headers=headers, json=content, verify=True)
    response_json = response.json()

    if args.debug:
        print("### Response")
        print(json.dumps(response_json, indent=4))
        print("### Output")

    if response_json.get("errors"):
        print(json.dumps(response_json, indent=4))
    else:
        print(
            json.dumps(
                response_json["data"]["attributes"]["matchmakingResults"], indent=4
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
