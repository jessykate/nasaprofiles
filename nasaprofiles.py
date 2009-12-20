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
from x500DisplayParser import x500DisplayPageParser

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_cookie("uid")

class PersonHandler(BaseHandler):
    def x500_profile_search(self, query):
        results = x500_search(query, ou=None, wildcard=False)
        return results[tornado.escape.url_escape(query)]

    def get(self, uid): 
        db = settings['db']

        try:
            person = Person(uid)
        except:
            self.redirect('/')

        self.render('templates/person.html', title=person.display_name(), 
                    person=person, map=helper.map, mailing=helper.mailing, 
                    category=helper.category, category_sm=helper.category_sm)


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
            message = "This user does not have any email addresses, so we cannot verify your identity. You should update your official x500 information. If this isn't possible, email support@people.opennasa.com and we can help you work it out."
            self.render('templates/email_notify.html', message=message)
            return

        # construct and send the email
        base = 'http://'+settings['domain']
        if settings['port'] != 80:
            base += ':'+str(settings['port'])
        edit_url = base+'/login/'+onetime_uuid
        text = '''Please click the following link to update your information:\n%s''' % edit_url
        html = '''<html><p>Please click the following link to update your information:<br><a href="%s">%s</a></p></html>''' % (edit_url, edit_url)
        part1 = MIMEText(text, 'text')
        part2 = MIMEText(html, 'html')
        msg = MIMEMultipart('alternative')
        msg.attach(part1)
        msg.attach(part2)
        msg['Subject'] = '[NASA Profiles] Update your Information'
        msg['From'] = 'profiles@opennasa.com'
        msg['To'] = email
        if settings['email_enabled']:
            s = smtplib.SMTP('smtp.gmail.com:587')
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
            self.set_cookie("uid", uid)
            # remove this cookie so it can't be used again
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
            #self.set_cookie("message","You were successfully logged out")
        self.redirect('/')

class EditHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        if not self.get_argument('submitted', None):
            db = settings['db']
            uid = self.get_current_user()
            person = Person(uid)
            self.render('templates/profile_edit.html', person=person)

        else:
            new_values = self.request.arguments
            self.write(str(new_values))

            uid = self.get_current_user()
            person = Person(uid)
            for field, value in new_values.iteritems():            
                # check to see if it's an x500 field; if so, compare
                # it to the original value, and if it's new, set the
                # new value as a local override.
                if field in person.x500:
                    if value != person.x500[field]:
                        person.set(field, value)
                else:
                    print 'settings new value %s = %s' % (field, value)
                    person.set(field, value)
            person.save()
            self.redirect('/person/'+uid)

        
class RefreshHandler(BaseHandler):
    pass

class MainHandler(BaseHandler):
    def get(self):
        db = settings['db']
        query = self.get_argument("query", None)
        if query:
            center = self.get_argument("ou")
            if center == "all":
                center = None

            # results is a key value store of the name, info pairs
            # from the ldap server. info is itself a dict. for each
            # new result, check if we already have this person's
            # record. if so, then it contains both the x500 info AND
            # any local additions. if not, add it. each value is a
            # list, no matter if it has one or more values.
            results = self.x500_search(query, ou=center)
            # as we parse the results, build an list of people objects
            # which will be used to present the search results in the
            # template.
            people = []
            for name, info in results.iteritems():
                print 'search results: %s' % name
                # get the uid so we can uniquely reference each search
                # result
                try:
                    uid = info['uniqueIdentifier'][0]
                except KeyError:
                    # xxx todo actually handle this error. 
                    print '*** Warning! User %s did not have a unique identifier. Weird. Here is their user data:' % name
                    print info
                    continue
                if uid not in db:            
                    print 'Adding %s to data store' % name
                    person = Person()
                    person.build(info)                    
                    person.save()
                else:
                    person = Person(uid)
                    print 'User %s is already in the data store' % name
                people.append(person)
            
            # if there's only one search result, redirect to the display
            # page for that person.
            if len(results) == 1:
                self.redirect('person/'+results.values()[0]['uniqueIdentifier'][0])
                return

            # display the search results
            self.render('templates/results.html', title='Search Results', results=people, 
                        category_sm=helper.category_sm)

        else: 
            # if no search has been done yet, just present user w
            # search form
            self.render('templates/search.html', title='Search for your NASA Homies',
                        message = self.get_cookie("message"))

    def x500_search(self,query, ou="Ames Research Center", wildcard=True):
        l = ldap.open("x500.nasa.gov")
        if ou:
            dn="ou=%s,o=National Aeronautics and Space Administration,c=US" % (ou)
        else:
            dn="o=National Aeronautics and Space Administration,c=US"
        print dn
        if wildcard:
            filter = "(&(objectClass=organizationalPerson)(cn=*%s*))" % (query)
        else:
            filter = "(&(objectClass=organizationalPerson)(cn=%s))" % (query)
        print filter
        result_id = l.search(dn, ldap.SCOPE_SUBTREE, filter, None)
        timeout = 0
        result_set = {}
        while 1:
            result_type, result_data = l.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    name = tornado.escape.url_escape(result_data[0][1]['cn'][0])
                    result_set[name] = result_data[0][1]
        return result_set

######################################################
######################################################

application = tornado.web.Application([
        (r'/', MainHandler),
        # XXX FIXME this regex probably wouldnt support many names
        (r'/person/([A-Za-z0-9\+,\-%]+)', PersonHandler),
        (r'/person/([A-Za-z0-9\+,\-%]+/refresh)', RefreshHandler),
        (r'/request/([A-Za-z0-9\+,\-%]+)', EditRequestHandler),
        (r'/edit', EditHandler),
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
