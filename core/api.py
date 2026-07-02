import core.data as data
import csv
import json
import os
import re
from re import match

files = data.Files()

def get_game_path(game_path):
    try:
        game_path = game_path[1]
        if ("starfarer.api.zip" not in os.listdir(game_path)) or ("data" not in os.listdir(game_path)):
            print("Error: not a starsector directory")
            exit(1)
        print(f"Game data is located at {game_path}")
        files.set_game_path(game_path + "data")
    except IndexError:
        print("Error: game directory not specified")
        exit(1)
    except FileNotFoundError:
        print("Error: directory does not exist")
        exit(1)

def _parse_field(key, value):
    if match("^[0-9]+$", value):
        return int(value)
    elif match(r"^[0-9]+(\.[0-9]+)?$", value):
        return float(value)
    elif value == '':
        return None
    elif key in ["hints", "tags"]:
        return value.split(", ")
    return value

def list_ships():
    with open(files.game_path + "/hulls/ship_data.csv", "r") as f:
        reader = csv.DictReader(f)
        ships = []
        for row in reader:
            new_ship = {}
            for k, v in row.items():
                new_ship[k] = _parse_field(k, v)
            if new_ship["id"]:
                try:
                    with open(files.game_path + f"/hulls/{new_ship['id']}.ship", "r") as g:
                        ship_data = json.loads("".join([row for row in g]))
                        ships.append(new_ship | ship_data)
                except FileNotFoundError:
                    print(f"File not found: {new_ship['id']}.ship")
        return ships


def list_weapons():

    with open(files.game_path + "/weapons/weapon_data.csv", "r") as f:
        reader = csv.DictReader(f)
        weapons = []
        for row in reader:
            if row["id"]:
                new_weapon = {}
                for k, v in row.items():
                    new_weapon[k] = _parse_field(k, v)
                try:
                    print(new_weapon["id"])
                    with open(files.game_path + f"/weapons/{new_weapon['id']}.wpn", "r") as g:
                        text = "".join(row.split("#", 1)[0] for row in g)

                    text = re.sub(
                        r'(?<!")\b([A-Z][A-Z0-9_]*)\b(?!")',
                        r'"\1"',
                        text
                    )

                    text = re.sub(r',(\s*[}\]])', r'\1', text)

                    text = text.replace(";", ",")

                    weapon = json.loads(text)

                except json.JSONDecodeError as e:
                    print(f"Line {e.lineno}, column {e.colno}")
                    print(text.splitlines()[e.lineno - 1])
                    raise
                except FileNotFoundError: 
                    print(f"File not found: {new_weapon['id']}.wpn")
                weapons.append(new_weapon)
        return weapons
        
def new_battle():
    pass


def new_fleet():
    pass


def add_ship():
    pass
