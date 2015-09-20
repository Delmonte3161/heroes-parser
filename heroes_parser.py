__author__ = 'ds3161'
import api.tasks
import json
import os
import psycopg2
import ConfigParser

def InsertMatchRecord(conn, match_id, key, datestring, map, winning_team_id):
    print "InsertMatchRecord: " + str(match_id) + " : " + str(key) + " : " + str(datestring) + " : " + str(
        map) + " : " + str(winning_team_id)
    cursor = conn.cursor()
    query = "select id from match where key = '" + key + "';"
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        query = "insert into match (id, key, date, type, map, winning_team_id) VALUES (%s, %s, to_timestamp(%s), 'unknown', %s, %s);"
        data = (match_id, key, datestring, map, winning_team_id)
        cursor.execute(query, data)
        return 1
    else:
        print "Match record already exists"
        return 0

def InsertPlayerRecord(conn, player_id, player_name):
    print "InsertPlayerRecord: " + str(player_id) + " : " + str(player_name)
    cursor = conn.cursor()
    query = "select id from player where id = " + str(player_id) + ";"
    cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) == 0:
        query = "insert into player (id, player_name) VALUES (%s, %s);"
        data = (player_id, player_name)
        cursor.execute(query, data)
    else:
        print "Player record already exists"


def InsertMatchPlayerRelRecord(conn, id, match_id, team_id, player_id, hero):
    print "InsertMatchPlayerRelRecord: " + str(id) + " : " + str(match_id) + " : " + str(team_id) + " : " + str(
        player_id) + " : " + str(hero)
    cursor = conn.cursor()
    query = "insert into match_player_rel (id, match_id, team_id, player_id, hero) VALUES (%s, %s, %s, %s, %s);"
    data = (id, match_id, team_id, player_id, hero)
    cursor.execute(query, data)

def GetDBConnection(config):
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
        conn = psycopg2.connect(host=host, port=port,database=dbname, user=user, password=password)
        return conn
    except:
        print "Error connection to the database"

def ProcessReplays(conn, path):
    print "Begin processing replays in path: " + path
    match_id = 0
    match_player_rel_id = 0
    for fn in os.listdir(path):
        print fn
        if fn.__contains__(".StormReplay"):
            replayFile = open(path + fn)
            items = ["RawReplayDetails"]
            retval = api.tasks.AnalyzeReplayFile(replayFile, items)
            replayFile.close()
            data_string = json.dumps(retval, skipkeys=False, ensure_ascii=False)
            data = json.loads(data_string.decode('utf-8', 'ignore'))
            details = data["raw"]["details"]

            datestring = (details["m_timeUTC"] - 116444736000000000) / 10000
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

            match_inserted = 0
            try:
                match_inserted = InsertMatchRecord(conn, match_id, key, datestring, details["m_title"], winning_team_id)
            except:
                "Error in InsertMatchRecord"
                continue

            if match_inserted == 1:
                for player in details["m_playerList"]:
                    try:
                        InsertPlayerRecord(conn, player["m_toon"]["m_id"], player["m_name"])
                        match_player_rel_id += 1
                        InsertMatchPlayerRelRecord(conn, match_player_rel_id, match_id, player["m_teamId"],
                                                   player["m_toon"]["m_id"], player["m_hero"])
                    except:
                        "Error in InsertPlayerRecord"
            # transactionally commit the match
            conn.commit()

        #break

def main():
    print "Starting main program"
    config = ConfigParser.RawConfigParser()
    config.read('heroes.ini')
    path = config.get('Replays', 'replays.path');
    conn = GetDBConnection(config)
    ProcessReplays(conn,path)

if __name__ == "__main__":
    main()




#        print data_string

#        # write the json file
#        with open('/Users/ds3161/parses/' + fn + ".json", 'w') as outfile:
#            json.dump(retval, outfile,skipkeys=False,ensure_ascii=False)


# ,"RawReplayTrackerEvents","RawReplayAttributesEvents","RawReplayGameEvents","RawReplayMessageEvents","RawTalentSelectionGameEvents"
