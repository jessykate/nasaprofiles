
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
        self.primary_email = ''
        self.all_email = []
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
        self.category = ''
        self.main_project_name = ''
        self.main_project_description = ''
        self.main_project_web = ''
        self.side_projects = ''
        self.personal_web = ''
        self.twitter = ''
        self.facebook = ''
        # all the original values pulled from x500
        self.x500 = {}

        if uid:
            self._populate(db[uid].copy())

    def build(self, ldap_dict):
        ''' Build a Person object from information returned by x500
        ldap. each x500 field gets stored in two fields, one with an
        x500_ prefix, and one without.  '''
        if settings['debug']:
            print 'Person.build() debug:'
            print ldap_dict

        for field, values in ldap_dict.iteritems():
            if field == 'cn':
                self.x500['all_names'] = []
                for value in values:
                    self.x500['all_names'].append(value)

            if field == 'mail':
                self.x500['all_email'] = []
                for value in values:
                    self.x500['all_email'].append(value)

# different centers format this differently, of course :)
# Goddard: ['NASA ', ' Goddard Space Flight Center ', ' Mailstop 750.0 ', ' Greenbelt, MD 20771']
            if field == 'postalAddress':
                for value in values:
                    address = value.split('$')             
                    # strip whitespace
                    address = [a.strip() for a in address]
                    if 'NASA' in address:
                        address.remove('NASA')
                    if 'nasa' in address:
                        address.remove('nasa')
                    self.x500['center'] = address[0].strip()
                    if len(address) > 1:
                        self.x500['mail_stop'] = address[1].strip()
                    if len(address) > 2:
                        print '*** Warning: some values from Postal Address Field were missed.'
                        print 'Raw value of postal address field:'
                        print str(address)


            if field == 'roomNumber':
                # assumes there is only one list item for this
                # result. might turn out to be wrong.
                location = values[0].split(',')
                self.x500['building'] = location[0][location[0].find(':')+1:].strip()
                if len(location) > 1:
                    self.x500['room_num'] = location[1][location[1].find(':')+1:].strip()
                if len(location) > 2:
                        print '*** Warning: some values from Room Number field were missed.'
                        print 'Raw value of room number field:'
                        print str(location)

                    

            if field == 'telephoneNumber':
                self.x500['all_phones'] = []
                for value in values:
                    self.x500['all_phones'].append(value)


            # both are inconsistently used, of course :)
            if field == 'uniqueIdentifier':
                self.uid = values[0]
            elif field == 'uid':
                self.uid = values[0]

            if field == 'userClass':
                # assumes there is only one list item for this
                # result. might turn out to be wrong.
                value = values[0]
                self.x500['organization'] = value[value.find('Organization:')+14 : value.find(',')].strip()
                self.x500['employer'] = value[value.find('Employer:')+10 : ].strip()

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
        ''' save or update a person object '''
        if not self.uid:
            print 'Error: UID is empty. Cannot save new user data.'
            return
        if self.uid not in db:
            try:
                db[self.uid] = self.__dict__
            except:
                pass
        else:
            person = db[self.uid]
            for field, value in self.__dict__.iteritems():
                if field == 'x500':
                    continue
                # couch will automatically convert non-string values
                # to json.
                person[field] = value
            db[self.uid] = person
    def _populate(self, user_dict):
        ''' Populate a Person object from the data store. '''
        if settings['debug']:
            print '_populate() debug:'
            print user_dict

        for field, value in user_dict.iteritems():
            self.__dict__[field] = value

    def get(self, field, default=''):
        ''' Return the value of field, first looking for a locally
        modified version, and returning the original x500 version
        otherwise. If the field doesnt exist, return the value of
        default instead.'''
        if field in self.__dict__ and self.__dict__[field]:
            return self.__dict__[field]
        elif field in self.__dict__['x500']:
            return self.__dict__['x500'][field]
        else: return default

    def set(self, field, value):
        if field.find('x500') >= 0:
            print 'Error: You cannot overwrite an x500 field. Skipping request to update %s = %s' % (field, value)
            return
        self.__dict__[field] = value

    def gravatar(self, size=125):
        email = self.email()
        if not email:
            email = 'noone@opennasa.com'
        base = "http://www.gravatar.com/avatar.php?"
        return base+urllib.urlencode({'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                                      'size':str(size)})

    def display_name(self):
        if self.primary_name:
            return self.primary_name
        else:
            names = self.get('all_names')
            if names:
                return names[0]
            else: return '<< Name Missing >>'

    def phone(self):
        if self.primary_phone:
            return self.primary_phone
        else:
            names = self.get('all_phones')
            if names:
                return names[0]
            else: return ''

    def email(self):
        ''' get the user's primary email if they have set one,
        otherwise grab the first email in their profile, or return an
        empty string if the user has no emails'''
        if self.primary_email:
            return self.primary_email
        else:
            emails = self.get('all_email')
            if emails:
                return emails[0]
            else: return ''
