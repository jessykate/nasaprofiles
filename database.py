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

    def connect(self):
        # connect to the db, creating it if it doesnt exist. 
        couch = couchdb.Server('http://localhost:5984/')
        if 'nasaprofiles' not in couch:
            self.db = couch.create('nasaprofiles')
        else:
            self.db = couch['nasaprofiles']
        return self.db

    def configure(self):
        # define/update the views

        self.connect()
        all_docs_fun = '''
        function(doc) {
          emit(doc._id, doc);
        }
        '''
        all_docs_view = ViewDefinition('main', 'all_docs', all_docs_fun )
        all_docs_view.sync(self.db)

        existing_profiles_fun = '''
        function(doc) {
          emit(doc.x500_url, doc._id);
        }
        '''
        existing_profiles_view = ViewDefinition('main', 'existing_profiles', existing_profiles_fun )
        existing_profiles_view.sync(self.db)        

        recently_edited_fun = '''
        function(doc) {
          if (doc.edited) {
            emit(Date.parse(doc.edited), doc._id);
          }
        }
        '''
        recently_edited_view = ViewDefinition('main', 'recently_edited', recently_edited_fun )
        recently_edited_view.sync(self.db)

if __name__ == '__main__':
    database = Database()    
    database.configure()
    
