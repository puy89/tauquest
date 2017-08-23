import csv
import os
import sys
import re
from db import Base, Course, Lecturer, engine, DBSession

site_pattern = re.compile('<a href="(.+?)">(.+?)</a>')
 
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)

MR = u'\u05de\u05e8'
MS = u"\u05d2\u05d1'"
PROF = u'\u05e4\u05e8\u05d5\u05e4'
PROFQ = u"\u05e4\u05e8\u05d5\u05e4'"
DR = u'\u05d3"\u05e8'
GVERET = u'\u05d2\u05d1\u05e8\u05ea'

honor_heb2en = {MR: 'Mr.',
                MS: 'Ms.',
                GVERET: 'Ms.',
               PROF: 'Prof',
               PROFQ: 'Prof',
               DR: 'Dr'}

def_cols = ['hebrew_name', 'name', 'course_id', 'departure', 'semester', 'time', 'day', 'place', 'building', 'kind', 'lecturer']
alph_cols = ['hebrew_name', 'title', 'phone', 'fax', 'email', 'name', 'office']

title2idx = {t: i  for i, t in enumerate(def_cols)}
alpg_title2idx = {t: i  for i, t in enumerate(alph_cols)}

forbidden_chars = list(',.?-;"\'()!+') + ['&amp']

def clear_name(s):
    s = s.replace('_')
    for c in forbidden_chars:
        s = s.replace(c, '_')
    return s
s = DBSession()
f = open('alphon.csv')
r = csv.reader(f)
n_f = open('names', 'w')
lecturers = {}
for row in r:
    cell = row[alpg_title2idx['hebrew_name']]
    match = site_pattern.findall(cell)
    if match:
        (site, cell), = match
        cell = cell.replace('&#039;', '')
        cell = cell.replace('&quot;', '"')
        cell = cell.replace('-', ' ')
    lecturer_name = unicode(cell)
    words = lecturer_name.split()
    honor = honor_heb2en.get(words[0])
    if honor is not None:
        lecturer_name = ' '.join(words[1:])
    lecturer = lecturers.get(lecturer_name)
    print >> n_f, lecturer_name
    if lecturer is None:
        lecturer = Lecturer(id=lecturer_name, hebrew_name=lecturer_name,
                            name=unicode(row[alpg_title2idx['name']]),
                           title=unicode(row[alpg_title2idx['title']]), 
                           phone=unicode(row[alpg_title2idx['phone']]),
                           fax=unicode(row[alpg_title2idx['fax']]), email=unicode(row[alpg_title2idx['email']]),
                           honor=honor)
        lecturers[lecturer_name] = lecturer
        s.add(lecturer)
s.commit()
f.close()
n_f.close()

f = open('courses.csv')
r = csv.reader(f)

for row in r:
    t = row[title2idx['time']].split('-')
    if len(t) == 2:
        end_time, start_time = t
    else:
        start_time = end_time = -1
    if len(row[title2idx['day']]):
        day = ord(row[title2idx['day']][1]) - 0x90
    else:
        day = -1
    words = unicode(row[title2idx['lecturer']].lstrip().rstrip().replace('-', ' ')).split(' ')
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
            s.add(lecturer)
    elif lecturer.honor is None:
        lecturer.honor = honor
    course = Course(id=int(row[title2idx['course_id']].replace('-', '')),
                    name=row[title2idx['name']],
                    hebrew_name=unicode(row[title2idx['hebrew_name']]),
                    departure=unicode(row[title2idx['departure']]),
                    semester=ord(row[title2idx['semester']][1])-0x90,
                    start_time=int(start_time),
                    end_time=int(end_time),
                    day=day,
                    place=unicode(row[title2idx['place']]),
                    building=unicode(row[title2idx['building']]),
                    kind=unicode(row[title2idx['kind']]),
                    lecturer=lecturer)
    s.add(course)
s.commit()
f.close()