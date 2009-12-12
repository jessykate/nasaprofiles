#!/usr/bin/python
import ldap, os, sys
con = ldap.initialize("ldap://lc.nasa.gov")
#con = ldap.initialize("ldap://webdir.nasa.gov")
dn = "uid=ARC\jcowansh"
pw = open(os.getenv("HOME")+"/.nasapasswd").read().strip()
#r = con.simple_bind_s(dn,pw)
r = con.simple_bind_s()
#base_dn = 'o=National Aeronautics and Space Administration,c=US'
base_dn = 'OU=people, OU=NASA, o=U.S. Government, c=US'
#filter_ = 'ou=ARC*'
#filter_ = 'cn=*worden*'
filter_ = 'cn=*'+raw_input('enter your query >> ')+'*'
attrs = ['*']
attrs_only = 0
timeout = 5
get_all_attributes=None # None means 'all'
#result = con.search_st( base_dn, ldap.SCOPE_SUBTREE, filter_, attrs, attrs_only, timeout )
result_id = con.search(base_dn, ldap.SCOPE_SUBTREE, filter_, get_all_attributes)
result_type, result_data = con.result(result_id, timeout)
for item in result_data:
    
    print item

#print r
#for (name,value) in r:
#    print "\n============= %s ==========" % name
#    for (n,v) in value.iteritems():
#        print " ",n,"=>",v
#    print ""
