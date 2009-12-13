#!/usr/bin/python

import urllib2, urllib, re, time, hashlib, uuid
import smtplib
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
from x500DisplayParser import x500DisplayPageParser

class PersonHandler(tornado.web.RequestHandler):
    def get(self, name):
        db = settings['db']
        search_results = tornado.escape.json_decode(tornado.escape.url_unescape(self.get_cookie('search_results')))

        # get the x500 info. XXX TODO we should be able to detect if
        # the person is in our local database BEFORE we hit the remote
        # x500 server.
        url = tornado.escape.url_unescape(search_results[name])
        html = urllib2.urlopen(url)
        parser = x500DisplayPageParser()
        parser.feed(''.join(html.readlines()))
        profile = parser.profile_fields

        # get the NASA uid, which is also the index into our data
        # store. all the scraped values from x500 are lists, even if
        # only one item.
        uid = profile['Unique Identifier'][0]

        # see if there's a local record first. if so, then it contains
        # both the x500 info AND any local extensions.
        if uid in db:
            doc = db[uid]
            profile = doc.copy()
        else:
            # create a new record
            db[uid] = profile
        # remove profile fields that we dont want to render.
        profile.pop('_id')
        profile.pop('_rev')
        
        # get gravatar. use the first email address as the defaul for
        # now.
        try:
            email = profile['Internet Addresses'][0]
        except:
            email = "empty@opennasa.com"        
            
        # save the uid for the edit request.
        edit_request = '/edit/'+uid
        self.render('templates/person.html', title=profile['Name'], edit_request=edit_request,
                    gravatar_url=self.gravatar_url('jk@f00d.org'), profile=profile)
        
    def gravatar_url(self, email):
        size = 150
        base = "http://www.gravatar.com/avatar.php?"
        return base+urllib.urlencode({'gravatar_id':hashlib.md5(email).hexdigest(), 
                                      'size':str(size)})                


class EditRequestHandler(tornado.web.RequestHandler):
    def get(self, uid):
        db = settings['db']
        # generate a one-time hash
        if not 'edit_requests' in db:
            db['edit_requests'] = {}
        edit_requests = db['edit_requests']
        edit_requests[uid] = str(uuid.uuid4())
        db['edit_requests'] = edit_requests
        user = db[uid]
        email = user['Internet Addresses'][0]
        
        # construct and send the email
        text = '''Please click the following link to update your information:\n"%s/login/%s"''' % (settings['domain'], edit_requests[uid])
        html = '''<html><p>Please click the following link to update your information:<br><a href="%s/login/%s"></a></p></html>''' % (settings['domain'], edit_requests[uid])
        part1 = MIMEText(text, 'text')
        part2 = MIMEText(html, 'html')
        msg = MIMEMultipart('alternative')
        msg.attach(part1)
        msg.attach(part2)
        msg['Subject'] = '[NASA Profiles] Update your Information'
        msg['From'] = 'profiles@opennasa.com'
        msg['To'] = email
        s = smtplib.SMTP('localhost')
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        self.write('An email with one-time login has been sent to your email address at %s' % email)
        

class EditHandler(tornado.web.RequestHandler):
    # update any new fields
    #for field, value in profile:
    #    doc[field] = value
    #db[uid] = doc
    pass



class SearchHandler(tornado.web.RequestHandler):
    def post(self):
        # pull in x500 data
        query = self.get_argument("query")
        results = self.x500_search(query)
        if not results:
            self.write('No results for "%s"' % query)
            #self.redirect('/search/')
            return

        # save the search results in a session variable   
        json = tornado.escape.url_escape(tornado.escape.json_encode(results))
        self.set_cookie('search_results', json)
        
        # display the search results
        people = results.keys()
        self.render('templates/results.html', title='Search Results', results=people)

    def get(self):
        # present user w search form
        self.set_header("Content-Type", "text/html")
        self.render('templates/search.html', title='Search for your NASA Homies')

    def x500_search(self, query):
        # base url searches for entries in country = US and org = NASA
        base_url = "http://x500root.nasa.gov:80/cgi-bin/wlDoSearch/ou%3dAmes%20Research%20Center%2co%3dNational%20Aeronautics%20and%20Space%20Administration%2cc%3dUS"

        #name = raw_input('name? >> ')
        org = 'National Aeronautics and Space Administration'
        country = 'US'
        subtree = 'on' # checkbox to indicate search within Ames subtree
        # form drop down list options
        type = 'Full Name'
        level2 = 'Organization'
        level1 = 'Country'
        style = 'Substring'
        request = urllib.urlencode({'NAME':query, 'ORG':org, 'COUNTRY':country, 
                                    'SUBTREE':subtree, 'TYPE':type, 'LEVEL2':level2,
                                    'LEVEL1':country, 'STYLE':style})
        html = urllib2.urlopen(base_url, request)
        return self.structured_results(html)

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
        

######################################################
######################################################

settings = {
    'db':Database().connect(),
    'domain': 'localhost',
    'port': 8989,
}

application = tornado.web.Application([
        (r'/search', SearchHandler),
        # XXX FIXME this regex probably wouldnt support many names
        (r'/person/([A-Za-z0-9\+,\-%]+)', PersonHandler),
        (r'/edit/([A-Za-z0-9\+,\-%]+)', EditRequestHandler),
        ], **settings)


if __name__ == '__main__':

   # set up the elixir mapper functions
    #setup_all()

    # set up tornado handling
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(settings['port'])
    tornado.ioloop.IOLoop.instance().start()

