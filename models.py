from elixir import *
import datetime

metadata.bind = 'sqlite:///crossfit.sqlite'
metadata.bind.echo = True

# we're not currently storing the x500 fields, only our wrapper fields. 
class Person(Entity):
    id = Field(Integer, primary_key=True)
    last_updated - Field(Datetime, default=datetime.datime.now, required=True)
    bio = Field(Text)
    
class PersonTags(Entity):
    id = 

class Tags(Entity):
    id = Field(Integer, primary_key=True)
    tag = FIeld(Text)
