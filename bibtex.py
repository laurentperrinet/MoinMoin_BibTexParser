#FORMAT python
# -*- coding: UTF-8 -*-
"""

A parser to display bibtex code with a nice formatting within MoinMoin wiki pages.

The parsing is done in pure pytho, so that you will not need external programs. This 
parser script should work for MoinMoin 1.9.3.
   
   Copyright: 2012 by Laurent Perrinet -- see https://github.com/meduz/MoinMoin_BibTexParser
   Copyright: 2010 by Ryota Tomioka -- see http://moinmo.in/ParserMarket/SimpleBibtex
   Based on Matt Cooper's keyval parser Copyright: 2006 by Matt Cooper <macooper@vt.edu>
   
   License: GNU GPL
   
   Version: 1.0

"""
import re
from MoinMoin import wikiutil

show_hide = """
<script language="javascript"> 
function toggle() {
    var ele = document.getElementById("toggleText");
    var text = document.getElementById("displayText");
    if(ele.style.display == "block") {
            ele.style.display = "none";
        text.innerHTML = "show";
    }
    else {
        ele.style.display = "block";
        text.innerHTML = "hide";
    }
} 
</script>
"""

show_hide_old = """
<script type="text/javascript">
function hideshow(which){
if (!document.getElementById)
return
if (which.style.display=="block")
which.style.display="none"
else
which.style.display="block"
}
</script>

"""

def latex2unicode(str):
    # translation dictionary
    tab = {"\\\"u": "&uuml;",
           "\\\"o": "&ouml;",
           "\\\"e": "&euml;",
           "\\\"a": "&auml;",
           "\\o"  : "&oslash;",
           "\\O"  : "&Oslash;",
           "~"    : " ",
           "\\'e" : "&eacute;",
           "\\'E" : "&Eacute;",
           "\\`e" : "&egrave;",
           "\\`E" : "&Egrave;",
           }

    for key in tab.keys():
        str = str.replace(key, tab[key])
        str = str.replace("{" + key + "}", tab[key])# case where the character is enclosed in curly brackets
    return str

def removepar(str):
    str = str.replace("{", "").replace("}", "")
    return str

class Bibitem:
    def __init__(self):
        # fields common to all entries
        self.bib = {"title":"", "author":"", "year":"", "url":"", "abstract":""}

    def setValue(self, key, val):
        if key.lower().strip() in self.bib.keys() and not(self.bib[key.lower().strip()] == ""):
            key_ = key.lower().strip()
            tmp = self.bib[key_] # ????
            self.bib[key_] += ' + ' + removepar(val.lstrip('" ').rstrip(' ",'))
        else:
            self.bib[key.lower().strip()] = removepar(val.lstrip('" ').rstrip(' ",'))

    # TODO: include bibtex entry by unfolding it 
    # TODO: better handle format instead of one line at a time
    # TODO: include DOI and link
    # TODO: remove duplicate entries
    # TODO: include citeulike links


    def isReady(self):
        return len(self.bib["author"]) > 0 and len(self.bib["title"]) > 0 and len(self.bib["year"]) > 0

    def format_author(self):
        authors = self.bib["author"].split(" and ")
        result = []
        for author in authors:
            if "," in author:
                # TODO: handle the more complex cases?
                name, surname = author.split(", ")
                author = surname + " " + name
            result.append(latex2unicode(author.strip()))
        return ", ".join(result)+"."

    def format_abstract(self):
        result = self.bib["abstract"]
        # TODO: include abstract by unfolding it 
#         tmp = '<a href="javascript:hideshow(document.getElementById("%s"))">abstract</a>' % self.bib["author"]
#         tmp += '<div id="%s" style="font:12px ; display: block"> %s </div>' % (self.bib["author"], result)

        tmp = '<a id="displayText" href="javascript:toggle();">abstract</a>'
        tmp += '<div id="toggleText" style="display: none"> %s </div>' % result
        return tmp
#    return "<i> %s </i> " % result
#         return "<p style=\"font-size:x-small;\"> %s </p> " % result

    def format_title(self):
        title = latex2unicode(self.bib["title"])
        tmp = "<u>%s</u>" % (title)

        # TODO: title is a link to the first URL encountered
        if not(self.bib["url"] == ""):
#             return "<u>%s</u>, <a href=\"%s\">URL</a>." % (title, self.bib["url"])
            tmp += ", "
            for i_url, url in enumerate(self.bib["url"].split('+')):
                number = ""
                if i_url > 0: number = str(i_url+1)
                tmp += "<a href=\"%s\">URL%s</a> " % (url.strip(), number)
            tmp += '.'
            return tmp

        else:
            return tmp + '.'


class BibitemJournal(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["journal"] = ""
        self.bib["volume"] = ""
        self.bib["number"] = ""
        self.bib["pages"] = ""

    def format(self):
        if len(self.bib["title"]) > 0:
            #return "<li>%s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_journal(), self.format_volnumpages(), self.bib["year"])
            return "<li>%s %s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_journal(), self.format_volnumpages(), self.bib["year"], self.format_abstract())
        else:
            return ""

    def format_journal(self):
        if len(self.bib["journal"]) > 0:
            return "<i>%s</i>," % (self.bib["journal"])
        else:
            return ""

    def format_volnumpages(self):
        result = ""
        if len(self.bib["volume"]) > 0:
            result += "<b>%s</b>" % self.bib["volume"]
        if len(self.bib["number"]) > 0:
            result += "(%s)" % self.bib["number"]
        if len(self.bib["pages"]) > 0:
            result += ":%s," % self.bib["pages"]
        elif len(result) > 0:
            result += ","
        return result

class BibitemBook(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["publisher"] = ""
        self.bib["address"] = ""

    def format(self):
        if len(self.bib["title"]) > 0:
            return "<li>%s <i>%s</i> %s %s.</li>" % (self.format_author(), self.format_title(), self.format_pubadd(), self.bib["year"])
        else:
            return ""

    def format_pubadd(self):
        result = ""
        if len(self.bib["publisher"]) > 0:
            result += "%s," % self.bib["publisher"]
        if len(self.bib["address"]) > 0:
            result += " %s," % self.bib["address"]
        return result

class BibitemTechreport(Bibitem):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["institution"] = ""

    def format(self):
        if len(self.bib["title"]) > 0:
            return "<li>%s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_institution(), self.bib["year"])
        else:
            return ""

    def format_institution(self):
        if len(self.bib["institution"]) > 0:
            return "Technical report, %s," % self.bib["institution"]
        else:
            return ""

class BibitemInCollection(BibitemBook):
    def __init__(self):
        Bibitem.__init__(self)
        self.bib["booktitle"] = ""
        self.bib["pages"] = ""
        self.bib["publisher"] = ""
        self.bib["address"] = ""

    def format(self):
        if len(self.bib["title"]) > 0:
#             return "<li>%s %s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_booktitle(), self.format_pages(), self.format_pubadd(), self.bib["year"])
            return "<li>%s %s %s %s %s %s %s.</li>" % (self.format_author(), self.format_title(), self.format_booktitle(), self.format_pages(), self.format_pubadd(), self.bib["year"], self.format_abstract())
        else:
            return ""

    def format_booktitle(self):
        if len(self.bib["booktitle"]) > 0:
            return "In <i>%s</i>," % self.bib["booktitle"]
        else:
            return ""

    def format_pages(self):
        if len(self.bib["pages"]) > 0:
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

    parsername = "BibTex"

    def __init__(self, raw, request, **kw):
        self.request = request
        self.form = request.form
        self.raw = raw
        self._ = request.getText
        self.args = kw.get('format_args', '')

        attrs, msg = wikiutil.parseAttributes(request, self.args)
        self.delim = attrs.get('delim', '')[1:-1]


    def format(self, formatter):
        linesep = "\n"
        delimiter = self.delim or "="

        # split the raw input into lines
        lines = self.raw.split("\n")

        bib = None
        result = []
        while lines:
            line = lines.pop(0)
            line = latex2unicode(line)
            if len(line.strip()) > 0 and line.strip()[0] == "@": # bibitem type
                # Output the last bibitem
                if bib is not None:
                    result.append(bib.format())

                # New bibitem begins
                bibitem_type = line[1:-1].split("{", 1)[0] # the type is the string between "@" and "{" and we drop the rest (hoping we end the line after the citekey and ",")
                bibitem_type = bibitem_type.lower()
                if bibitem_type == "incollection" or bibitem_type == "inproceedings" or bibitem_type == "conference":
                    bib = BibitemInCollection()
                elif bibitem_type == "book":
                    bib = BibitemBook()
                elif bibitem_type == "techreport":
                    bib = BibitemTechreport()
                else:
                    bib = BibitemJournal()

            elif line.find(delimiter) > -1: # we found a line with a "=" sign
                (k, v) = line.split(delimiter, 1)
                while (v.count('{') - v.count('}')) > 0:
                    line = lines.pop(0)
                    #line = latex2unicode(line)
                    v += line
                v = v.strip('\n')

                if bib is not None:
                    bib.setValue(k, v)
                else:
                    result.append("Strange line [%s] found\n" % line)

            # if there is no delimiter, we append the proper formatting of the bibitem to the results:
            else:
                if bib is not None and bib.isReady():
                    result.append(bib.format())
                    bib = None

        if bib is not None:
            result.append(bib.format())
        self.raw = show_hide
        self.raw += "<ul>\n%s</ul>\n" % linesep.join(result)
        self.request.write(formatter.rawHTML(self.raw))

