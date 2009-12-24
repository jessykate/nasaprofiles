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

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_cookie("uid")

class PersonHandler(BaseHandler):

    def get(self, uid): 
        db = settings['db']
        person = Person(uid)

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
            # the user had updated their information. 
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
                elif field == 'primary_email' and custom_email_flag:
                    continue
                elif field == 'primary_name' and custom_name_flag:
                    continue
                elif field == 'primary_phone' and custom_phone_flag:
                    continue

                # for all other fields, if it wasnt empty, then store
                # the new value.
                elif value:
                    print 'settings new value %s = %s' % (field, value)
                    person.set(field, value)

            person.save()
            self.redirect('/person/'+uid)

        
class RefreshHandler(BaseHandler):
    ''' supports refreshing of x500 info'''
    pass


class FaqHandler(BaseHandler):
    def get(self):
        self.render('templates/faq.html')
    
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
            no_uid_flag = False
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

                if uid not in db:            
                    print 'Adding %s (uid=%s) to data store' % (name, uid)
                    person = Person()
                    person.build(info)                    
                    person.save()
                else:
                    person = Person(uid)
                    print 'User %s is already in the data store' % name
                people.append(person)
            
            # if there's only one search result, redirect to the display
            # page for that person.
            if len(results) == 1 and not no_uid_flag:
                if settings['debug']:
                    print 
                self.redirect('person/'+uid)
                return

            # display the search results
            self.render('templates/results.html', title='Search Results', results=people, 
                        query=query, category_sm=helper.category_sm)

        else: 
            # if no search has been done yet, just present user w
            # search form
            self.render('templates/search.html', title='Search for your NASA Homies',
                        message = self.get_cookie("message"))

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
            # defaults
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

######################################################
######################################################

application = tornado.web.Application([
        (r'/', MainHandler),
        # XXX FIXME this regex probably wouldnt support many names
        (r'/person/([A-Za-z0-9\+,\-%]+)', PersonHandler),
        (r'/person/([A-Za-z0-9\+,\-%]+/refresh)', RefreshHandler),
        (r'/request/([A-Za-z0-9\+,\-%]+)', EditRequestHandler),
        (r'/edit', EditHandler),
        (r'/faq', FaqHandler),
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
