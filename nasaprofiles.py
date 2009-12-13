#!/usr/bin/python

import urllib2, urllib, re, time, 

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

        # get the x500 info
        url = tornado.escape.url_unescape(search_results[name])
        html = urllib2.urlopen(url)
        parser = x500DisplayPageParser()
        parser.feed(''.join(html.readlines()))
        for field, values in parser.profile_fields.iteritems():        
            for value in values:
                self.write("%s: %s<br>" % (field, value))

        # see if we have any local info. if so, display it. 
        all_docs = db.view('main/all_docs')

        #if parser.profile_fields['Unique Identifier'] in all_docs

        # gravatar

        # display "is this you?"        

class SearchHandler(tornado.web.RequestHandler):
    def post(self):
        # pull in x500 data
        query = self.get_argument("query")
        results = x500_search(query)
        if not results:
            self.write('No results for "%s"' % query)
            #self.redirect('/search/')
            return

        # save the search results in a session variable   
        json = tornado.escape.url_escape(tornado.escape.json_encode(results))
        self.set_cookie('search_results', json)
        
        # display the search results to the user
        self.set_header("Content-Type", "text/html")
        for name, link in results.iteritems(): 
            # for each person in the x500 results, display a link to
            # see info about them. if it's only one result, display it
            # directly, instead of a list.
            self.write('<a href="/person/%s">%s</a><br>' % (name,name))

    def get(self):
        # present user w search form
        self.set_header("Content-Type", "text/html")
        self.write('<form action="/search" method="post">'
                   '<label for="query">Search for a NASA person</label><br>'
                   '<input type="text" name="query"><br>'
                   '<label for="center">Select a Center or Centers for your Search</label><br>'
                   '<input type="checkbox" name="arc">Ames Research Center<br>'
                   '<input type="submit" value="Find me some Space Peeps!">'
                   '</form></body></html>')

def x500_search(query):
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
    return structured_results(html)

def structured_results(html):
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
}

application = tornado.web.Application([
        (r'/search', SearchHandler),
        # XXX FIXME this regex probably wouldnt support many names
        (r'/person/([A-Za-z0-9\+,\-%]+)', PersonHandler),
        ], **settings)


if __name__ == '__main__':

   # set up the elixir mapper functions
    #setup_all()

    # set up tornado handling
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8989)
    tornado.ioloop.IOLoop.instance().start()

