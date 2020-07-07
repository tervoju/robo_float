"""
This file contains some hand-picked PGN identifiers.
to be modfied
"""

message_types = {
    "18FEE900": {
        "name": "Fuel Consumption (Liquid)",
        "parameters": [
            {
                "name": "Total Fuel Used",
                "bytes": "4:7",
                "offset": 0,
                "resolution": 0.5,
                "unit": "l",
            }
        ]
    },
    "18FEF200": {
        "name": "Fuel Economy (Liquid)",
        "parameters": [
            {
                "name": "Fuel Rate",
                "bytes": "0:1",
                "offset": 0,
                "resolution": 0.05,
                "unit": "l/h",
            }
        ]
    },
    "0C00EF47": {
        "name": "Fuel level",
        "parameters": [
            {
                "name": "Fuel Level",
                "bytes": "1",
                "offset": 0,
                "resolution": 0.4,
                "unit": "%",
            }
        ]
    },
    "18FEE500": {
        "name": "Engine Hours, Revolutions (HOURS)",
        "parameters": [
            {
                "name": "Engine Total Hours of Operation",
                "bytes": "0:3",
                "offset": 0,
                "resolution": 0.05,
                "unit": "h",
            }
        ]
    },
    "1CFF1404": {
        "name": "Operation State",
        "parameters": [
            {
                "name": "Status",
                "bytes": "0",
                "offset": 0,
                "resolution": 1,
                "unit": "int",
            }
        ]
    },
}