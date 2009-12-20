# Organizational_units = {
# 
# 
# ARC=Ames%20Research%20Center
# 
# DFRC=Dryden%20Flight%20Research%20Center
# 
# EOS=Earth%20Observing%20System 
# //GSFC
# 
# IVV=Fairmont%20IVV%20Facility
# //LaRC
# 
# GISS=Goddard%20Institute%20for%20Space%20Studies
# //GSFC
# 
# GRC=Glenn%20Research%20Center
# 
# GSFC=Goddard%20Space%20Flight%20Center
# 
# HQ=Headquarters
# 
# JPL=Jet%20Propulsion%20Laboratory
# 
# JSC=Johnson%20Space%20Center
# 
# KSC=Kennedy%20Space%20Center
# 
# LaRC=Langley%20Research%20Center
# 
# MSFC=Marshall%20Space%20Flight%20Center
# 
# MAF=Michoud%20Assembly%20Facility
# //KSC
# 
# NSSC=NASA%20Shared%20Services%20Center
# //SSC
# 
# NS=Network%20Services
# //MSFC
# 
# SSC=Stennis%20Space%20Center%2co
# 
# RJSP=Russia%20Joint%20Space%20Project
# //JSC
# 
# WFF=Wallops%20Flight%20Facility
# //GSFC
# 
# WSTF=White%20Sands%20Test%20Facility
# //JSC
# 
# }


Address = {
    "NASA Ames Research Center": "Moffett Field, California 94035",
    "NASA Dryden Flight Research Center": "4800 Lilly Drive, Edwards, California 93523-0273",
    "NASA Glenn Research Center": "21000 Brookpark Rd, Cleveland, OH 44135",
    "NASA Goddard Space Flight Center": "Greenbelt, MD 20771",
    "NASA Global Institute of Space Studies": "2880 Broadway, New York, NY",
    "NASA Fairmont IVV Facility": "100 University Dr Fairmont, WV 26554",
    "NASA Jet Propulsion Laboratory": "4800 Oak Grove Drive, Pasadena, California 91109",
    "NASA Johnson Space Center": "Houston, TX 77058",
    "NASA Kennedy Space Center": "FL 32899-0001",
    "NASA Langley Research Center": "Hampton, Virginia 23681",
    "NASA Marshall Spaceflight Center": "One Tranquility Base, Huntsville, AL 35805",
    "NASA Headquarters": "300 E Street SW, Washington, DC 20546",
    "NASA Shared Services Center": "Building 1111 C Road, MS 39529",
    "NASA Stennis Space Center": "MS,39529",
    "NASA Wallops Flight Facility": "VA 23337",
    "NASA White Sands Test Facility": "12600 NASA Road Las Cruces, NM 88012"
}


Centers = {
    "NASA Ames Research Center": "label:ARC|37.411870,-122.062333",
    "NASA Dryden Flight Research Center": "label:DFRC|34.901944,-117.891026",
    "NASA Glenn Research Center": "label:GRC|41.412728,-81.862178",
    "NASA Goddard Space Flight Center": "label:GSFC|38.995938,-76.851768",
    "NASA Jet Propulsion Laboratory": "label:JPL|34.203138,-118.172207",
    "NASA Johnson Space Center": "label:JSC|29.560726,-95.093365",
    "NASA Kennedy Space Center": "label:KSC|28.58583,-80.651321",
    "NASA Langley Research Center": "label:LaRC|37.102681,-76.385536",
    "NASA Marshall Space Flight Center": "label:MSFC|34.696988,-86.684361",
    "NASA Stennis Space Center": "label:SSC|30.302121,-89.594879",
    "NASA Headquarters": "label:HQ|38.883128,-77.016413"
}

category_lookup = {
    "Developer": "<img src='/static/images/category/developer.png'>",
    "Scientist": "<img src='/static/images/category/scientist.png'>",
    "Engineer": "<img src='/static/images/category/engineer.png'>",
    "Management": "<img src='/static/images/category/management.png'>",
    "Center Operations": "<img src='/static/images/category/center_ops.png'>",
    "Mission Operations": "<img src='/static/images/category/mission_ops.png'>",
    "Administrative": "<img src='/static/images/category/administrative.png'>",
    "Legal": "<img src='/static/images/category/legal.png'>",
    "Finance": "<img src='/static/images/category/finance.png'>",
    "Communications": "<img src='/static/images/category/communications.png'>"
}

category_sm_lookup = {
    "Developer": "<img src='/static/images/category/developer_sm.png'>",
    "Scientist": "<img src='/static/images/category/scientist_sm.png'>",
    "Engineer": "<img src='/static/images/category/engineer_sm.png'>",
    "Management": "<img src='/static/images/category/management_sm.png'>",
    "Center Operations": "<img src='/static/images/category/center_ops_sm.png'>",
    "Mission Operations": "<img src='/static/images/category/mission_ops_sm.png'>",
    "Administrative": "<img src='/static/images/category/administrative_sm.png'>",
    "Legal": "<img src='/static/images/category/legal_sm.png'>",
    "Finance": "<img src='/static/images/category/finance_sm.png'>",
    "Communications": "<img src='/static/images/category/communications_sm.png'>"
}

def mailing(address):
    mailing_address = Address[address]
    return mailing_address



def map(center):
    """ return a google maps static url for a nasa center """
    selected = '|'.join(["markers=size:large|color:red", Centers[center]])
    others = '|'.join(["markers=size:tiny|color:orange"] + Centers.values())
    return "http://maps.google.com/maps/api/staticmap?" + \
       "&".join(["center=United+States",
                 "zoom=3",
                 "size=320x220",
                 "maptype=hybrid",
                 selected,
                 others,
                 "sensor=false",
                 "key=ABQIAAAAcA1uAFMrbjLedVsnIfdzKBTB6AAoiF2DC7aNiN_b61fgFnS7FhTHUsE12TUzpqrichBbMDc2ZKHDlw"])

def category_sm(category):
    category_img = category_sm_lookup[category]
    return category_img
    
def category(category):
    category_img = category_lookup[category]
    return category_img


if __name__ == '__main__':
    print map('LaRC')
