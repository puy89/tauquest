class SqliteDB():

    def __init__(self, session):
        self._session = session

    def add_lecturer(self, lecturer):
        self._session.add(lecturer)

    def add_course(self, course):
        self._session.add(course)

    def add_multi_course(self, multi_course):
        self._session.add(multi_course)

    def commit(self):
        self._session.commit()


