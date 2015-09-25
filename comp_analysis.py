import psycopg2
import ConfigParser
import datetime
import itertools
import decimal


def get_comp_data(conn, game_type, date_begin, date_end, player_list, exclude_players, min_game_threshold):
    retval = ''
    decimal.getcontext().prec = 3
    cursor = conn.cursor()

    comps = get_comps(conn, player_list)
    for comp in comps:
        include_list = comp[0]
        if exclude_players == 0:
            exclude_list = []
        else:
            exclude_list = comp[1]

        query = generate_query_string(cursor, include_list, exclude_list, date_begin, date_end, game_type, 1)
        cursor.execute(query)
        wins = cursor.fetchone()[0]

        query = generate_query_string(cursor, include_list, exclude_list, date_begin, date_end, game_type, 0)
        cursor.execute(query)
        total = cursor.fetchone()[0]

        percent = 0;
        if total > 0:
            percent = (decimal.Decimal(wins) / decimal.Decimal(total)) * 100

        if total >= min_game_threshold:
            retval += "\n" + get_comp_string(include_list) + ": Games (" + str(total) + ") " + str(wins) + "-" + str(
                total - wins) + " (" + str(percent) + "%)"

    return retval


def generate_query_string(cursor, include_list, exclude_list, date_begin, date_end, game_type, add_winning_team_clause):
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
    if len(game_type) > 0:
        query += " and m.type = '"
        query += str(game_type)
        query += "'"

    if date_begin is not None:
        query += " and m.date >= %s "

    if date_end is not None:
        query += " and m.date <= %s "

    if exclude_list.__len__() > 0:
        if date_begin is None and date_end is None:
            return cursor.mogrify(query, (tuple(exclude_list),))
        elif date_begin is None and date_end is not None:
            return cursor.mogrify(query, (tuple(exclude_list), date_end))
        elif date_end is None and date_begin is not None:
            return cursor.mogrify(query, (tuple(exclude_list), date_begin))
        else:
            return cursor.mogrify(query, (tuple(exclude_list), date_begin, date_end))
    else:
        if date_begin is None and date_end is None:
            return query
        elif date_begin is None and date_end is not None:
            return cursor.mogrify(query, (date_end,))
        elif date_end is None and date_begin is not None:
            return cursor.mogrify(query, (date_begin,))
        else:
            return cursor.mogrify(query, (date_begin, date_end))


def get_comp_string(player_list):
    display = ""
    count = 0
    for x in player_list:
        if count == 0:
            display += x
        else:
            display += ", " + x
        count += 1
    return display


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
        if i + 1 > 5:
            # don't do comps larger than 5 players
            break
        result = itertools.combinations(player_list, i + 1)
        for j in result:
            include_list = set(j)
            exclude_list = set(player_list) - set(j)
            comp = [include_list, exclude_list]
            comp_list.append(comp)
    return comp_list


def main():
    print "********* Starting composition analysis **********"

    config = ConfigParser.RawConfigParser()
    config.read('heroes.ini')
    conn = get_db_connection(config)
    player_list = config.get('CompAnalysis', 'comp.player_list').split(',')
    # game_type = config.get('CompAnalysis', 'comp.game_type')

    # date_begin = datetime.datetime.now() - datetime.timedelta(days=60)
    # date_end = datetime.datetime.now() - datetime.timedelta(days=30)
    date_begin = None
    date_end = None

    print "Begin date: " + str(date_begin)
    print "End date: " + str(date_end)

    print ' '
    print '*** Quick Match (w/exclusions) ***'
    print get_comp_data(conn, 'Quick Match', date_begin, date_end, player_list, 1, 1)
    print ' '
    print '*** Hero League (w/exclusions) ***'
    print get_comp_data(conn, 'Hero League', date_begin, date_end, player_list, 1, 1)
    print ' '
    print '*** All Game Types (w/exclusions) ***'
    print get_comp_data(conn, '', date_begin, date_end, player_list, 1, 1)
    print ' '
    print '*** Quick Match ***'
    print get_comp_data(conn, 'Quick Match', date_begin, date_end, player_list, 0, 1)
    print ' '
    print '*** Hero League ***'
    print get_comp_data(conn, 'Hero League', date_begin, date_end, player_list, 0, 1)
    print ' '
    print '*** All Game Types ***'
    print get_comp_data(conn, '', date_begin, date_end, player_list, 0, 1)


if __name__ == "__main__":
    main()
