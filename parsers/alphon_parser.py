import csv
import re
from entities.lecturer import Lecturer

from parsers.honor import honor_heb2en

site_pattern = re.compile('<a href="(.+?)">(.+?)</a>')
alph_cols = ['hebrew_name', 'title', 'phone', 'fax', 'email', 'name', 'office']

alpg_title2idx = {t: i for i, t in enumerate(alph_cols)}


def parse_alphon():
    lecturer_name_to_lecturers = dict()

    with open('alphon.csv') as alphon_file:
        alphon_rows = csv.reader(alphon_file)
        for alphon_row in alphon_rows:
            cell = alphon_row[alpg_title2idx['hebrew_name']]
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
            lecturer = lecturer_name_to_lecturers.get(lecturer_name)
            if lecturer is None:
                lecturer = Lecturer(id=lecturer_name,
                                    hebrew_name=lecturer_name,
                                    name=unicode(alphon_row[alpg_title2idx['name']]),
                                    title=unicode(alphon_row[alpg_title2idx['title']]),
                                    phone=unicode(alphon_row[alpg_title2idx['phone']]),
                                    fax=unicode(alphon_row[alpg_title2idx['fax']]),
                                    email=unicode(alphon_row[alpg_title2idx['email']]),
                                    honor=honor)
                lecturer_name_to_lecturers[lecturer_name] = lecturer

    return lecturer_name_to_lecturers
