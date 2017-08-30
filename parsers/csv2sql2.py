import sys

from parsers.alphon_parser import parse_alphon
from course_parser import parse_courses
from db.neo4jdb import Neo4jDB

reload(sys)
sys.setdefaultencoding('utf8')

neo4jdb = Neo4jDB()

print("parsing alphon")
lecturers = parse_alphon()

print("adding lecturers to the db")
for lecturer_name, lecturer in lecturers.iteritems():
    neo4jdb.add_lecturer(lecturer)

print("parsing courses")
courses_to_lecturers_map = parse_courses(lecturers)

print("adding courses to the db")
for course, lecturer in courses_to_lecturers_map.iteritems():
    if lecturer is not None:
        neo4jdb.add_lecturer(lecturer)
        neo4jdb.add_course(course, lecturer)