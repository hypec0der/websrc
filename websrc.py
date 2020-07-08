
import urllib.request as request 
from urllib.error import HTTPError 
from urllib.parse import urlencode
import sys
import re
import os
import argparse
import base64
from queue import Queue
from bs4 import BeautifulSoup


pattern_header = '([\w]*)=([\w]*)'   #es. GET=/

pattern_tag_with_attributes = '([\w]*)->([\w]*)'   #es. a -> href
pattern_tag = '([\w]*)'

pattern_authentication = '([\w\d]*):([\w\d]*)'   #es. user:passw


def preurlopen ( target, credentials, hrequests ) :

    headers = dict ()

    if hrequests:
        getheader ( hrequests, headers )

    if credentials:
        basicauthentication ( credentials, target )

    return urlencode ( headers ) .encode ( 'utf-8' )



def getheader ( hrequests, headers ):

    prog = re.compile ( pattern_header )

    for header in hrequests:

        try:

            res = prog.match ( header )

            if res:
                headers.update ({ res.group(1) : res.group(2) })

            else:
                raise ValueError ()

        except ValueError :
            print ('Invalid format for header -> %s' %header )
            



def basicauthentication ( credentials, target ):

    prog = re.compile ( pattern_authentication )

    try:

        res = prog.match ( credentials )

        if res :

            httpsHandler = request.HTTPSHandler()

            manager = request.HTTPPasswordMgrWithDefaultRealm()

            manager.add_password( None, target, res.group(1), res.group(2) )

            authHandler = request.HTTPBasicAuthHandler(manager)

            opener = request.build_opener(httpsHandler, authHandler)
            
            request.install_opener(opener)

        else:
            raise ValueError ()
    
    except ValueError :
        print ('Invalid format for credentials')




def createhttpreq ( url, headers ):

    opener = None
    info = None
    code = 0


    try:

        req = request.Request ( url, headers )

        opener = request.urlopen ( req )
        
        info = opener.info ()
        
        code = opener.getcode ()

    except HTTPError as error:

        print ( error )

        if hasattr ( error, 'code' ):
            code = error.code
        
        if hasattr ( error, 'info' ):
            info = error.headers

    finally:
        return opener, info, code
     


def gethtmltag ( opener, tagrequest, extrequests, parser ):

    prog1 = re.compile ( pattern_tag )
    prog2 = re.compile ( pattern_tag_with_attributes )

    content = opener.read ()

    soup = BeautifulSoup ( content, parser )

    if not tagrequest:
        return soup.prettify ()

    else:

        taglist = list ()

        for tag in tagrequest: 

            res1 = prog1.match ( tag )
            res2 = prog2.match ( tag )

            if res2:
                
                for item in soup.find_all ( res2.group(1) ):

                    res = item.get ( res2.group(2) )

                    if not extrequests:
                        taglist.append ( res )
                    
                    else:
                        for extension in extrequests:
                            if res and extension in res:
                                taglist.append ( res )


            elif res1:
                for tag in soup.find_all ( tag ):
                    taglist.append ( tag )


            else:
                print ('Invalid format for tag requests')
        
        return taglist 




def verbose ( target, info, code ) :

    print ( '\n ####################################################################### \n')

    print ( '%s -> [%d] \n' %( target, code ))

    print ( '%s' %info )

    print ( '\n ####################################################################### \n')



def main () :

    parser = argparse.ArgumentParser ( description = "Get all file in a webpage" )

    parser.add_argument ( '-?', dest = 'hrequests', type = str, default = None, action = 'append', required = False, help = 'HTTP request headers' )
    parser.add_argument ( '-u', dest = 'targets', type = str, action = 'append', default = None, required = True, help = 'Url webpage target' )
    parser.add_argument ( '-e', dest = 'extension_requests', type = str, action = 'append', required = False, help = 'Search only files with this extension' )
    parser.add_argument ( '-b', dest = 'basic_auth', type = str, required = False, help = 'Basic http authentication')
    parser.add_argument ( '-t', dest = 'tag_requests', type = str, action = 'append', help = 'Show only request tag from html' )
    parser.add_argument ( '-v', dest = 'verbose', required = False , action = 'store_true', help = 'Show http result code and information about the target')
    parser.add_argument ( '-s', dest = 'save', required = False, default = None, help = 'Save result in a new file')
    parser.add_argument ( '-p', dest = 'printer', action = 'store_true', help = 'Print content obtained from request')
    parser.add_argument ( '--parser', dest = 'parser', type = str, default = 'html5lib', required = False, help = 'BeautifulSoup parser')

    args = parser.parse_args ()
    targets = args.targets
    content = None

    for target in targets :

        print ( '\nSending request for %s ... \n' %target )

        opener, info, code = createhttpreq ( target, preurlopen ( target, args.basic_auth, args.hrequests ) )

        if code == 200 :

            content = gethtmltag ( opener, args.tag_requests, args.extension_requests, args.parser )

            if args.save:
                with open ( args.save , 'w' ) as file:
                    file.write ( content )
            
            if args.printer:
                print ( content )

        if code == 0:
            print ('Page not found!')

        if args.verbose:
            verbose ( target, info, code )

    


main ()
