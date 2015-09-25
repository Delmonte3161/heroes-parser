__author__ = 'ds3161'
import api.tasks
import json
import os
import psycopg2
import ConfigParser
import datetime
import sys


def insert_match_record(conn, key, match_date, type, map, winning_team_id):
    print "insert_match_record: " + " : " + str(key) + " : " + str(match_date) + " : " + str(
        type) + " : " + str(map) + " : " + str(winning_team_id)
    cursor = conn.cursor()
    query = "select id from match where key = '" + key + "';"
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        date = datetime.datetime.utcfromtimestamp(match_date)
        query = "insert into match (key, date, type, map, winning_team_id) VALUES (%s, %s, %s, %s, %s) returning id;"
        data = (key, date, type, map, winning_team_id)
        cursor.execute(query, data)
        return cursor.fetchone()[0]
    else:
        print "Match record already exists"
        return 0


def insert_player_record(conn, player_id, player_name):
    print "insert_player_record: " + str(player_id) + " : " + str(player_name)
    cursor = conn.cursor()
    query = "select id from player where id = " + str(player_id) + ";"
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        query = "insert into player (id, name) VALUES (%s, %s);"
        data = (player_id, player_name)
        cursor.execute(query, data)
    else:
        print "Player record already exists"


def insert_match_player_relationship_record(conn, match_id, team_id, player_id, hero):
    print "insert_match_player_relationship_record: " + str(id) + " : " + str(match_id) + " : " + str(
        team_id) + " : " + str(
        player_id) + " : " + str(hero)
    cursor = conn.cursor()
    query = "insert into match_player_rel (match_id, team_id, player_id, hero) VALUES (%s, %s, %s, %s);"
    data = (match_id, team_id, player_id, hero)
    cursor.execute(query, data)


def get_db_connection(config):
    host = config.get('Database', 'database.host')
    port = config.get('Database', 'database.port')
    dbname = config.get('Database', 'database.dbname')
    user = config.get('Database', 'database.user')
    password = config.get('Database', 'database.password')
    print "Initializing connection to database..."
    print "host: " + host
    print "port " + port
    print "dbname " + dbname

    try:
        conn = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
        return conn
    except:
        print "Error connecting to the database"


def get_match_winning_team(player_list):
    for player in player_list:
        if player["m_result"] == 1:
            return player["m_teamId"]


def generate_match_key(match_date, player_list):
    key = str(match_date)
    player_id_list = []
    for player in player_list:
        player_id_list.append(player["m_toon"]["m_id"])

    # sort list to ensure consistent order of players across replays
    player_id_list_sorted = sorted(player_id_list)
    for player_id in player_id_list_sorted:
        key += ":" + str(player_id)

    return key


def is_computer_player_present(player_list):
    for player in player_list:
        if player["m_toon"]["m_id"] == 0:
            return 1
    return 0


def process_replay(conn, fn):
    print "Processing replay file: " + fn
    replay_file = open(fn)
    items = ["RawReplayDetails", "RawReplayAttributesEvents"]
    retval = api.tasks.AnalyzeReplayFile(replay_file, items)
    replay_file.close()
    data_string = json.dumps(retval, skipkeys=False, ensure_ascii=False)
    data = json.loads(data_string.decode('utf-8', 'ignore'))
    details = data["raw"]["details"]
    attributes = data["raw"]["attributes_events"]

    if is_computer_player_present(details["m_playerList"]) == 1 or len(details["m_playerList"]) < 10:
        print "Computer Player found.  Skipping replay."
        return

    # this works for windows dates.  What about mac?  Will worry about it when I need to worry about it
    match_date = ((details["m_timeUTC"] - 116444736000000000) / 10000) / 1000
    key = generate_match_key(match_date, details["m_playerList"])
    winning_team_id = get_match_winning_team(details["m_playerList"])
    game_mode = get_game_mode(attributes)
    map = details["m_title"]

    match_id = 0
    try:
        match_id = insert_match_record(conn, key, match_date, game_mode, map, winning_team_id)
    except:
        conn.rollback()
        print "Unexpected error:", sys.exc_info()
        return

    if match_id > 0:
        for player in details["m_playerList"]:
            try:
                insert_player_record(conn, player["m_toon"]["m_id"], player["m_name"])
                insert_match_player_relationship_record(conn, match_id, player["m_teamId"],
                                                        player["m_toon"]["m_id"], player["m_hero"])
            except:
                conn.rollback()
                "Error in InsertPlayerRecord"

    # transactionally commit the match
    conn.commit()


def process_all_replays(conn, path):
    print "Begin processing replays in path: " + path
    match_id = 0
    match_player_rel_id = 0
    for fn in os.listdir(path):
        if fn.__contains__("(Training)"):
            continue
        if fn.__contains__(".StormReplay"):
            process_replay(conn, path + fn)

            # break # uncomment to test just one match


def get_game_mode(attributes):
    for x in attributes["scopes"]["16"]["4010"]:
        game_type = x["value"]
    for y in attributes["scopes"]["16"]["4018"]:
        draft_type = y["value"]
    game_mode = "unknown"
    if game_type == "stan":
        game_mode = "Quick Match"
    elif game_type == "priv":
        game_mode = "Custom"
    elif game_type == "drft":
        if draft_type == "fcfs":
            game_mode = "Team League"
        else:
            game_mode = "Hero League"
    return game_mode


def main():
    print "Starting main program"
    config = ConfigParser.RawConfigParser()
    config.read('heroes.ini')
    path = config.get('Replays', 'replays.path');
    conn = get_db_connection(config)
    process_all_replays(conn, path)


if __name__ == "__main__":
    main()



# print data_string

#        # write the json file
#        with open('/Users/ds3161/parses/' + fn + ".json", 'w') as outfile:
#            json.dump(retval, outfile,skipkeys=False,ensure_ascii=False)


# ,"RawReplayTrackerEvents","RawReplayAttributesEvents","RawReplayGameEvents","RawReplayMessageEvents","RawTalentSelectionGameEvents"

# GameTypeAttribute = 3009,
#
# Character = 4002,
# CharacterLevel = 4008,
#
# HeroSelectionMode = 4010,
# HeroDraftMode = 4018
