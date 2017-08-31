import sys
from db.db import DBSession, engine, Base
from db.sqlite_executor import SqliteExecutor

import courses_parser
import alphon_parser

reload(sys)
sys.setdefaultencoding('utf8')


session = DBSession()
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)

sqlitedb = SqliteExecutor(session)

lecturer_name_to_lecturer_dict = alphon_parser.parse_alphon()
courses, lecturer_name_to_lecturer_dict = courses_parser.parse_courses(lecturer_name_to_lecturer_dict)

for lecturer_name, lecturer in lecturer_name_to_lecturer_dict.iteritems():
    sqlitedb.add_lecturer(lecturer)

for course in courses:
    sqlitedb.add_course(course)

sqlitedb.commit()