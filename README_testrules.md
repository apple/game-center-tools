# Testing matchmaking rules using a Python script

**Abstract:**

Test your matchmaking rules before running your game using a Python 3 script to execute the App Store Connect APIs.


## Overview

You can test the matchmaking rules you configure in Game Center using [App Store Connect APIs](https://developer.apple.com/documentation/appstoreconnectapi/game_center#4301628), without running your native game.
Test your rules to ensure that they find compatible players without long wait times. You pass your rule set with sample match requests to the test APIs and then analyze the match results.
Use the `testrules.py` command-line script to reduce the amount of JSON content you need to provide to test your matchmaking rules.


## Configure your matchmaking rules

Before you begin, create the matchmaking rules in Game Center that include the rule set, rule, and queue objects.
You group rules into rule sets and then assign the rule sets to queues.
Later, in your game code, you submit match requests to specific queues that you configure in Game Center.
To create your matchmaking rules, see [Finding players using matchmaking rules](https://developer.apple.com/documentation/gamekit/matchmaking_rules/finding_players_using_matchmaking_rules).

Then follow these steps to use the script:

1. Optionally, set an environment variable for the rule ID (`RULE_ID`) and ASC API JWT authentication token (`ASC_API_TOKEN`) so you don’t need to pass these to the script.
2. Run the `pip3 `**`install`**` requests` command.

For a complete list of the `testrules.py` arguments, run the  `testrules.py —h` command.

## Test matchmaking rules

Pass the rule set ID as the `--rulesetid` argument and an array of objects in `stdin` to the `testrules.py` script.
Each object you pass represents a match request and contains the player properties that you later pass from a game instance.
You can use game-specific player properties in matchmaking rules to find compatible players.
For examples of rules that use player properties, see [Letting players join matches using party codes](https://developer.apple.com/documentation/gamekit/matchmaking_rules/letting_players_join_matches_using_party_codes)
and [Finding players with similar skill levels](https://developer.apple.com/documentation/gamekit/matchmaking_rules/finding_players_with_similar_skill_levels).

In the `testrules.py` example below, the rules match two players with skill values ranging from 0 to 20.
The `testrules.py` command passes four match requests to the testing API with player property skill values 1, 21, 2, and 22.
The script generates JSON content for the match requests with `requestName` attributes in sequence ( `r1`, `r2`, `r3`, `r4`, etc.), along with `playerId` attributes in the sequence (`r1_p1`, `r2_p1`, `r3_p1`, `r4_p1`, and so on).
If you associate more than one player with a match request, the script generates `playerId` attributes in the sequence: `r1_p1`, `r1_p2`, etc. 

The testing API response contains the match results. In this example, the skill-based matchmaking rules find players with compatible skill levels. The results contain two matches (`[ r1, r3 ]` and `[ r2, r4 ]`).

```
$ testrules.py --id 81ed2e4c-2c8f-4937-a1c8-0cdb5a6a54dd << 'EOF'
> [ { "skill": 1 }, { "skill": 21 }, { "skill": 2 }, { "skill": 22 } ]
> EOF
[
    [
        {
            "requestName": "r1",
            "teamAssignments": null
        },
        {
            "requestName": "r3",
            "teamAssignments": null
        }
    ],
    [
        {
            "requestName": "r2",
            "teamAssignments": null
        },
        {
            "requestName": "r4",
            "teamAssignments": null
        }
    ]
]
```

## Override script default values

To override the script defaults, include the attributes in the match request data you pass to the script. The script passes these default values for the required testing API endpoints (`appVersion`, `bundleId`, `platform`, and `secondsInQueue`):

```
"attributes": {
    "requestName": "r1",
    "appVersion": "1.0.0",
    "secondsInQueue": 0,
    "bundleId": "com.example.mygame",
    "platform": "IOS"
}
```

For example, to specify the amount of seconds a match request is in the queue, add `secondsInQueue` to the match request data:

```
$ testrules.py --id 81ed2e4c-2c8f-4937-a1c8-0cdb5a6a54dd << 'EOF'
> [
>   { "skill": 1 },
>   { "skill": 21, "secondsInQueue": 15 }
> ]
> EOF
```

## Test team assignments

If you create team rules, the testing API response contains team assignments.
In this example, the rules assign players to a blue or red team based on skill level.
For more information, see [Assigning players to teams using rules](https://developer.apple.com/documentation/gamekit/matchmaking_rules/assigning_players_to_teams_using_rules).

```
$ testrules.py --id b9eb9b92-ce9f-47b3-ac49-b94d75abc7f3 << 'EOF'
> [ { "skill": 1 }, { "skill": 2 }, { "skill": 3 }, { "skill": 4 } ]
> EOF
[
    [
        {
            "requestName": "r1",
            "teamAssignments": [
                {
                    "playerId": "r1_p1",
                    "team": "blue"
                }
            ]
        },
        {
            "requestName": "r2",
            "teamAssignments": [
                {
                    "playerId": "r2_p1",
                    "team": "red"
                }
            ]
        },
        {
            "requestName": "r3",
            "teamAssignments": [
                {
                    "playerId": "r3_p1",
                    "team": "red"
                }
            ]
        },
        {
            "requestName": "r4",
            "teamAssignments": [
                {
                    "playerId": "r4_p1",
                    "team": "blue"
                }
            ]
        }
    ]
```

