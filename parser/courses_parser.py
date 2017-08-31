import csv
import cPickle
from db.db import Lecturer, Course
from honor import honor_heb2en

courses_columns = ['hebrew_name', 'name', 'course_id', 'departure', 'semester', 'time', 'day', 'place', 'building', 'kind', 'lecturer']
title2idx = {t: i  for i, t in enumerate(courses_columns)}

with open('files/kind_he2en.pkl', 'rb') as f:
    kind_heb2en = cPickle.load(f)

with open('files/departure_he2en.pkl', 'rb') as f:
    departure_heb2en = cPickle.load(f)

def parse_courses(lecturers):
    courses = list()

    with open('files/courses.csv') as courses_file:
        courses_rows = csv.reader(courses_file)

        for course_row in courses_rows:
            course_time = course_row[title2idx['time']].split('-')
            if len(course_time) == 2:
                end_time, start_time = course_time
            else:
                start_time = end_time = -1

            if len(course_row[title2idx['day']]):
                course_day = ord(course_row[title2idx['day']][1]) - 0x90
            else:
                course_day = -1

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
                            departure=unicode(departure_heb2en[unicode(course_row[title2idx['departure']])]),
                            semester=ord(course_row[title2idx['semester']][1])-0x90,
                            start_time=int(start_time),
                            end_time=int(end_time),
                            day=course_day,
                            place=unicode(course_row[title2idx['place']]),
                            building=unicode(course_row[title2idx['building']]),
                            kind=unicode(kind_heb2en[unicode(course_row[title2idx['kind']])]),
                            lecturer=lecturer)

            courses.append(course)
    return courses, lecturers