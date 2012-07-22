#FORMAT python
# -*- coding: UTF-8 -*-
"""
   MoinMoin - Simple bibtex parser

   Based on Matt Cooper's keyval parser
  
   Copyright: 2012 by Laurent Perrinet
   Copyright: 2010 by Ryota Tomioka
   Copyright: 2006 by Matt Cooper <macooper@vt.edu>
   License: GNU GPL
   Version: 1.0
"""
import re
from MoinMoin import wikiutil


def latex2unicode(str):
    tab = {"\\\"u": "&uuml;",
           "\\\"o": "&ouml;",
           "\\\"e": "&euml;",
           "\\\"a": "&auml;",
           "\\o"  : "&oslash;",
           "\\O"  : "&Oslash;",
           "~"    : " ",
           "\\'e" : "&eacute;",
           "\\'E" : "&Eacute;",
           "\\`e" : "&egrave;"}

    for key in tab.keys():
        str = str.replace(key, tab[key])
    return str

def removepar(str):
    str = str.replace("{","").replace("}","")
    return str

class Bibitem:
    def __init__(self):
        self.bib = {"title":"", "author":"", "year":"", "url":""}

    def setValue(self, key, val):
        if key.lower().strip() in self.bib.keys() and not(self.bib[key.lower().strip()]==""):
            key_ = key.lower().strip()
            tmp = self.bib[key_]
            self.bib[key_] += ' + ' + removepar(val.lstrip('" ').rstrip(' ",'))
        else:
            self.bib[key.lower().strip()] = removepar(val.lstrip('" ').rstrip(' ",'))

    # TODO: include abstract by unfolding it 
    # TODO: include bibtex entry by unfolding it 
    # TODO: better format instread of one line at a time
    # TODO: include DOI and link
    # TODO: remove duplicate entries
    # TODO: include citeulike links


    def isReady(self):
        return len(self.bib["author"])>0 and len(self.bib["title"])>0 and len(self.bib["year"])>0

    def format_author(self):
        authors = self.bib["author"].split(" and ")
        result = []
        for author in authors:
            result.append(latex2unicode(author.strip()))
        return ", ".join(result)+"." # TODO: reverse Firstname, Lastname and write and at the end 

    def format_title(self):
        title = latex2unicode(self.bib["title"])
        tmp = "<u>%s</u>" % (title)

    # TODO: title is a link to the first URL encountered


#         return "<a href=\"%s\">%s</a>." % (self.bib["url"], title)
        if not(self.bib["url"]==""):
#             return "<u>%s</u>, <a href=\"%s\">URL</a>." % (title, self.bib["url"])
            tmp += ", "
            for i_url, url in enumerate(self.bib["url"].split('+')):
                number = ""
                if i_url>1: number = str(i_url+1)
                tmp += "<a href=\"%s\">URL%s</a> " % (url.strip(), number)
            tmp += '.'
            return tmp

        else:
            return tmp + '.'


class BibitemJournal(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["journal"]=""
        self.bib["volume"]=""
        self.bib["number"]=""
        self.bib["pages"]=""

    def format(self):
        if len(self.bib["title"])>0:
            return "<li>%s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_journal(), self.format_volnumpages(), self.bib["year"])
        else:
            return ""

    def format_journal(self):
        if len(self.bib["journal"])>0:
            return "<i>%s</i>," % (self.bib["journal"])
        else:
            return ""

    def format_volnumpages(self):
        result = ""
        if len(self.bib["volume"])>0:
            result += "<b>%s</b>" % self.bib["volume"]
        if len(self.bib["number"])>0:
            result += "(%s)" % self.bib["number"]
        if len(self.bib["pages"])>0:
            result += ":%s," % self.bib["pages"]
        elif len(result)>0:
            result += ","
        return result

class BibitemBook(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["publisher"]=""
        self.bib["address"]=""

    def format(self):
        if len(self.bib["title"])>0:
            return "<li>%s <i>%s</i> %s %s.</li>" % (self.format_author(), self.format_title(), self.format_pubadd(), self.bib["year"])
        else:
            return ""
        
    def format_pubadd(self):
        result=""
        if len(self.bib["publisher"])>0:
            result += "%s," % self.bib["publisher"]
        if len(self.bib["address"])>0:
            result += " %s," % self.bib["address"]
        return result

class BibitemTechreport(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["institution"]=""

    def format(self):
        if len(self.bib["title"])>0:
            return "<li>%s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_institution(), self.bib["year"])
        else:
            return ""

    def format_institution(self):
        if len(self.bib["institution"])>0:
            return "Technical report, %s," % self.bib["institution"]
        else:
            return ""

class BibitemInCollection(BibitemBook):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["booktitle"]=""
        self.bib["pages"]=""
        self.bib["publisher"]=""
        self.bib["address"]=""

    def format(self):
        if len(self.bib["title"])>0:
            return "<li>%s %s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_booktitle(), self.format_pages(), self.format_pubadd(), self.bib["year"])
        else:
            return ""

    def format_booktitle(self):
        if len(self.bib["booktitle"])>0:
            return "In <i>%s</i>," % self.bib["booktitle"]
        else:
            return ""

    def format_pages(self):
        if len(self.bib["pages"])>0:
            return "pages %s." % self.bib["pages"]
        else:
            return ""

       
class Parser:
    """
        Key-value pairs parser
        "Key" is anything before the delimiter,
        "Value" is everything after (including more delimiters)
        If a delimiter isn't found, the line is not turned into a key-value pair
    """
    
    parsername = "KeyValueParser"
    
    def __init__(self, raw, request, **kw):
        self.request = request
        self.form = request.form
        self.raw = raw
        self._ = request.getText
        self.args = kw.get('format_args', '')
    
        attrs, msg = wikiutil.parseAttributes(request, self.args)
        self.delim = attrs.get('delim', '')[1:-1]


    def format(self, formatter):
        linesep   = "\n"
        delimiter = self.delim or "="
        
        # split the raw input into lines
        lines = self.raw.split("\n")
        
        bib=None
        result = []
        while lines:
            line = lines.pop(0)
            if len(line.strip())>0 and line.strip()[0]=="@": # bibitem type
                # Output the last bibitem
                if bib is not None:
                    result.append(bib.format())

                # New bibitem begins
                type = line[1:-1].split("{",1)[0]
                if type.lower()=="incollection" or type.lower()=="inproceedings" or type.lower()=="conference":
                    bib=BibitemInCollection()
                elif type.lower()=="book":
                    bib=BibitemBook()
                elif type.lower()=="techreport":
                    bib=BibitemTechreport()
                else:
                    bib=BibitemJournal()

            elif line.find(delimiter) > -1:
                (k, v) = line.split(delimiter, 1)

                if bib is not None:
                    bib.setValue(k, v)
                else:
                    result.append("Strange line [%s] found\n" % line)

            # if there is no delimiter...
            else:
                if bib is not None and bib.isReady():
                    result.append(bib.format())
                    bib = None

        if bib is not None:
            result.append(bib.format())

        self.raw = "<ul>\n%s</ul>\n" % linesep.join(result)
        self.request.write(formatter.rawHTML(self.raw))
