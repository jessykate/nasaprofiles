#!/usr/bin/python

import urllib2, urllib, re, time, hashlib, uuid, helper
import smtplib, os, ldap
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import json
except:
    import simplejson as json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
from database import Database
from person import Person
from settings import settings


class TemplateBase(tornado.template.Template):
    def generate(self, **kwargs):
        ''' this function gets called for all templates to make each
        of the kwargs available as variables to the rendered
        template. Override the function to customize the default
        variables available to *all* templates. '''
        namespace = {
            'recent_gravatars' : recent_gravatars, 
            'top_skills' :_top_skills,
            'num_customized' : num_customized,
            'top_tags' :_top_tags, 
            'categories' : categories,
            }
        namespace.update(kwargs)
        super(TemplateBase, self).generate(namespace)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("uid")

class PersonHandler(BaseHandler):
    def get(self, uid): 
        db = settings['db']
        try:
            person = Person(uid)
            self.render('templates/person.html', title=person.display_name(), 
                        person=person, map=helper.map, mailing=helper.mailing, 
                        category=helper.category, category_sm=helper.category_sm)
        except:
            user_message = "There is no profile with that ID. Please try again."
            self.render('templates/results.html', title='Search Results', results=None, message=user_message)

class EditRequestHandler(BaseHandler):
    def get(self, uid):
        if self.current_user and self.current_user == uid:
            self.redirect('/edit')
            return
        db = settings['db']
        # generate a one-time hash. these are stored in the database
        # as uuid --> uid key-value pairs, so that the uuid is an
        # index which returns the uid which the user is logging into
        # as.
        if not 'edit_requests' in db:
            db['edit_requests'] = {}
        edit_requests = db['edit_requests']
        onetime_uuid = str(uuid.uuid4())
        edit_requests[onetime_uuid] = uid
        db['edit_requests'] = edit_requests
        user = Person(uid)
        email = user.email()
        if not email:
            message = "This user does not have any email addresses, so we cannot verify your identity. You should update your official x500 information. If this isn't possible, email people@opennasa.com and we can help you work it out."
            self.render('templates/email_notify.html', message=message)
            return

        # construct and send the email
        base = 'http://'+settings['domain']
        if settings['port'] != 80:
            base += ':'+str(settings['port'])
        edit_url = base+'/login/'+onetime_uuid
        text = '''Please click the following link to update your information:\n%s''' % edit_url
        html = '''<html><p>Welcome! People.openNASA is the open
        extension to the NASA x500 system. We hope that you will find
        this a useful way to share information about your skills, work
        and interests. If you have any trouble or questions, check out
        the <a href="http://people.opennasa.com/faq">FAQ</a>, or email
        us at <a href="mailto:people@opennasa.com">
        people@opennasa.com</a>.</p> <p>Happy collaborating!</p>'''
        html += '''<p>Follow this link to update your information:<br><a href="%s">%s</a></p></html>''' % (edit_url, edit_url)
        part1 = MIMEText(text, 'text')
        part2 = MIMEText(html, 'html')
        msg = MIMEMultipart('alternative')
        msg.attach(part1)
        msg.attach(part2)
        msg['Subject'] = '[openNASA Profiles] Update your Information'
        msg['From'] = 'people@opennasa.com'
        msg['To'] = email
        if settings['email_enabled']:
            s = smtplib.SMTP('smtp.gmail.com')
            s.starttls()
            s.login(settings['smtp_user'], settings['smtp_pass'] )
            s.sendmail(msg['From'], msg['To'], msg.as_string())
            s.quit()
            message = 'An email with one-time login has been sent to your email address at %s. (You can change your primary email address when you log in to edit your profile)' % email
            print 'One-time login sent'
        elif settings['debug']:
            # careful with this! it will allow anyone to log into any
            # profile to edit its fields.
            message = 'Click <a href="%s">here</a> to log in.' % edit_url
        self.render('templates/email_notify.html', message=message)
        return

class LoginHandler(BaseHandler):
    def get(self, uuid):
        ''' check the uuid and compare it against active edit_requests
        in the data store.'''
        db = settings['db']
        edit_requests = db['edit_requests']
        if uuid in edit_requests:
            uid = edit_requests[uuid]
            self.set_secure_cookie("uid", uid)
            # remove this edit request so it can't be used again
            edit_requests.pop(uuid)
            db['edit_requests'] = edit_requests
            print 'Expired cookie for one-time login %s' % uuid
            self.redirect('/edit')
            return
        else:
            self.write('Invalid/Expired')

class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.clear_cookie("uid")
        self.redirect('/')

class EditHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        #if not self.get_argument('submitted', None):
        db = settings['db']
        uid = self.get_current_user()
        person = Person(uid)
        self.render('templates/profile_edit.html', person=person)

    def post(self):
        new_values = self.request.arguments

        if settings['debug']:
            print 'The user submitted the following new values for their profile:'
            print new_values

        uid = self.get_current_user()
        person = Person(uid)

        custom_email_flag = False
        custom_name_flag = False
        custom_phone_flag = False
        for field, value in new_values.iteritems():            

            field = field.strip()
            # the values returned by the form are lists by
            # default. all OUR custom fields are strings, so
            # this is easy-- if they weren't this would have
            # to be a bit more nuanced. 
            value = value[0].strip()
            # force into unicode, dropping non-unicode characters. 
            value = unicode(value, errors='ignore')

            if field == 'submitted' or field == 'x500':
                continue
            elif field == 'custom_name' and (value == 'custom...' or value == ''):
                continue
            elif field == 'custom_email' and (value == 'custom...' or value == ''):
                continue
            elif field == 'custom_phone' and (value == 'custom...' or value == ''):
                continue

            elif field == 'custom_phone':
                print 'settings custom value %s = %s' % (field, value)
                person.add('all_phones', value)
                person.primary_phone = value
                custom_phone_flag = True

            elif field == 'custom_email':
                print 'settings custom value %s = %s' % (field, value)
                person.add('all_email', value)
                person.primary_email = value
                custom_email_flag = True

            elif field == 'custom_name':
                print 'settings custom value %s = %s' % (field, value)
                person.add('all_names', value)
                person.primary_name = value
                custom_name_flag = True

            # dont override custom fields if they've been set
            # elsewhere in this form.
            elif field == 'primary_email' and custom_email_flag:
                continue
            elif field == 'primary_name' and custom_name_flag:
                continue
            elif field == 'primary_phone' and custom_phone_flag:
                continue

            # store tags and skills as lists
            elif field == 'tags' or field == 'skills':
                values = value.split(',')
                values = [v.strip() for v in values]
                person.set(field, values)

            # make sure we have WWW urls
            elif field == 'personal_web' or field == 'main_project_web':
                if not value.startswith('http://'):
                    value = 'http://'+value
                person.set(field, value)

            # for all other fields, if it wasnt empty, then store
            # the new value.
            elif value:
                print 'settings new value %s = %s' % (field, value)
                person.set(field, value)

        person.save()
        self.redirect('/person/'+uid)

class CreateRequestHandler(BaseHandler):
    def get(self):
        message = None
        email = self.get_argument("email", None)
        # check if the form has been submitted yet 
        if not email: 
            self.render('templates/create_request.html', message=message)
            return
        # else-- process their request. check to make sure this is a
        # nasa email by looking for the word nasa in the domain part
        # of the address.
        try:
            name, domain = email.split('@')
        except:
            message = 'Invalid email address. Please try again.'
            self.render('templates/create_request.html', message=message)
            return
        if domain.lower().find('nasa') < 0:
            message = 'You must enter a NASA email address. Please try again.'
            self.render('templates/create_request.html', message=message)
            return
        # double check that a profile with this email does not already
        # exist (note this unfortunately does not account for the fact
        # that people often have multiple @nasa.gov emails)
        matching_email = settings['db'].view('main/all_email', key=email.lower())
        if matching_email:
            people = []
            for match in matching_email:
                people.append(Person(match.value))
            self.render('templates/message.html', message_data=people, message_type='profile_exists')
            return
        else:
            # create an empty profile for this person with just their
            # email address
            new_person = Person()
            new_person.all_email = [email,]            
            new_person.opennasa_only = True
            uid = next_custom_uid()
            new_person.uid = uid
            new_person.save()            

            # and then send them a one-time login.
            self.redirect('request/'+uid)
            return


class CreateHandler(BaseHandler):
    pass

        
class RefreshHandler(BaseHandler):
    ''' supports refreshing of x500 info'''
    pass


class PageHandler(BaseHandler):
    def get(self, pagename):
        self.render('templates/'+pagename+'.html')
    
class MainHandler(BaseHandler):
    def get(self):
        user_message = ''
        query = self.get_argument("query", None)
        search_type = self.get_argument("search_type", None)
        if not query:
            # if no search has been done yet, just present user w
            # search form
            self.render('templates/index.html', title='Search for your NASA Homies', 
                        recent_gravatars=get_recent_gravatars(10), message=None)
            return

        elif len(query) < 3 and search_type == 'center':
            user_message = 'Please use a search term longer than 2 characters'
            self.render('templates/index.html', title='Search for your NASA Homies', 
                        recent_gravatars=get_recent_gravatars(10), message=user_message)
            return

        else:
            print 'search_type=%s' % search_type
            if search_type == 'center':
                if self.get_argument("ou") == "None":
                    user_message = 'You must select a center before doing a center-specific search.'
                    self.render('templates/index.html', 
                                title='Search for your NASA Homies', 
                                recent_gravatars=get_recent_gravatars(10), 
                                message=user_message)
                    return

                else:
                    people = self.center_search(query)
            elif search_type == 'skill':
                people = self.skill_search(query)
            else:
                people = self.tag_search(query)

        if not len(people):
            user_message = 'No results for that search. Please try again.<br>(<a href="/faq#notfound">Can\'t find your profile?</a>)'
            self.render('templates/index.html', 
                        title='Search for your NASA Homies', 
                        recent_gravatars=get_recent_gravatars(10), 
                        message=user_message)
            return
           
        # if there's only one search result, redirect to the display
        # page for that person.
        if len(people) == 1:
            self.redirect('person/'+people[0].uid)
            return

        # get some stats from the db
        num_customized = total_customized()
        _top_tags = top_tags(10)
        _top_skills = top_skills(10)

        categories = category_count(format='string')

        # display the search results
        self.render('templates/results.html', title='Search Results', results=people, 
                    query=query, category_sm=helper.category_sm, 
                    recent_gravatars=get_recent_gravatars(10), top_skills=_top_skills,
                    num_customized=num_customized, top_tags=_top_tags, 
                    categories=categories, message=user_message)

    def tag_search(self, query):
        ''' search for matches of case-normalized query string against
        tags, returning a list of Person objects with matching
        tags.'''
        tags = settings['db'].view('main/all_tags')

        people = []
        uids = []
        # make sure the query is also made lowercase!
        query = query.lower()
        for tag in tags:
            # tag.key is the tag; tag.value is the uid of the
            # corrsponding user
            if tag.key.lower().find(query) >= 0:
                # make sure the people we add are unique
                if tag.value not in uids:
                    uids.append(tag.value)
                    people.append(Person(tag.value))
        return people

    def skill_search(self, query):
        ''' search for matches of case-normalized query string against
        skills, returning a list of Person objects with matching
        tags.'''
        skills = settings['db'].view('main/all_skills')

        # make sure the query is also made lowercase!
        query = query.lower()
        people = []
        uids = []
        for skill in skills:
            # tag.key is the tag; tag.value is the uid of the
            # corrsponding user
            if skill.key.lower().find(query) >= 0:
                # make sure the people we add are unique
                if skill.value not in uids:
                    uids.append(skill.value)
                    people.append(Person(skill.value))
        return people
                
    def center_search(self, query):            
        center = self.get_argument("ou")
        # flag to note if a record returns with no recognizable uid
        no_uid_flag = False

        # figure out if we're doing a local search or a remote search
        if center=='local': 
            people = self.local_search(query)
            return people

        else: 
            # results is a key value store of the (name, info)
            # pairs from the ldap server. info is itself a
            # dict. for each new result, check if we already have
            # this person's record. if so, then it contains both
            # the x500 info AND any local additions. if not, add
            # it. each value is a list, no matter if it has one or
            # more values.
            results = self.x500_search(query, ou=center)

            # as we parse the results, build a list of people objects
            # which will be used to present the search results in the
            # template.
            people = []
            for name, info in results.iteritems():
                print 'Processing search results for: %s' % name
                # get the uid so we can uniquely reference each search
                # result
                try:
                    # careful here-- some results have BOTH a uid
                    # field and a uniqueIdentifier.
                    if 'uniqueIdentifier' in info:
                        uid = info['uniqueIdentifier'][0]
                    elif 'uid' in info:
                        uid = info['uid'][0]
                    else: raise KeyError
                except KeyError:
                    # xxx todo actually handle this error a little better. 
                    no_uid_flag = True
                    print '*** Warning! User %s did not have a unique identifier. Weird. Here is their user data:' % name
                    print info
                    continue

                if uid not in settings['db']:            
                    print 'Adding %s (uid=%s) to data store' % (name, uid)
                    person = Person()
                    person.build(info)                    
                    person.save()
                else:
                    person = Person(uid)
                    print 'User %s is already in the data store' % name
                people.append(person)            
            if len(people) == 1 and no_uid_flag:
                return None
            else: return people

    def local_search(self,query):
        ''' do a search of the local database for documents that have
        names with a substring matching the query term. case
        insensitive. returns a list of Person objects.'''
        results = settings['db'].view('main/all_names')
        uids_in_list = []
        people = []
        for result in results:
            if result.key.lower().find(query) >= 0:
                # since people can have multiple names in their
                # profile, the search string might match once for each
                # version of their name. keep track of uids we've
                # already matched on so that we dont return duplicate
                # results.
                if result.value not in uids_in_list:
                    uids_in_list.append(result.value)
                    people.append(Person(result.value))
        print 'len people: %d' % len(people)
        return people

    def x500_search(self,query, ou=None, wildcard=True):
        if ou:
            # we have different ldap servers for some centers who dont
            # play nice with the default x500.
            if ou == 'headquarters':
                server = "ldap.nasa.gov"
                dn = "ou=headquarters, o=National Aeronautics and Space Administration,c=US"

            elif ou == 'Jet Propulsion Laboratory':
                server = 'ldap.jpl.nasa.gov'
                dn = "dc=dir,dc=jpl,dc=nasa,dc=gov"

            else:
                server = "x500.nasa.gov"
                dn = "ou=%s,o=National Aeronautics and Space Administration,c=US" % (ou)                            
        else:
            # when center == None --> agency-wide search
            server = "x500.nasa.gov"
            dn="o=National Aeronautics and Space Administration,c=US"

        if wildcard:
            _filter = "cn=*%s*" % (query)
            #filter = "(&(objectClass=organizationalPerson)(cn=*%s*))" % (query)
        else:
            _filter = "(&(objectClass=organizationalPerson)(cn=%s))" % (query)
        print 'Searching ldap with filter: %s, dn="%s"' % (_filter, dn)
        l = ldap.open(server)
        result_id = l.search(dn, ldap.SCOPE_SUBTREE, _filter, None)
        timeout = 0
        result_set = {}
        while 1: 
            result_type, result_data = l.result(result_id, timeout)
            print 'raw ldap result:'
            print result_type
            print result_data

            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    name = tornado.escape.url_escape(result_data[0][1]['cn'][0])
                    result_set[name] = result_data[0][1]
        return result_set

def recently_edited(n=None):
    '''returns a list of the n most recently edited profiles. If n is
    None, returns all records, sorted in order of descending edit date
    (eg. most recently edited to least recently edited)'''
    
    # the key value of the recently_edited view is a javascript date
    # string representing the "number of milliseconds after midnight
    # January 1, 1970 till the given date." so descending returns the
    # largest value FIRST, and the largest value is furthest 1970 ==>
    # most recent.
    if n:
        recent = settings['db'].view('main/recently_edited', descending=True, limit=n)  
    else:
        recent = settings['db'].view('main/recently_edited', descending=True)    
    return [r.value for r in recent]

def get_recent_gravatars(num):
    # get recently edited profiles
    recent = recently_edited(num)
    recent_gravatars = {}
    for uid in recent:
        person = Person(uid)
        recent_gravatars[uid] = person.gravatar(50)
    return recent_gravatars


def total_customized():
    ''' returns an integer representing the total number of profiles
    which have been customized in our system'''
    # this is a reduce function, so it should only have one result.
    customized = settings['db'].view('main/total_customized')

    if not len(customized):
        return 0
    # not sure how else to access the results, though iterating over a
    # single item list seems a bit silly.
    for row in customized:
        return row.value

def category_count(format=None):
    ''' return a dict of category:count pairs for all job
    categories. format can be 'string' or None, and specifies how the
    values should be formatted. if format == None, int is used.'''
    cat_counts = settings['db'].view('main/categories_count', group=True)
    categories = {}
    for item in cat_counts:
        if format == 'string':
            categories[item.key] = str(item.value)
        else:
            categories[item.key] = item.value        
    return categories

def top_tags(n=None):
    ''' return a list of the top n tags in order of decreasing frequency'''
    # the group=True parameter is key; it's what tells the view to
    # group the results by key (er, no pun intended).
    if n:
        tags = settings['db'].view('main/tags_count', group=True, limit=n, descending=True)
    else:
        tags = settings['db'].view('main/tags_count', group=True, descending=True)
    top_tags = []
    for tag in tags:
        top_tags.append((tag.value, tag.key))
    top_tags.sort(reverse=True)
    return [tag[1] for tag in top_tags]

def top_skills(n=None):
    ''' return a dict of skill:count pairs for the top n skills'''
    # the group=True parameter is key; it's what tells the view to
    # group the results by key (er, no pun intended).
    if n:
        skills = settings['db'].view('main/skills_count', group=True, limit=n, descending=True)
    else:
        skills = settings['db'].view('main/skills_count', group=True, descending=True)
    top_skills = []
    for skill in skills:
        top_skills.append((skill.value, skill.key))
    top_skills.sort(reverse=True)
    return [skill[1] for skill in top_skills]

def next_custom_uid():
    ''' return the value of the next custom UID. note that this is a
    string value, and all custom UIDs (ie, those note based on an x500
    value) begin with a # symbol.'''
    results = settings['db'].view('main/max_custom_uid', descending=True, limit=1)
    if not results:
        return '+0'
    for result in results:
        return '+'+ str(result.value + 1)

######################################################
######################################################

application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/person/([A-Za-z0-9\+,\-%\+]+)', PersonHandler),
        (r'/person/([A-Za-z0-9\+,\-%\+]+/refresh)', RefreshHandler),
        (r'/request/([A-Za-z0-9\+,\-\+]+)', EditRequestHandler),
        (r'/create_request', CreateRequestHandler),
        (r'/create', CreateHandler),
        (r'/edit', EditHandler),
        (r'/(faq)', PageHandler),
        #(r'/(advanced)', PageHandler),
        (r'/(about)', PageHandler),
        (r'/logout', LogoutHandler),
        (r'/login/([A-Za-z0-9\-]+)', LoginHandler),
        ], **settings)


if __name__ == '__main__':

    # make sure the couchdb views are up to date
    # Database().configure()

    # start tornado
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(settings['port'])
    tornado.ioloop.IOLoop.instance().start()
