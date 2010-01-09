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
        ''' define/update the views. note that the sync function will
        also update existing views.'''

        self.connect()
        all_docs_fun = '''
        function(doc) {
          emit(doc._id, doc);
        }
        '''
        all_docs_view = ViewDefinition('main', 'all_docs', all_docs_fun )
        all_docs_view.sync(self.db) 

        recently_edited_fun = '''
        function(doc) {
          if (doc.edited && doc.customized) {
            emit(Date.parse(doc.edited), doc._id);
          }
        }
        '''
        recently_edited_view = ViewDefinition('main', 'recently_edited', recently_edited_fun )
        recently_edited_view.sync(self.db)

        total_customized_map = '''
        function(doc) {
          if (doc.customized) {
            emit(doc._id, 1);
          }
        }
        '''
        total_customized_reduce = '''
        function(key, values, rereduce) {
          return sum(values);
        }
        '''        
        total_customized_view = ViewDefinition('main', 'total_customized', total_customized_map, 
                                              reduce_fun=total_customized_reduce )
        total_customized_view.sync(self.db)

        tags_count_map = '''
        function(doc) {
          doc.tags.forEach(function(tag) {
            emit(tag, 1);
          });
        }
        '''
        tags_count_reduce = '''
        function(key, values, rereduce) {
          return sum(values);
        }
        '''        
        tags_count_view = ViewDefinition('main', 'tags_count', tags_count_map, 
                                         reduce_fun=tags_count_reduce )
        tags_count_view.sync(self.db)

        skills_count_map = '''
        function(doc) {
          doc.skills.forEach(function(skill) {
            emit(skill, 1);
          });
        }
        '''
        skills_count_reduce = '''
        function(key, values, rereduce) {
          return sum(values);
        }
        '''        
        skills_count_view = ViewDefinition('main', 'skills_count', skills_count_map, 
                                           reduce_fun=skills_count_reduce )
        skills_count_view.sync(self.db)

        categories_count_map = '''
        function(doc) {
          if (doc.category) {
           emit(doc.category, 1);
          }
        }
        '''
        categories_count_reduce = '''
        function(key, values, rereduce) {
          return sum(values);
        }
        '''        
        categories_count_view = ViewDefinition('main', 'categories_count', categories_count_map, 
                                           reduce_fun=categories_count_reduce )
        categories_count_view.sync(self.db)


        max_custom_uid_map = '''
        function(doc) {
          if (doc.opennasa_only == true) {
            emit(null, doc._id.substring(1));
          }
        }
        '''

        max_custom_uid_reduce = '''
        function(key, values, rereduce) {
          var greatest = 0;
          values.forEach(function(value) {
            value = value * 1;
            if (value > greatest) {
              greatest = value;
            }     
          });
          return greatest;
        }
        '''        
        max_custom_uid_view = ViewDefinition('main', 'max_custom_uid', max_custom_uid_map, 
                                           reduce_fun=max_custom_uid_reduce )
        max_custom_uid_view.sync(self.db)

        all_names_map = '''
        function(doc) {
          if (doc.all_names) {
            doc.all_names.forEach(function(name) {
              emit(name, doc._id);
            });
          }
        }
        '''
        all_names_view = ViewDefinition('main', 'all_names', all_names_map)
        all_names_view.sync(self.db)


        all_tags_map = '''
        function(doc) {
          doc.tags.forEach(function(tag) {
            emit(tag, doc._id);
          });
        }
        '''
        all_tags_view = ViewDefinition('main', 'all_tags', all_tags_map)
        all_tags_view.sync(self.db)

        all_skills_map = '''
        function(doc) {
          doc.skills.forEach(function(skill) {
            emit(skill, doc._id);
          });
        }
        '''
        all_skills_view = ViewDefinition('main', 'all_skills', all_skills_map)
        all_skills_view.sync(self.db)

        all_email_map = '''
        function(doc) {
          if (doc.all_email) {
            doc.all_email.forEach(function(email) {
              emit(email.toLowerCase(), doc._id);
            });
          }
        }
        '''
        all_email_view = ViewDefinition('main', 'all_email', all_email_map)
        all_email_view.sync(self.db)


if __name__ == '__main__':
    database = Database()    
    database.configure()
    
