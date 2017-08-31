import csv
import re
from db.db import Lecturer
from honor import honor_heb2en

site_pattern = re.compile('<a href="(.+?)">(.+?)</a>')
alphon_columns = ['hebrew_name', 'title', 'phone', 'fax', 'email', 'name', 'office']
alpg_title2idx = {t: i for i, t in enumerate(alphon_columns)}

forbidden_chars = list(',.?-;"\'()!+') + ['&amp']


def parse_alphon():
    lecturers = dict()
    with open('files/alphon.csv') as alphon_file:
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
            lecturer = lecturers.get(lecturer_name)
            if lecturer is None:
                lecturer = Lecturer(id=lecturer_name, hebrew_name=lecturer_name,
                                    name=unicode(alphon_row[alpg_title2idx['name']]),
                                    title=unicode(alphon_row[alpg_title2idx['title']]),
                                    phone=unicode(alphon_row[alpg_title2idx['phone']]),
                                    fax=unicode(alphon_row[alpg_title2idx['fax']]),
                                    email=unicode(alphon_row[alpg_title2idx['email']]),
                                    honor=honor)
                lecturers[lecturer_name] = lecturer

    return lecturers