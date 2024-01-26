#!/usr/bin/env python3

# Copyright (C) 2024 Apple Inc. All Rights Reserved.

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
    MAX_PLAYERS = "maxPlayers"
    MIN_PLAYERS = "minPlayers"
    PLATFORM = "platform"
    PLAYER_COUNT = "playerCount",
    SECONDS_IN_QUEUE = "secondsInQueue"


def to_index_request_players_tuple(index, input):
    """ Return a tuple of the index(0), request (1), and list of player properties (2).
    """

    request_input = input[0] if type(input) == list else input
    input_list = input if type(input) == list else [ input ]
    players_properties = [
        to_player_properties(p)
        for p in input_list
    ]
    players = [
        to_player(index, i + 1, players_properties[i])
        for i in range(0, len(players_properties))
    ]
    request = {
        "requestName": f'r{index}',
        "playerId": f'r{index}_p1',
        "properties": players_properties[0],
        "players": players,
        Keys.APP_VERSION: request_input.get(Keys.APP_VERSION) or "1.0.0",
        Keys.BUNDLE_ID: request_input.get(Keys.BUNDLE_ID) or "com.example.mygame",
        Keys.PLATFORM: request_input.get(Keys.PLATFORM) or "IOS",
        Keys.LOCALE: request_input.get(Keys.LOCALE) or "EN-US",
        Keys.LONGITUDE: request_input.get(Keys.LONGITUDE) or 0,
        Keys.LATITUDE: request_input.get(Keys.LATITUDE) or 0,
        Keys.MIN_PLAYERS: request_input.get(Keys.MIN_PLAYERS) or 2,
        Keys.MAX_PLAYERS: request_input.get(Keys.MAX_PLAYERS) or 2,
        Keys.PLAYER_COUNT: len(players),
        Keys.SECONDS_IN_QUEUE : request_input.get(Keys.SECONDS_IN_QUEUE) or 0
    }

    return (
        index,
        request,
        players
    )

def to_player(request_index, player_index, player_properties):
    """ Return player properties, stripped of request level keys.
    """
    
    return {
        "playerId": f'r{request_index}_p{player_index}',
        "properties": player_properties,
        "requestName": f'r{request_index}'
    }

def to_player_properties(input):
    """ Return player properties, stripped of request level keys.
    """
    
    return dict(item for item in input.items() if not item[0] in [e.value for e in Keys])


def to_request(request_index):
    return {
        "type": "gameCenterMatchmakingTestRequests",
        "id": f'${{r{request_index}}}'
    }

def to_teams(indexRequestPlayers):
    """ Return teams from list of tuples of index, request, and list of players.
    """
    maxPlayers = 2
    teams = [
        {
            "name": "blue",
            "minPlayers": 2,
            "maxPlayers": maxPlayers,
            "players": [
            ]
        },
        {
            "name": "red",
            "minPlayers": 2,
            "maxPlayers": maxPlayers,
            "players": [
            ]
        }
    ]

    teamIndex = 0
    
    for indexRequestPlayer in indexRequestPlayers:
        request_index = indexRequestPlayer[0]
        request = indexRequestPlayer[1]
        players = indexRequestPlayer[2]
        
        for player in players:
            teams[teamIndex]["players"].append(player)
            teamIndex = (teamIndex + 1) % len(teams)
            
    return teams

def verify_input(input):
    assert (type(input) is list), f'Input must be list. Found {type(input)}'

    for object in input:
        match object:
            case dict():
                pass
            case list():
                verify_input_list_of_object(object)
            case _:
                assert False, f'Object must be list of objects or an object. Found {type(object)}'
    return

def verify_input_list_of_object(input):
    assert (type(input) is list), f'Input must be list. Found {type(input)}'

    for object in input:
        assert (type(object) is dict), f'Input must be list of dict. Found {type(object)} in list'


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Create MATCH rules JSON input for JMESPath playground",
        epilog="""
        See https://developer.apple.com/documentation/appstoreconnectapi/creating_rule_expressions.

        The input is a JSON string representing an array of objects. Each object represents a request
        where the name and value pairs are either request-level properties or custom player properties.
        The request properties that can be set from the input are:

        appVersion      - default '1.0'
        bundleId        - default 'com.example.mygame'
        maxPlayers      - no default
        minPlayers      - no default
        platform        - default 'IOS'
        secondsInQueue  - default 0

        See https://developer.apple.com/documentation/appstoreconnectapi/gamecentermatchmakingtestrequestinlinecreate/attributes

        Other input request object names are assumed to be custom player properties.

        A input array object can also be an array of objects representing a request with invited players,
        where each object is the player properties. The first object representing the requesting player
        accepts request-level properties.
        """,
    )
    parser.add_argument(
        "-d",
        "--debug",
        type=bool,
        action=argparse.BooleanOptionalAction,
        help="enable debug logging",
    )
    args = parser.parse_args()
    input = json.load(sys.stdin)
    verify_input(input)

    index_input = [(i + 1, input[i]) for i in range(0, len(input))]
    index_request_players = [
        to_index_request_players_tuple(t[0], t[1])
        for t in index_input
    ]
    requests = [ t[1] for t in index_request_players ]
    players = [player for t in index_request_players for player in t[2]]
    assert players1 == players
    teams = to_teams(index_request_players)
    output = {
        "requests": requests,
        "players": players,
        "teams": teams
    }

    if args.debug:
        print("### Input")
        print(json.dumps(input, indent = 4))
        print("### Output")
    
    print(json.dumps(output, indent=4))

if __name__ == '__main__':
    sys.exit(main())
