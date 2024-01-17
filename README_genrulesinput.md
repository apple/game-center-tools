# Writing matchmaking rule expressions

**Abstract:**

Explore rule expressions using the [JMESPath playground](https://play.jmespath.org) and use a Python 3 script to generate the rule based matchmaking JSON input.


## Overview

[Rule based matchmaking](https://developer.apple.com/documentation/gamekit/matchmaking_rules) uses expressions in the [JMESPath JSON query language](https://jmespath.org) against JSON representations of match requests to select the best requests for a match.
The expressions can be complex and it is useful to explore the results of intermediate expressions in order to obtain the desired result.
Explore	rule expressions using the [JMESPath playground](https://play.jmespath.org) with example input representing requests in the queue.
The structure of the JSON used as input when evaluating the expressions is described in the App Store Connect API documentation for [Expressions](https://developer.apple.com/documentation/appstoreconnectapi/game_center/expressions).
However, it is tedious and time consuming to construct the input manually.
Use the script to generate the input from the same compact input as the `testrules.py` script.

For a complete list of the `genrulesinput.py` arguments, run the  `genrulesinput.py —h` command.

## Example 1

In The first example there are 3 requests in the queue:

1. Player skill = 1, submitted 20 seconds ago.
2. Player skill = 50, submitted 10 seconds ago.
3. Request from player with skill = 20, invited player skill = 30, submitted just now.

Run the [genrulesinput.py](https://github.com/apple/game-center-tools/README_genrulesinput.md) script with the input shown to generate the input for these requests.

```
$ genrulesinput.py << 'EOF'
> [
>   {"secondsInQueue":20, "skill":1},
>   {"secondsInQueue":10, "skill":50},
>   [{"skill":20}, {"skill":30}]
> ]
> EOF
{           
    "requests": [
        {       
            "requestName": "r1",
            "playerId": "r1_p1",
            "properties": {
                "skill": 1
            },
...
                    "properties": {
                        "skill": 30
                    },
                    "requestName": "r3"
                }
            ]
        }
    ]
}
```

The script generates over 160 lines and so it is left to the reader to run the script as above and paste the generated input into the [JMESPath playground](https://play.jmespath.org) "Input JSON" field.

Enter `players[].properties.skill` into the expression field. Observe the `Result` field contains an array of the skill value for each player.

```
[
  1,
  50,
  20,
  30
]
```

You can use the [diff](https://developer.apple.com/documentation/appstoreconnectapi/game_center/expressions/computing_numeric_differences) function to evaluate the skill range in a MATCH rule expression.
However, currently this isn't available in the [JMESPath playground](https://play.jmespath.org).

If you use the expression `requests[].properties.skill` the result only contains the skill values for the players making the requests and doesn't include the value the request provides for the invited player.
This is the difference between the `players` and the `requests` object in the input.

```
[
  1,
  50,
  20
]
```

Enter `requests[].secondsInQueue` to obtain an array of the time in the queue for each request.

```
[
  20,
  10,
  0
]
```

Enter `avg(requests[].secondsInQueue)` to calculate the average age of the requests.
The result will be `10`.

### Example 2

In the second example there are 2 new requests:

1. Request from an older version of the app where no skill property is provided.
2. Request from a new version of the app where a skill of 45 is provided.

```
$ genrulesinput.py << 'EOF'
> [
>   {"skill":45},
>   {}
> ]
> EOF
...
    "players": [
        {
            "playerId": "r1_p1",
            "properties": {
                "skill": 45
            },
            "requestName": "r1"
        },
        {
            "playerId": "r2_p1",
            "properties": {},
            "requestName": "r2"
        }
    ],
...
```

The objective is to write an expression that evaluates an array which contains a skill value for each request and provides a default value where the request provides no skill property.
Enter the expression used before `players[].properties.skill` to obtain an array of skill values.

```
[
  45
]
```

Enter `requests[].properties.[ skill, ``50``]` to generate an array for each request where the first element is the actual skill value and the second is the default skill value of `50`.

```
[
  [
    45,
    50
  ],
  [
    null,
    50
  ]
]
```

Enter `requests[].properties.[ skill, ``50``][*].not_null(@) | [*][0]` which flattens the arrays one level, filters out null values, pipes the results to select the first element, and flattens again into a single array of a skill value for each request.

```
[
  45,
  50
]
```

This can then be used to evaluate a skill range and compare to the desired skill range for the match.

As you can see the [JMESPath JSON query language](https://jmespath.org) is very powerful and it is helpful to have a playground to explore complex expressions.

