#! /bin/env python -u
#
# tex2bib.py
#
# Get bib entries from tex file using this amazing global network called the
# world wide web.
#
# Usage: tex2bib.py file names of the tex files to parse
#
# The bib entries are fetched and printed to stdout.
#
# This script is is as KISS as it can be: no crazy error reporting, no logging
# mechanism, no nothing actually. Use it with love, still.

import sys, re, time, urllib2, socket
import arxiv2bib
import argparse
from glob import glob

print "%"
print "% tex2bib at", time.strftime('%X %x %Z')
print "%"

# ------------------------------------------------------------------------------
# Init

#parser = argparse.ArgumentParser(description='Fetch bib citations from tha internet!')
#parser.add_argument('integers', metavar='N', type=int, nargs='+',
#                    help='an integer for the accumulator')
#parser.add_argument('--exclude', dest='accumulate', action='store_const',
#                    const=sum, default=max,
#                    help='sum the integers (default: find the max)')
#
#args = parser.parse_args()
#print args.accumulate(args.integers)

# counting errors is what i've done all my life
errcount = 0
warcount = 0

# recognized citation types (lowercase!)
types = [ 'doi', 'arxiv', 'inspire', 'isbn' ]

if len(sys.argv)==1:
    print "% Error: Please provide at least one input file"
    exit(1)

# get all files (delete duplicates and use glob for wildcards)
filelist = set()
for f in sys.argv[1:]: filelist.update(glob(f))
filelist = list(filelist)

# ------------------------------------------------------------------------------
# Parsing

# the list of citations to fetch
citations = []

# The detected format is xxx:yyy, where xxx defines a type (doi, isbn, etc.) and
# yyy is the corresponding identifier

for f in filelist:

    # get file data
    d = open(f).read()
    # delete latex comments
    d = re.sub(r'%.*', r'', d)

    # get all citations to fetch (split succesive citations separated by commas)
    allmatches = []
    for m in re.finditer(r'\\cite.*?{(.+?)}', d):
        for s in m.group(1).split(','):
            match = re.match(r'((.+?):(.+))', s)
            # check that format xxx:yyy is respected
            if match==None:
                print '% Warning: discarding citation', s
                warcount += 1
            else:
                allmatches.append(match)

    for m in allmatches:

        cit = re.sub(r'^\s', '', m.group(1))

        # strip whitesaces
        e = re.sub(r'\s', '', cit)
        t = re.sub(r'\s', '', m.group(2)).lower() # + lowercase
        i = re.sub(r'\s', '', m.group(3))

        # white spaces are not allowed: warn the user if we find one
        if e!=cit:
            print '% Warning: citation \''+ cit, '\' contains white spaces'

        # check that we have implemented the type
        if t not in types:
            print '% Warning: discarding citation', m.group(1)
            warcount += 1
            continue

        # add to the list if not there yet
        if next((c for c in citations
                   if c['type']==t
                   and c['identifier']==i), 0)==0:
            citations += [{
                'entry': e, 'type' : t, 'identifier' : i,
                }]
            print '% Found citation', e

print

# ------------------------------------------------------------------------------
# Fetching

# We fetch type by type because some servers like to keep the connection alive.
# In particular, keeping the connection alive is feature of arxiv2bib. The
# behaviour is the following: if the fetch succeeds, the entry 'bib' of the
# corresponding citation is created with the correct bib, and if the fetchit
# fails then the entry 'error' is created.

# replace the bibtex identifier with the correct one for a given entry
def replace_id(dat, entry):
    return re.sub(r'@(article|report|inproceedings|phdthesis|book){(.*?),',
                  r'@\1{'+entry+',', dat)

#
# doi
#
for c in [ c for c in citations if c['type']=='doi' ]:

    # fetch from crossref.org
    url = (r'http://search.crossref.org/citation?format=bibtex&doi={}'
            ).format(c['identifier'])
    dat = ''
    try:
        dat = urllib2.urlopen(url, timeout=30).read()
    except socket.timeout, e:
        print "% Error while fetching from crossref.org. Server says:", e
        # server did not answer, do not try crossref anymore
        break
    # replace the bibtex identifier with the correct one
    dat = replace_id(dat, c['entry'])
    # store
    if not dat=='':
        c['bib'] = dat
    else:
        c['error'] = 'can not fetch citation ' + c['entry']

#
# arxiv
#
arxiv_citations = [ c for c in citations if c['type']=='arxiv' ]
# we use arxiv2bib directly
bib = arxiv2bib.arxiv2bib([ c['identifier'] for c in arxiv_citations ])
for (c, b) in zip(arxiv_citations, bib):
    if isinstance(b, arxiv2bib.ReferenceErrorInfo):
        c['error'] = str(b)
    else:
        dat = replace_id(b.bibtex(), c['entry'])
        c['bib'] = dat

#
# inspire
#
for c in [ c for c in citations if c['type']=='inspire' ]:

    # inspire is a bit of a hit-or-miss, since it allows to search using any
    # entry in their database (paper title, ISBN, eprint number etc). However
    # the requested entry must be given in advance. For ease of use we try here
    # to detect the correct entry to be fetched using regexps.
    queryval = c['identifier']

    # tex key (welcome in the 60s)
    if re.search(r'^.*\:\d{4}\w\w\w?$', c['identifier']):
        ref_type = 'texkey'
        queryval = '"'+queryval+'"'
    # arXiv
    elif re.search(arxiv2bib.OLD_STYLE, c['identifier']):
        ref_type = 'eprint'
    elif re.search(arxiv2bib.NEW_STYLE, c['identifier']):
        ref_type = 'eprint'
    # journal ref
    elif re.search(r'^[.\w]+[+][.\w]+[+][.\w]+$', c['identifier']):
        ref_type = 'j'
        queryval = c['identifier'].replace('+', ',')
    # ISBN
    elif re.search(r'^ISBN-.*', c['identifier']):
        ref_type = 'isbn'
        queryval = c['identifier'][len('ISBN-'):]
    # doi
    elif re.search(r'^10[.][0-9]{3,}(?:[.][0-9]+)*/.*', c['identifier']):
        ref_type = 'doi'
    # report number
    elif re.search(r'\w\-\w', c['identifier']):
        ref_type = 'r'
    else:
        c['error'] = 'could not guess reference type for ' + c['identifier']

    # fetch from inspire (they have a doc somewhere...)
    url = (r'http://inspirehep.net/search?p={}:{}&em=B&of=hx&action_search=search'
            ).format(ref_type, queryval)
    dat = urllib2.urlopen(url).read()
    # strip surrounding html
    dat = re.sub(r'<.+?>', r'', dat)
    # check for errors the crude way
    if re.search(r'@(article|report|inproceedings|phdthesis|book)', dat)==None:
        c['error'] = 'inspirehep.net says: ' + dat.replace('\n', '')
    else:
        dat = replace_id(dat, c['entry'])
        c['bib'] = dat

# ------------------------------------------------------------------------------
# Print

# we postpone error reporting for ease of debugging
for c in citations:
    if not 'bib' in c:
        if 'error' in c:
            print '% Error:', c['error']
        else:
            print '% Error: did not fetch citation', c['entry']
        errcount += 1
    else:
        print '% Fetched citation', c['entry']

if errcount>0:
    print
    print '% !!!!! There have been', errcount, 'errors !!!!!'
print
print
print '% ------------------------------------------------------------------------------'
print
print

# finally print these bibtex entries!
for c in citations:
    if 'bib' in c:
        print c['bib']
        print

sys.exit(errcount>0)
