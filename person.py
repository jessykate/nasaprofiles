
import urllib, urllib2, hashlib
from settings import settings
try:
    import json
except:
    import simplejson as json

db = settings['db']

class Person(object):
    ''' An object to map information about a person into an object for
    display and manipulation. Allows us to retrieve profile field
    values easily for templates, falling back to sane (usually empty)
    values if not present. Also provides functions for retrieving
    gravatar info and editing user fields.'''
    def __init__(self, uid=None):
        ''' initialize either an empty Person object, or if uid is
        specified, populate it with the corresponding info from the
        database.'''
        self.uid = ''
        self.primary_name = ''
        self.all_names = []
        self.all_email = []
        self.primary_email = ''
        self.primary_phone = ''
        self.all_phones = []
        self.building = ''
        self.center = ''
        self.mail_stop = ''
        self.organization = ''
        self.employer = ''
        self.room_num = ''
        self.bio = ''
        self.tags = ''
        self.skills = ''
        self.hire_date = ''
        self.title = ''
        self.main_project_name = ''
        self.main_project_description = ''
        self.main_project_web = ''
        self.side_projects = ''
        self.personal_web = ''

        if uid:
            self._populate(db[uid].copy())

    def build(self, ldap_dict):
        ''' Build a Person object from information returned by x500
        ldap'''
        if settings['debug']:
            print 'debug:'
            print ldap_dict

        for field, values in ldap_dict.iteritems():
            if field == 'cn':
                for value in values:
                    self.all_names.append(value)

            if field == 'mail':
                for value in values:
                    self.all_email.append(value)

            if field == 'postalAddress':
                for value in values:
                    center, mail_stop = value.split('$')
                self.center = center.strip()
                self.mail_stop = mail_stop.strip()

            if field == 'roomNumber':
                # assumes there is only one list item for this
                # result. might turn out to be wrong.
                building, room = values[0].split(',')
                self.building = building[building.find(':')+1:].strip()
                self.room_num = room[room.find(':')+1:].strip()

            if field == 'telephoneNumber':
                for value in values:
                    self.all_phones.append(value)

            if field == 'uniqueIdentifier':
                self.uid = values[0]

            if field == 'userClass':
                # assumes there is only one list item for this
                # result. might turn out to be wrong.
                value = values[0]
                self.organization = value[value.find('Organization:')+14 : value.find(',')].strip()
                self.employer = value[value.find('Employer:')+10 : ].strip()

            if field == '':
                pass
            if field == '':
                pass
            if field == '':
                pass
            if field == '':
                pass
            if field == '':
                pass
            if field == '':
                pass

    def save(self):
        db[self.uid] = self.__dict__

    def _populate(self, user_dict):
        ''' Populate a Person object from the data store. user_dict
        should have every field defined already, since we only store
        objects that have been built by a Person this class, via the
        build() method. if for some reason it doesnt already exist, it
        WILL be created anyway. '''
        if settings['debug']:
            print '_populate() debug:'
            print user_dict

        for field, value in user_dict.iteritems():
            self.__dict__[field] = value

    def get(self, field, default=''):
        if field in self.__dict__:
            return self.__dict__[field]
        else: return default

    def set(self, field, value):
        self.__dict__[field] = value

    def gravatar(self, size=125):
        if self.primary_email:
            email = self.primary_email
        elif self.all_email:
            email = self.all_email[0]
        else:
            email = 'noone@opennasa.com'
        base = "http://www.gravatar.com/avatar.php?"
        return base+urllib.urlencode({'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                                      'size':str(size)})

    def display_name(self):
        if self.primary_name:
            return self.primary_name
        else:
            return self.all_names[0]
