#!/usr/bin/python

from HTMLParser import HTMLParser

class x500DisplayPageParser(HTMLParser):

    def __init__(self):
        self.table = False
        self.newrow = False
        self.cell = False
        self.currentfield = False
        self.getvalue = False
        self.profile_fields = {}
        self.finished = False
        HTMLParser.__init__(self)

    # for each table row, if there's a 
    def handle_starttag(self, tag, attrs):
        # start paying attention when we get inside the table. 
        if self.finished:
            return
        elif tag == 'table':
            self.table = True
        elif self.table:
            if tag == 'tr': # starting a new row
                self.newrow = True
            elif self.newrow and tag == 'td':
                # if it's a new row and this is a td tag, then this is
                # the first cell.
                self.newrow = False
                self.cell = 1
            elif tag == 'td' and not self.newrow:
                # if it's not the first cell in the row, then it's
                # contains a value.
                self.cell += 1
                self.getvalue = True

    def handle_data(self,data):
        data = data.strip()
        data = data.strip(':')
        if self.cell == 1:
            if data:            
                # if there's data, then we have a new field
                self.currentfield = data  
                # initialize an empty list for the field values since
                # sometimes the fields have more than one value--
                # eg. if someone has more than one email address
                # listed.
                self.profile_fields[self.currentfield] = []
        if self.cell > 1 and data:
            # then it's a new value for the current field
            self.profile_fields[self.currentfield].append(data)

    def handle_endtag(self, tag):
        if tag == 'table':
            self.finished = True            
        if tag == 'tr':
            self.cell = False

if __name__ == '__main__':
    
    html = open('/home/jessy/dev/nasaprofiles/example_display.html')
    parser = x500DisplayPageParser()
    parser.feed(''.join(html.readlines()))
    for field, values in parser.profile_fields.iteritems():        
        for value in values:
            print "%s\t\t\t%s" % (field, value)
