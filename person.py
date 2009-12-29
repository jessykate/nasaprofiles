
import urllib, urllib2, hashlib
from datetime import datetime
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
        # string formatted timestamp of when this revision of this
        # record was saved. format: '%Y-%m-%dT%H:%M:%S'
        self.edited = '' 
        # a flag that gets set to true if a user edits their profile 
        self.customized = False
        self.primary_name = ''
        self.primary_email = ''
        self.primary_phone = ''
        self.all_names = []
        self.all_email = []
        self.all_phones = []
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
        # self.opennasa_only --> set only when this is a custom local
        # profile NOT based on x500 info.

        # all the original values pulled from x500
        self.x500 = {}
        # x500 info we may want to let people customize in a future
        # release
        #self.building = ''
        #self.center = ''
        #self.mail_stop = ''
        #self.organization = ''
        #self.employer = ''
        #self.room_num = ''

        # if a uid was passed it, then populate it with an existing
        # record.
        if uid:
            self._populate(db[uid].copy())

    def build(self, ldap_dict):
        ''' Build a Person object from information returned by x500
        ldap. '''
        
        # there are two categories of fileds in the ldap results:
        # those that are part of our standard repertoire, and those
        # that are random other fields. we handle both, parsing the
        # former carefully, and renaming their key values to something
        # more intuitive, and storing the additional fields unchanged.
        for field, values in ldap_dict.iteritems():
            print 'now processing:'
            print '(%s, %s)' % (field, values)

            # regarding uniqueIdentifier and uid: both are
            # inconsistently used, and some records have both. we
            # always use uniqueIdentifier if it exists. this is a
            # little messy, since python dicts are not ordered, so we
            # have no guarantee uniqueIdentifier will be seen
            # first. if we're not consistent, duplicate records with
            # different keys will get created and messes will
            # ensue. blah.
            if field == 'uid' and 'uniqueIdentifier' not in ldap_dict:
                print 'found uid instead of uniqueIdentifier. adding record with key = %s' % values[0]
                self.uid = values[0]
                
            elif field == 'uniqueIdentifier':
                print 'found uniqueIdentifier. adding record with key = %s' % values[0]
                self.uid = values[0]

            elif field == 'cn' or field == 'jplalias':
                # store the canonical copy under x500 info and our own
                # copy in all_names field.
                if not 'all_names' in self.x500:
                    self.x500['all_names'] = []
                for value in values:
                    self.x500['all_names'].append(value)                    
                    self.all_names.append(value)

            elif field == 'mail':
                self.x500['all_email'] = []
                for value in values:
                    self.x500['all_email'].append(value)
                    self.all_email.append(value)

            # different centers format this differently, of course :)
            # Goddard: ['NASA ', ' Goddard Space Flight Center ', ' Mailstop 750.0 ', ' Greenbelt, MD 20771']
            # Headquarters: ['NASA Headquarters', '300 E ST SW', 'Washington DC 20546-0001']
            # Ames: ['NASA Ames Research Center', 'MS 269-3']
            # JPL: ['4800 Oak Grove Drive', ' M/S 180-904 ', ' Pasadena, CA 91109']

            # general parsing principle: once we remove the 'NASA'
            # list item, if it exists, then:
            # list[0] = center name
            # list[1] = mail stop
            # list[2], if if it exists, is the street address. 
            elif field == 'postalAddress':
                address = values[0].split('$')             
                address = [a.strip() for a in address]
                if len(address) == 3 and address[2].find('Pasadena') >= 0:
                    # this is JPL
                    self.x500['center'] = 'Jet Propulsion Laboratory'
                    self.x500['mail_stop'] = address[1].strip()
                    self.x500['street_address'] = address[0].strip()

                else:
                    if 'nasa' in address:
                        address.remove('nasa')
                    if 'NASA' in address:
                        address.remove('NASA')
                    self.x500['center'] = address[0].strip()
                    if len(address) > 1:
                        self.x500['mail_stop'] = address[1].strip()
                    if len(address) > 2:
                        self.x500['street_address'] = address[2].strip()
                    if len(address) > 3:
                        print '*** Warning: some values from Postal Address Field were missed.'
                        print 'Raw value of postal address field:'
                        print str(address)

            elif field == 'roomNumber':
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

            elif field == 'telephoneNumber':
                if not 'all_phones' in self.x500:
                    self.x500['all_phones'] = []
                for value in values:
                    # since telephoneNumber is most likely to be the
                    # user's main phone number, we always insert it as
                    # the first record.
                    self.x500['all_phones'].insert(0,value)
                    self.all_phones.insert(0,value)

            elif field == 'pager':
                if not 'all_phones' in self.x500:
                    self.x500['all_phones'] = []
                for value in values:
                    self.x500['all_phones'].append(value)
                    self.all_phones.append(value) 

            # 'fascimileTelephoneNumber.' awesome. 
            elif field == 'facsimileTelephoneNumber':            
                self.x500['fax'] = []
                for value in values:
                    self.x500['fax'].append(value)
                

            elif field == 'userClass':
                # assumes there is only one list item for this
                # result. might turn out to be wrong.
                value = values[0]
                self.x500['organization'] = value[value.find('Organization:')+14 : value.find(',')].strip()
                self.x500['employer'] = value[value.find('Employer:')+10 : ].strip()

            # this is typical of JPL records. jpldepartmentname is
            # sort of like their "Code"
            elif field == 'jpldepartmentname' and 'userClass' not in ldap_dict: 
                self.x500['organization'] = values[0]

            elif field == 'jplemployer' and 'userClass' not in ldap_dict: 
                self.x500['employer'] = values[0]

            # some glenn records at least have their own title field. 
            elif field == 'title':
                self.x500['title'] = values[0]
                self.title = values[0]

            else:
                # whatever is leftover, store it too
                self.x500[field] = values

    def save(self):
        ''' save or update a person object '''
        if not self.uid:
            print 'Error: UID is empty. Cannot save new user data.'
            return

        # always include a timestamp. use a javascript-compatible
        # format, so that we can manipulate and order by dates easily
        # in couch views (which uses javascript for its view
        # functions).
        # eg: "Mon, 25 Dec 2009 13:30:00 PST"
        timestamp = datetime.now().strftime('%a, %d %b %Y %H:%M:%S PST')
        self.edited = timestamp

        # if there's no uid, then it's a new record
        if self.uid not in db:
            try:
                print 'saving new record with uid = %s' % self.uid
                db[self.uid] = self.__dict__
            except:
                print 'Error: self.uid = %s was not in db, but getting error on attempting to add' % (self.uid)
                return 

        # else, we're updating an existing record
        else:
            self.customized = True
            person = db[self.uid]            
            for field, value in self.__dict__.iteritems():
                # Don't EVER overwrite the x500 fields. they are the
                # canonical reference.
                if field == 'x500':
                    continue
                # couch will automatically convert non-string values
                # for simple objects into json. 
                person[field] = value
            db[self.uid] = person

    def _populate(self, user_dict):
        ''' Populate a Person object from the data store. '''
        if settings['debug']:
            print '_populate: Populating person object from data store with the following info:'
            print user_dict

        for field, value in user_dict.iteritems():
            self.__dict__[field] = value

    def get(self, field, max_results=None, default=''):
        ''' Return the value of field, first looking for a local
        version, then looking in the x500 values. If the field doesnt
        exist at all, return the value of default instead. If
        max_results is set, slice the result set so that it has no
        more than max_results. useful for limiting a list of items to
        a single string.'''
        if field in self.__dict__ and self.__dict__[field]:
            result = self.__dict__[field]
        elif field in self.__dict__['x500']:
            result = self.__dict__['x500'][field]
        else: 
            result = default

        if max_results == 1:
            # if it's just one, return it as a string
            return result[0]
        elif max_results:
            return result[:max_results]
        else:
            return result

    def set(self, field, value):
        if field.find('x500') >= 0:
            print 'Error: You cannot overwrite an x500 field. Skipping request to update %s = %s' % (field, value)
            return
        self.__dict__[field] = value

    def add(self, field, value):
        '''Add an item to a list-based attribute'''
        if not isinstance(self.__dict__[field], list):
            print 'Error in Person.add(): %s is not a list attribute.' % field
            return
        self.__dict__[field].append(value)

    def gravatar(self, size=125):
        email = self.email()       
        if not email:
            email = 'noone@opennasa.com'

        site_base = 'http://'+settings['domain']
        if settings['port'] != 80:
            site_base += ':'+str(settings['port'])
        default_img = site_base + settings['default_gravatar'][size]

        gravatar_base = "http://www.gravatar.com/avatar.php?"
        return gravatar_base+urllib.urlencode({'gravatar_id':hashlib.md5(email.lower()).hexdigest(),
                                               'size':str(size), 'd':default_img})

    def display_name(self):
        if self.primary_name:
            return self.primary_name
        else: 
            names = self.get('all_names')
            if names:
                return names[0]
        return '<< Name Missing >>'

    def phone(self):
        if self.primary_phone:
            return self.primary_phone
        else: 
            phones = self.get('all_phones')
            if phones:
                return phones[0]
        return ''

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
        return ''
