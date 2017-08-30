import uuid

from neo4j.v1 import GraphDatabase


class Neo4j:

    def __init__(self):
        self._driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "1qazZAQ!"))
        self._session = self._driver.session()

    def add_lecturer(self, name, hebrew_name):
        self._session.run("CREATE (a:Lecturer {id: {id}, name: {name}, hebrew_name: {hebrew_name}})",
                          {"id": uuid.uuid4(), "name": name, 'hebrew_name': hebrew_name})

    def add_course(self, name, hebrew_name, lecturer_id):
        course_id = uuid.uuid4()
        self._session.run("CREATE (a:Course {id: {id}, name: {name}, hebrew_name: {hebrew_name}})",
                          {"id": course_id, "name": name, 'hebrew_name': hebrew_name})

        self._session.run(
            "MATCH (u:Lecturer {id: {lecturer_id}}), (r:Course {id: {course_id}}) CREATE (u)-[:Teaches]->(r)",
            {"lecturer_id": lecturer_id, 'course_id': course_id})
