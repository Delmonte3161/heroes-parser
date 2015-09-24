__author__ = 'ds3161'

import json
import psycopg2
import ConfigParser
import datetime
import sys
import itertools


def get_comp_data(conn, game_type, player_list):
    cursor = conn.cursor()

    comps = get_comps(conn, player_list)
    for comp in comps:
        include_list = comp[0]
        exclude_list = comp[1]
        result = generate_query_string(include_list, exclude_list, game_type, 1)
        query = cursor.mogrify(result, (tuple(exclude_list),))
        cursor.execute(query)
        wins = cursor.fetchone()[0]
        print str(include_list) + " Wins: " + str()
        result = generate_query_string(include_list, exclude_list, game_type, 0)
        query = cursor.mogrify(result, (tuple(exclude_list),))
        cursor.execute(query)
        total = cursor.fetchone()[0]

        percent = 0;
        if total > 0:
            percent = (wins/total) * 100

        print str(include_list) + " Total: " + str(total) + " Wins: " + str(wins) + " Win rate: " + str(percent)


def generate_query_string(include_list, exclude_list, game_type, add_winning_team_clause):
    query = "SELECT count(distinct m.id) FROM match m "
    query += " JOIN match_player_rel mpr ON m.id = mpr.match_id "
    query += " JOIN player p ON p.id = mpr.player_id "
    if exclude_list.__len__() > 0:
        query += " WHERE NOT EXISTS (SELECT 1 FROM match_player_rel mpr, player p "
        query += " WHERE  mpr.match_id = m.id "
        query += " AND  mpr.player_id = p.id "
        query += " and p.name in %s) "
    else:
        query += " WHERE 1=1 "

    for name in include_list:
        query += " and exists (SELECT 1 FROM match_player_rel mpr, player p "
        query += " WHERE  mpr.match_id = m.id "
        query += " AND  mpr.player_id = p.id "
        if add_winning_team_clause == 1:
            query += " and m.winning_team_id = mpr.team_id "
        query += " and p.name = '"
        query += name
        query += "') "
    query += " and m.type = '"
    query += str(game_type)
    query += "' ;"
    return query


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


def get_comps(conn, player_list):
    comp_list = []
    for i in range(len(player_list)):
        result = itertools.combinations(player_list, i + 1)
        for j in result:
            include_list = set(j)
            exclude_list = set(player_list) - set(j)
            comp = [include_list, exclude_list]
            comp_list.append(comp)

    return comp_list


def main():
    print "Starting comp analysis"

    config = ConfigParser.RawConfigParser()
    config.read('heroes.ini')
    conn = get_db_connection(config)
    player_list = config.get('CompAnalysis', 'comp.player_list').split(',')
    game_type = config.get('CompAnalysis', 'comp.game_type')

    get_comp_data(conn, game_type, player_list)


if __name__ == "__main__":
    main()
