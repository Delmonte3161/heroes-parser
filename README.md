# heroes-parser
A Heroes of the Storm parser

# heroes.ini
This project will require a heroes.ini file in the root or the project.  It needs the following content:
[Database]
database.host=<host>
database.port=<5432 is postgres default>
database.dbname=heroes
database.user=<username, default is postgres>
database.password=<password, default is blank>

[Replays]
replays.path=<full path to directory containing replays to parse>

# local db setup
To set up a local postgres database, it's very simple:

yum install postgres
mkdir ~/PostgresDB
postgres -D ~/PostgresDB
createdb heroes

Then run a maven build on the project contained in the heroes-db subdirectory to create the schema:
mvn liquibase:update
