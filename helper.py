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
# FIVVF=Fairmont%20IVV%20Facility
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





Centers = {
    "ARC": "label:ARC|37.411870,-122.062333",
    "DFRC": "label:DFRC|34.901944,-117.891026",
    "GSFC": "label:GSFC|38.995938,-76.851768",
    "JPL": "label:JPL|34.203138,-118.172207",
    "JSC": "label:JSC|29.560726,-95.093365",
    "KSC": "label:KSC|28.58583,-80.651321",
    "GRC": "label:GRC|41.412728,-81.862178",
    "LaRC": "label:LaRC|37.102681,-76.385536",
    "SSC": "label:SSC|30.302121,-89.594879",
    "HQ": "label:HQ|38.883128,-77.016413"
}

def map(center):
    """ return a google maps static url for a nasa center """
    selected = '|'.join(["markers=size:large|color:red", Centers[center]])
    others = '|'.join(["markers=size:tiny|color:green"] + Centers.values())
    return "http://maps.google.com/maps/api/staticmap?" + \
       "&".join(["center=United+States",
                 "zoom=3",
                 "size=320x220",
                 "maptype=hybrid",
                 selected,
                 others,
                 "sensor=false",
                 "key=ABQIAAAAcA1uAFMrbjLedVsnIfdzKBTB6AAoiF2DC7aNiN_b61fgFnS7FhTHUsE12TUzpqrichBbMDc2ZKHDlw"])


if __name__ == '__main__':
    print map('LaRC')