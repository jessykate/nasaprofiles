#!/usr/bin/python

import urllib2, urllib, re, time, hashlib, uuid, helper
import smtplib, os
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
import os
from database import Database
from settings import settings
from x500DisplayParser import x500DisplayPageParser

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_cookie("uid")

class PersonHandler(BaseHandler):
    def x500_profile_search(self, query):
        results = x500_search(query, wildcard=False)
        return results[tornado.escape.url_escape(query)]
    def get(self, name):
        db = settings['db']

        print 'search results 1'
        print self.get_cookie('search_results')
        print '============================='

        search_results = tornado.escape.json_decode(tornado.escape.url_unescape(self.get_cookie('search_results')))

        print 'search_results 2'
        print str(search_results)
        print '=============='
        # check if we already have this person's record. if so, then
        # it contains both the x500 info AND any local extensions.
        existing_profiles = db.view('main/existing_profiles')
        x500_url = tornado.escape.url_unescape(search_results[name])
        if len(existing_profiles[x500_url]):
            uid = list(existing_profiles[x500_url])[0]['value']
            doc = db[uid]
            profile = doc.copy()
            print 'Retrieved local record for %s' % name
        else:
            print 'Retrieving x500 record for %s' % name
            profile = self.x500_profile_search(x500_url)
            print profile

            # retrieve the x500 info and create a new record
            #html = urllib2.urlopen(x500_url)
            #parser = x500DisplayPageParser()
            #parser.feed(''.join(html.readlines()))
            #profile = parser.profile_fields

            # get the NASA uid, which is also the index into our data
            # store. all the scraped values from x500 are lists, even if
            # only one item.
            #uid = profile['Unique Identifier'][0]
            uid = profile['uniqueIdentifier'][0]
            profile['x500_url'] = x500_url
            db[uid] = profile
        # remove profile fields that we dont want to render.
        profile.pop('x500_url')
        profile.pop('_id')
        profile.pop('_rev')
	profile['Name'] = profile['cn'][0]

        # get gravatar. use the first email address as the defaul for
        # now.
        try:
            # gravatar uses hashes-- cases sensitive
            email = profile['Internet Addresses'][0].lower()
        except:
            email = "empty@opennasa.com"

        # save the uid for the edit request.
        edit_request = '/request/'+uid
        self.render('templates/person.html', title=profile['Name'], edit_request=edit_request,
                    gravatar_url=self.gravatar_url(email), profile=profile, map=helper.map, mailing=helper.mailing)

    def gravatar_url(self, email, size=125):
        base = "http://www.gravatar.com/avatar.php?"
        return base+urllib.urlencode({'gravatar_id':hashlib.md5(email).hexdigest(),
                                      'size':str(size)})


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
        user = db[uid]
        email = user['Internet Addresses'][0]

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
            message = 'An email with one-time login has been sent to your email address at %s' % email
            print 'One-time login sent'
        elif settings['debug']:
            # careful with this-- it will allow anyone to log into any
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
        else:
            self.write('Invalid/Expired')

class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.clear_cookie("uid")
            self.set_cookie("message","You were successfully logged out")
        self.redirect('/')

class EditHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        db = settings['db']
        uid = self.get_current_user()
        current_profile = db[uid]
        self.render('templates/profile_edit.html', current_profile=current_profile)

    def post(self):
        pass

class RefreshHandler(BaseHandler):
    pass

class MainHandler(BaseHandler):
    def post(self):
        # pull in x500 data
        query = self.get_argument("query")
        results = self.x500_user_search(query)

        # save the search results in a session variable
        json = tornado.escape.url_escape(tornado.escape.json_encode(results))
        self.set_cookie('search_results', json)

        # if there's only one search result, redirect to the display
        # page for that person.
        if len(results) == 1:
            self.redirect('person/'+results.keys()[0])
            return

        # display the search results
        people = results.keys()
        self.render('templates/results.html', title='Search Results', results=people)

    def get(self):
        # present user w search form
        self.render('templates/index.html', title='Search for your NASA Homies', 
                    message = self.get_cookie("message"))

#    def x500_search(self, query):
        # base url searches for entries in country = US and org = NASA
#        base_url = "http://x500root.nasa.gov:80/cgi-bin/wlDoSearch/ou%3dAmes%20Research%20Center%2co%3dNational%20Aeronautics%20and%20Space%20Administration%2cc%3dUS"

        #name = raw_input('name? >> ')
#        org = 'National Aeronautics and Space Administration'
#        country = 'US'
#        subtree = 'on' # checkbox to indicate search within Ames subtree
        # form drop down list options
#        type = 'Full Name'
#        level2 = 'Organization'
#        level1 = 'Country'
#        style = 'Substring'
#        request = urllib.urlencode({'NAME':query, 'ORG':org, 'COUNTRY':country,
#                                    'SUBTREE':subtree, 'TYPE':type, 'LEVEL2':level2,
#                                    'LEVEL1':country, 'STYLE':style})
#        html = urllib2.urlopen(base_url, request)
#        return self.structured_results(html)


    def x500_user_search(self, query):
        results = x500_search(query, wildcard=True)
        mapped = {}
	for k, v in results.iteritems():
		mapped[k] = v['cn'][0]
        return mapped



    def structured_results(self,html):
        ''' scrape through x500 search results and build a set of
        structured results.'''
        contents = ''.join(html.readlines())
        links = re.findall(r'''http://x500root.nasa.gov:80/cgi\-bin/wlDisplay/cn%3d.*">.*</a>''',
                           contents, re.IGNORECASE)
        # we match on everything up to the ending quote and '>' symbol,
        # just to be certain we're not matching on a quote in the url
        # itself. but we actually dont want to keep those symbols, so
        # strip them off.
        results = {}
        for link in links:
            link = link.strip('</aA>')
            url, name = link.rsplit('>')

            # properly encode the urls
            url = tornado.escape.url_escape(url.strip('">'))
            name = tornado.escape.url_escape(name.strip())
            results[name] = url
        return results

def x500_search(query, wildcard=True):
	import ldap
	l = ldap.open("x500.nasa.gov")
	dn="ou=Ames Research Center,o=National Aeronautics and Space Administration,c=US"
	if wildcard:
		filter = "cn=*%s*" % (query)
	else:
		filter = "cn=%s" % (query)
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

