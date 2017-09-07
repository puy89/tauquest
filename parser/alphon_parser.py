import csv
import re
from db.entities import Lecturer, Phone
from honor import honor_heb2en
import cPickle

site_pattern = re.compile('<a href="(.+?)">(.+?)</a>')
alphon_columns = ['hebrew_name', 'title', 'phone', 'fax', 'email', 'name', 'office']
alpg_title2idx = {t: i for i, t in enumerate(alphon_columns)}

forbidden_chars = list(',.?-;"\'()!+') + ['&amp']

with open('files/names_he2en.pkl', 'rb') as f:
    names_heb2en = cPickle.load(f)

with open('files/site2office.pkl', 'rb') as f:
    site2office = cPickle.load(f)

with open('files/building_he2en.pkl', 'rb') as f:
    building_heb2en = cPickle.load(f)


def parse_alphon():
    lecturers = dict()
    with open('files/alphon.csv') as alphon_file:
        alphon_rows = csv.reader(alphon_file)
        for alphon_row in alphon_rows:
            site = None
            office_building = None
            office = None
            cell = alphon_row[alpg_title2idx['hebrew_name']]
            match = site_pattern.findall(cell)
            if match:
                (site, cell), = match
                cell = cell.replace('&#039;', '')
                cell = cell.replace('&quot;', '"')
                cell = cell.replace('-', ' ')
                office_building, office = site2office.get(site, (None, None))
                if office_building is not None:
                    office_building = building_heb2en[office_building]

            lecturer_name = unicode(cell)
            words = lecturer_name.split()
            honor = honor_heb2en.get(words[0])
            if honor is not None:
                lecturer_name = ' '.join(words[1:])
            lecturer = lecturers.get(lecturer_name)
            if lecturer is None:
                lecturer = Lecturer(hebrew_name=lecturer_name,
                                    site=site,
                                    name=unicode(alphon_row[alpg_title2idx['name']]),
                                    title=unicode(alphon_row[alpg_title2idx['title']]),
                                    fax=unicode(alphon_row[alpg_title2idx['fax']]),
                                    email=unicode(alphon_row[alpg_title2idx['email']]),
                                    honor=honor,
                                    office_building=office_building,
                                    office=office)

                phones_string = unicode(alphon_row[alpg_title2idx['phone']])
                phones = phones_string.replace('<div>', '').replace('</div>', ',').split(',')[:-1]
                for phone_string in phones:
                    phone = Phone(phone=phone_string,
                                  lecturer_id=lecturer_name)

                    lecturer.phones.append(phone)
                lecturers[lecturer_name] = lecturer
    return lecturers
