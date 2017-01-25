#
# bib_from_tex.py
#
# Get bib entries from tex file using this amazing global network called the
# world wide web.
#
# Usage: bib_from_tex.py file names of the tex files to parse
#
# The bib entries are fetched and printed to stdout.

import sys, re, time, urllib2
from glob import glob

print "%"
print "% bib_from_tex.py at", time.strftime('%X %x %Z')
print "%"

# ------------------------------------------------------------------------------
# Init

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
    try:
        d = open(f).read()
    except IOError as e:
        print "Error: can not open or read file {0}: {1}".format(f, e.strerror)

    # get all citations to fetch
    allmatches = re.finditer(r'\\cite\s*{((.+?):(.+?))}', d)

    for m in allmatches:

        # strip whitesaces
        t = ''.join(m.group(2).split()) # strip all whitespaces
        i = ''.join(m.group(3).split())

        # add to the list if not there yet
        if next((c for c in citations
                 if c['type']==t and c['identifier']==i), 0)==0:
            citations += [{
                'entry' : m.group(1), 'type' : t, 'identifier' : i
                }]
            print '% Found citation', m.group(1)

print

# ------------------------------------------------------------------------------
# Fetching

for c in citations:

    #
    # doi
    #
    if(c['type']=='doi'):
        # fetch
        url = (r'http://search.crossref.org/citation?format=bibtex&doi={}'
                ).format(c['identifier'])
        dat = urllib2.urlopen(url).read()
        # replace the bibtex identifier with the correct one
        dat = re.sub(r'@article{(.*?),', r'@article{'+c['entry']+',', dat)
        # store
        c['bib'] = dat

        print '% Fetched citation', c['entry']

print

# ------------------------------------------------------------------------------
# Print

for c in citations:
    print c['bib']
    print
