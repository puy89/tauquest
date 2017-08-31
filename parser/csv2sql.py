import sys
from db.entities import db_session, engine, Base
from db.sqlite_executor import SqliteDB

import courses_parser
import alphon_parser

reload(sys)
sys.setdefaultencoding('utf8')


def main():
    # create all db objects
    session = db_session()
    Base.metadata.create_all(engine)
    sqlitedb = SqliteDB(session)

    lecturer_name_to_lecturer_dict = alphon_parser.parse_alphon()
    courses, lecturer_name_to_lecturer_dict = courses_parser.parse_courses(lecturer_name_to_lecturer_dict)

    for lecturer_name, lecturer in lecturer_name_to_lecturer_dict.iteritems():
        sqlitedb.add_lecturer(lecturer)

    for course in courses:
        sqlitedb.add_course(course)

    sqlitedb.commit()

if __name__ == '__main__':
    main()