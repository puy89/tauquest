from neo4j.v1 import GraphDatabase, basic_auth


class Neo4jDB:

    def __init__(self):
        self._driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "1qazZAQ!"))

    def add_lecturers(self, lecturers):

        # divide to bulks
        bulks = list()
        bulk_index = 0
        bulk = list()
        for lecturer_name, lecturer in lecturers.iteritems():
            if lecturer.name is None or lecturer.hebrew_name is None:
                continue
            if bulk_index == 1000:
                bulks.append(bulk)
                bulk_index = 0
                continue
            bulk.append(lecturer)
            bulk_index += 1

        with self._driver.session() as session:
            for bulk in bulks:
                with session.begin_transaction() as tx:
                    for lecturer in bulk:
                        tx.run("MERGE (a:Lecturer {name: {name}, hebrew_name: {hebrew_name}})",
                              {"name": lecturer.name, 'hebrew_name': lecturer.hebrew_name})


    def add_lecturer(self, lecturer):
        if lecturer.name is None or lecturer.hebrew_name is None:
            return;
        with self._driver.session() as session:
            session.run("MERGE (a:Lecturer {name: {name}, hebrew_name: {hebrew_name}})",
                          {"name": lecturer.name, 'hebrew_name': lecturer.hebrew_name})

    def add_course(self, course, lecturer):
        with self._driver.session() as session:
            session.run("MERGE (a:Course {name: {name}, hebrew_name: {hebrew_name}})",
                              {"name": course.name, 'hebrew_name': course.hebrew_name})

            session.run(
                "MATCH (u:Lecturer {name: {lecturer_name}}), (r:Course {name: {course_name}}) CREATE (u)-[:Teaches]->(r)",
                {"lecturer_name": lecturer.name, 'course_name': course.name})
