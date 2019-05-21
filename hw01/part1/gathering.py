import logging
import sys
import requests
import json
import time
import glob
import pandas as pd
from prettytable import PrettyTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TABLE_FORMAT_FILE = 'data.csv'

# function to flatten nested json file


def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


def gather_process():
    logger.info("gather")

# first we need to get IDs of games. IDs of games stored in  schedule
    response = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?startDate=2012-08-01&endDate=2019-04-01")

    with open('schedule2012-2019.json', 'w') as outfile:
        json.dump(response.json(), outfile)

    print("Get ids of games")

    logger.info("start to download game files for 2012-2019 seasons")

    with open('schedule2012-2019.json', 'r') as file:
        schedule_dict = json.load(file)

# https://statsapi.web.nhl.com/api/v1/game/ID/boxscore
    urlapi = "https://statsapi.web.nhl.com/api/v1/game/"
    for data in range(len(schedule_dict['dates'])):
        for item in range(schedule_dict['dates'][data]['totalItems']):
            gameid = str(schedule_dict['dates'][data]['games'][item]['gamePk'])
            url = urlapi + gameid + "/linescore"
            response = requests.get(url)
            time.sleep(0.1)
            filename = "./games_data/" + gameid + ".json"
            with open(filename, 'w') as outfile:
                json.dump(response.json(), outfile)

    logger.info("finish dowloading games files for 2012-2019 seasons")


def convert_data_to_table_format():
    logger.info("transform")

    # Your code here
    # transform gathered data from txt file to pandas DataFrame and save as csv

    read_files = glob.glob("./games_data/*.json")

    list_files = []
    for filename in read_files:
        with open(filename, 'r') as f:
            try:
                list_files.append(json.load(f))
            except ValueError:
                print("JSON object issue: %s", filename)

    list_df = []

    for file in list_files:
        list_df.append(flatten_json(file))

    result_df = pd.DataFrame([list_df.pop()])

    for i in range(len(list_df)):
        result_df = result_df.append(pd.DataFrame([list_df.pop()]), sort=False)

    result_df.to_csv(TABLE_FORMAT_FILE)


def stats_of_data():
    logger.info("stats")

    # Your code here
    # Load pandas DataFrame and print to stdout different statistics about the data.
    # Try to think about the data and use not only describe and info.
    # Ask yourself what would you like to know about this data (most frequent word, or something else)
    df = pd.read_csv(TABLE_FORMAT_FILE, low_memory=False)
    teams = df.teams_home_team_name.unique()

    t = PrettyTable(['Team ', 'Game played', 'Goals scored', 'Goals Against', 'GF/G', 'GA/G'])
    for team in teams:
        game_played_home = df[df['teams_home_team_name'] == team].shape[0]
        game_played_away = df[df['teams_away_team_name'] == team].shape[0]
        goals_scored_home = df.loc[df['teams_home_team_name'] == team, 'teams_home_goals'].sum()
        goals_scored_away = df.loc[df['teams_away_team_name'] == team, 'teams_away_goals'].sum()
        goals_against_home = df.loc[df['teams_home_team_name'] == team, 'teams_away_goals'].sum()
        goals_against_away = df.loc[df['teams_away_team_name'] == team, 'teams_home_goals'].sum()
        goals_per_game = (goals_scored_home + goals_scored_away)/(game_played_away+game_played_home)
        goals_against_per_game = (goals_against_away+goals_against_home)/(game_played_away+game_played_home)
        t.add_row([team, game_played_away+game_played_home, goals_scored_home+goals_scored_away, goals_against_home + goals_against_away,
            goals_per_game, goals_against_per_game])

    print(t)


if __name__ == '__main__':
    """
    why main is so...?
    https://stackoverflow.com/questions/419163/what-does-if-name-main-do
    """
    logger.info("Work started")

    if sys.argv[1] == 'gather':
        gather_process()

    elif sys.argv[1] == 'transform':
        convert_data_to_table_format()

    elif sys.argv[1] == 'stats':
        stats_of_data()

    logger.info("work ended")
