# -*- coding: utf-8 -*-
import os, csv, re, sys

from shutil import copyfile

from newspaperaccess import NewspaperArchive, NoSuchNewspaper, NoSuchDocumentFound

from Levenshtein import distance as L_distance

L_THRESHOLD = 1.9  # length of title / L distance. Bigger = better.

REFLIST = "positives.csv"

if len(sys.argv) > 1:
    REFLIST = sys.argv[1]

NEWLIST = "{0}_inprogress.csv".format(REFLIST[:-4])

if os.path.isfile(NEWLIST):
    # continue working on in progress list
    REFLIST = NEWLIST
    NEWLIST = "_" + NEWLIST

HEADERS = ["newspaper", "day", "month", "year", "page", "article", "article title", "ocr title", "match (title/article text/manual)"]

n = NewspaperArchive()

def title_match(a, b):
    # first, see if there is a direct match
    # lower case it all too             
    if re.search(re.escape(b.lower()), a.lower()) != None:
        return True
    
    # then see if there is something within a set L ratio
    l_ratio = float(len(a)) / L_distance(a.lower(), b.lower())
    if l_ratio > L_THRESHOLD :
        return True
    
def find_article_ref(ref):
    lref = {x: y for x,y in row.items() if x.lower() != "page"} # day level references
    if lref['article title'].strip() == "":
        #print("No article title given for {0}".format(ref))
        return "", "", "", ""
    try:
        doc = n.get(**lref)
        for page in doc:
            for article_no, (a_title, arttext) in [(x, doc[page][x]) for x in doc[page]]:
                if a_title != "" and a_title != None:
                    if title_match(a_title, lref['article title']):
                        return page, article_no, a_title, "title"
                    else:
                        # try the first part of the article, in case
                        if arttext.startswith(a_title):
                            if title_match(arttext[len(a_title)-1: len(a_title) + len(lref['article title']) + 5], lref['article title']):
                                return page, article_no, a_title, "article"
                            else:
                                if title_match(arttext[: len(lref['article title']) + 5], lref['article title']):
                                    return page, article_no, a_title, "article"
        # no automatic matches - manual?
        print("\n\nArticle title is : '{0}'\n".format(lref['article title']))
        arts = {}
        
        for page in doc:
            for article_no, (a_title, arttext) in [(x, doc[page][x]) for x in doc[page]]:
                arts[article_no] = (page, a_title, arttext)
                
        def print_article_list(full = False):
            print("Newspaper: {newspaper} {day}/{month}/{year}\n".format(**lref))
            for item in sorted(arts.keys()):
                if full:
                    if arts[item][1] != None:
                        print("pg {3} art {0}\t\t{1} ... '{2}'\n".format(item, arts[item][1], arts[item][2][:380], arts[item][0]))
                    else:
                        print("pg {3} art {0}\t\t{1} ... '{2}'\n".format(item, ".", arts[item][2][:380], arts[item][0]))
                else:
                    if arts[item][1] != None:
                        print("pg {2} art {0}\t\t{1}\t\tArticle length: {3} chars".format(item, arts[item][1], arts[item][0], len(arts[item][2])))
                    else:
                        print("pg {2} art {0}\t\t{1}\t\tArticle length: {3} chars".format(item, ".", arts[item][0], len(arts[item][2])))

        
        art = "FOO"

        print_article_list()
        print("\n   'l' - list article titles again, 'm' - article titles with more from article text")
        print("   'mXXX' - read OCR text for the XXX article, eg 'm015'")
        while art != "" and art not in arts and art != "q":
            if art.startswith("m") and art[1:] in arts:
                print("\n{0}".format(arts[art[1:]][2]))
            elif art == "m":
                print_article_list(full = True)
            elif art == "l":
                print_article_list(full = False)
            art = input("\n\nAny matches? ").strip()
            
        if art != "" and art in arts:
            return arts[art][0], art, arts[art][1], "manual"
        elif art == "q":
            return art
        return "", "", "", ""
                      
    except NoSuchNewspaper as e:
        print("No such newspaper found for '{0}'".format(ref))
        ...
    except NoSuchDocumentFound as e:
        print("No newspaper issue found for '{0}'".format(ref))
        ...
    
    # couldn't match? :(
    return "", "", "", ""

from feature import get_references

doc = get_references(REFLIST)

import codecs

# now overwrite the original with the new
def writeout():
    #if REFLIST == "_" + NEWLIST:
    copyfile(NEWLIST, REFLIST)
    #os.remove(NEWLIST)
        

with codecs.open(NEWLIST, "w", encoding = "utf-8") as nfp:
    ndoc = csv.DictWriter(nfp, fieldnames = HEADERS)
    ndoc.writerow({h:h for h in HEADERS})
    BAILOUT="notq"
    for row in doc:
        if BAILOUT == "q":
            for field in ["article", "page", "ocr title", "match (title/article text/manual)"]:
                row[field] = row.get(field, "")
            ndoc.writerow(row)
        elif "ocr title" in row and row["ocr title"] != "":
            print("Matched previously: {0} ({1}/{2}/{3}) - pg{4}/art:{5}".format(row['newspaper'], row['year'], row['month'], row['day'], row['page'], row['article']))
            ndoc.writerow(row)
        else:
            ans = find_article_ref(row)
            if ans == "q":
                for field in ["article", "page", "ocr title", "match (title/article text/manual)"]:
                    row[field] = row.get(field, "")
                ndoc.writerow(row)
                BAILOUT = "q"
            else:
                row["page"], row["article"], row["ocr title"], row["match (title/article text/manual)"] = ans 
                if row['article'] != "":
                    print("Match: '{0}' {1} for search {2}".format(row["ocr title"], (row['newspaper'], row['year'], row['month'], row['day']), row['article title']))
                ndoc.writerow(row)
print("Writing out to file")
writeout()
