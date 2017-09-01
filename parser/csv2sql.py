import sys
from db.db import db_instance
from db.sqlite_executor import SqliteDB

import courses_parser
import alphon_parser

reload(sys)
sys.setdefaultencoding('utf8')


def main():
    # create all db objects
    session = db_instance.session
    db_instance._base.metadata.create_all(db_instance.engine)
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