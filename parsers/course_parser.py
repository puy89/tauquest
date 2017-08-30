import csv
from entities.course import Course
from entities.lecturer import Lecturer

from parsers.honor import honor_heb2en

def_cols = ['hebrew_name', 'name', 'course_id', 'departure', 'semester', 'time', 'day', 'place', 'building', 'kind',
            'lecturer']

title2idx = {t: i for i, t in enumerate(def_cols)}


def parse_courses(lecturers=dict()):
    course_to_lecturers = dict()

    with open('courses.csv') as courses_file:
        courses_rows = csv.reader(courses_file)

        for course_row in courses_rows:
            t = course_row[title2idx['time']].split('-')
            if len(t) == 2:
                end_time, start_time = t
            else:
                start_time = end_time = -1
            if len(course_row[title2idx['day']]):
                day = ord(course_row[title2idx['day']][1]) - 0x90
            else:
                day = -1
            words = unicode(course_row[title2idx['lecturer']].lstrip().rstrip().replace('-', ' ')).split(' ')
            honor = honor_heb2en.get(words[0])
            if honor is None:
                lecturer_name = unicode(' '.join(words[-1:] + words[:-1]))
            else:
                lecturer_name = unicode(' '.join(words[-1:] + words[1:-1]))
            lecturer = lecturers.get(lecturer_name)
            if lecturer is None:
                if lecturer_name.rstrip():
                    lecturer = Lecturer(id=lecturer_name, hebrew_name=lecturer_name, honor=honor)
                    lecturers[lecturer_name] = lecturer
            elif lecturer.honor is None:
                lecturer.honor = honor
            course = Course(id=int(course_row[title2idx['course_id']].replace('-', '')),
                            name=course_row[title2idx['name']],
                            hebrew_name=unicode(course_row[title2idx['hebrew_name']]),
                            hebrew_departure=unicode(course_row[title2idx['departure']]),
                            departure="",  # unicode(departure_heb2en[unicode(course_row[title2idx['departure']])]),
                            semester=ord(course_row[title2idx['semester']][1]) - 0x90,
                            start_time=int(start_time),
                            end_time=int(end_time),
                            day=day,
                            place=unicode(course_row[title2idx['place']]),
                            building=unicode(course_row[title2idx['building']]),
                            kind=unicode(course_row[title2idx['kind']]),
                            lecturer=lecturer)
            course_to_lecturers[course] = lecturer
    return course_to_lecturers
