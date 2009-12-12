#!/usr/bin/python

import couchdb
from couchdb.design import *

# Fields
# - 
# - bio
# - tags
# - expertise
# - category
# - hire_date
# - job_title
# - website
# - twitter

class Database(object):
    def __init__(self):
        # connect to the db, creating it if it doesnt exist. 
        couch = couchdb.Server('http://localhost:5984/')
        if 'nasaprofiles' not in couch:
            self.db = couch.create('nasaprofiles')
        else:
            self.db = couch['nasaprofiles']

    def connect(self):
        return self.db

    def configure(self):
        # define/update the views
        all_docs_fun = '''
        function(doc) {
          emit(uid, doc);
        }
        '''
        all_docs_view = ViewDefinition('main', 'all_docs', all_docs_fun )
        all_docs_view.sync(self.db)

if __name__ == '__main__':
    database = Database()
    database.configure()
    
