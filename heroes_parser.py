__author__ = 'ds3161'
import api.tasks
import json
import os
import psycopg2
import ConfigParser
import datetime
import sys


def insert_match_record(conn, key, datestring, map, winning_team_id):
    print "insert_match_record: " + " : " + str(key) + " : " + str(datestring) + " : " + str(
        map) + " : " + str(winning_team_id)
    cursor = conn.cursor()
    query = "select id from match where key = '" + key + "';"
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        date = datetime.datetime.utcfromtimestamp(datestring)
        query = "insert into match (key, date, type, map, winning_team_id) VALUES (%s, %s, 'unknown', %s, %s) returning id;"
        data = (key, date, map, winning_team_id)
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
    host = config.get('Database', 'database.host');
    port = config.get('Database', 'database.port');
    dbname = config.get('Database', 'database.dbname');
    user = config.get('Database', 'database.user');
    password = config.get('Database', 'database.password');
    print "Initializing connection to database..."
    print "host: " + host
    print "port " + port
    print "dbname " + dbname

    try:
        conn = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
        return conn
    except:
        print "Error connecting to the database"


def process_replays(conn, path):
    print "Begin processing replays in path: " + path
    match_id = 0
    match_player_rel_id = 0
    for fn in os.listdir(path):
        print fn
        if fn.__contains__(".StormReplay"):
            replay_file = open(path + fn)
            items = ["RawReplayDetails"]
            retval = api.tasks.AnalyzeReplayFile(replay_file, items)
            replay_file.close()
            data_string = json.dumps(retval, skipkeys=False, ensure_ascii=False)
            data = json.loads(data_string.decode('utf-8', 'ignore'))
            details = data["raw"]["details"]

            datestring = ((details["m_timeUTC"] - 116444736000000000) / 10000) /1000
            match_id += 1
            key = str(details["m_timeUTC"])
            winning_team_id = 0
            computer_found = 0
            for player in details["m_playerList"]:
                key += ":" + str(player["m_toon"]["m_id"])
                if player["m_result"] == 1:
                    winning_team_id = player["m_teamId"]
                if player["m_toon"]["m_id"] == 0:
                    computer_found = 1
                    break

            if computer_found == 1:
                continue

            match_id = 0
            try:
                match_id = insert_match_record(conn, key, datestring, details["m_title"], winning_team_id)
            except:
                print "Unexpected error:", sys.exc_info()
                continue

            if match_id > 0:
                for player in details["m_playerList"]:
                    try:
                        insert_player_record(conn, player["m_toon"]["m_id"], player["m_name"])
                        match_player_rel_id += 1
                        insert_match_player_relationship_record(conn, match_id, player["m_teamId"],
                                                                player["m_toon"]["m_id"], player["m_hero"])
                    except:
                        "Error in InsertPlayerRecord"
            # transactionally commit the match
            conn.commit()

            # break # uncomment to test just one match


def main():
    print "Starting main program"
    config = ConfigParser.RawConfigParser()
    config.read('heroes.ini')
    path = config.get('Replays', 'replays.path');
    conn = get_db_connection(config)
    process_replays(conn, path)


if __name__ == "__main__":
    main()




# print data_string

#        # write the json file
#        with open('/Users/ds3161/parses/' + fn + ".json", 'w') as outfile:
#            json.dump(retval, outfile,skipkeys=False,ensure_ascii=False)


# ,"RawReplayTrackerEvents","RawReplayAttributesEvents","RawReplayGameEvents","RawReplayMessageEvents","RawTalentSelectionGameEvents"
