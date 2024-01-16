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
    appVersion = "appVersion"
    bundleId = "bundleId"
    latitude = "latitude"
    locale = "locale"
    longitude = "longitude"
    maxPlayers = "maxPlayers"
    minPlayers = "minPlayers"
    platform = "platform"
    playerCount = "playerCount",
    secondsInQueue = "secondsInQueue"


def to_IndexRequestPlayersTuple(index, input):
    """ Return a tuple of the index(0), request (1), and list of player properties (2)
    """

    requestInput = input[0] if type(input) == list else input
    inputList = input if type(input) == list else [ input ]
    playersProperties = list(map(lambda p: to_PlayerProperties(p), inputList))
    players = list(map(lambda i: to_Player(index, i + 1, playersProperties[i]), range(0, len(playersProperties))))
    request = {
        "requestName": f'r{index}',
        "playerId": f'r{index}_p1',
        "properties": playersProperties[0],
        "players": players,
        Keys.appVersion: requestInput.get(Keys.appVersion) or "1.0.0",
        Keys.bundleId: requestInput.get(Keys.bundleId) or "com.example.mygame",
        Keys.platform: requestInput.get(Keys.platform) or "IOS",
        Keys.locale: requestInput.get(Keys.locale) or "EN-US",
        Keys.longitude: requestInput.get(Keys.longitude) or 0,
        Keys.latitude: requestInput.get(Keys.latitude) or 0,
        Keys.minPlayers: requestInput.get(Keys.minPlayers) or 2,
        Keys.maxPlayers: requestInput.get(Keys.maxPlayers) or 2,
        Keys.playerCount: len(players),
        Keys.secondsInQueue : requestInput.get(Keys.secondsInQueue) or 0
    }

    return (
        index,
        request,
        players
    )

def to_Player(requestIndex, playerIndex, playerProperties):
    """ Return player properties - stripped of request level keys
    """
    
    return {
        "playerId": f'r{requestIndex}_p{playerIndex}',
        "properties": playerProperties,
        "requestName": f'r{requestIndex}'
    }

def to_PlayerProperties(input):
    """ Return player properties - stripped of request level keys
    """
    
    return dict(filter(lambda item: not item[0] in [e.value for e in Keys], input.items()))


def to_Request(requestIndex):
    return {
        "type": "gameCenterMatchmakingTestRequests",
        "id": f'${{r{requestIndex}}}'
    }

def to_Teams(indexRequestPlayers):
    """ Return teams from list of tuples of index, request and list of players.
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
        requestIndex = indexRequestPlayer[0]
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
        "-d",
        "--debug",
        type=bool,
        action=argparse.BooleanOptionalAction,
        help="enable debug logging",
    )
    args = parser.parse_args()
    input = json.load(sys.stdin)
    verify_input(input)

    indexRequestPlayers = list(map(lambda t: to_IndexRequestPlayersTuple(t[0], t[1]),
                                       map(lambda i: (i + 1, input[i]), range(0, len(input)))))
    requests = list(map(lambda t: t[1], indexRequestPlayers))
    players = list(chain.from_iterable(map(lambda t: t[2], indexRequestPlayers)))
    teams = to_Teams(indexRequestPlayers)
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
