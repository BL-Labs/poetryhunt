from xml.etree import ElementTree as ET
import os, csv, json

from burney_data import BurneyDB

import sys

STORE = "articleleveljson"

class CorruptXML(Exception):
  pass

def store_paper(newspaper, year, month, day, obj):
  os.makedirs(os.path.join(STORE, newspaper, year), exist_ok = True)
  with open(os.path.join(STORE, newspaper, year, "{0}_{1}.json".format(month, day)), "w") as ofp:
    json.dump(obj, ofp)

def get_page_text(filename):
  assert(os.path.isfile(filename))
  text = []
  with open(filename, "r") as fl:
    try:
      r = fl.read()
      doc = ET.fromstring(r)
    except Exception as e:
      raise CorruptXML
    title = ""
    # try to get the article title...?
    title_ele = doc.find("BL_article/article_metadata/dc_metadata/{http://purl.org/dc/elements/1.1/}Title")
    if title_ele != None:
      title = title_ele.text
    for words in doc.findall("BL_article/image_metadata/articleImage/articleText/articleWord"):
      text.append(words.text)
  return title, " ".join([x for x in text if x])

def get_article_list(path):
  return [x for x in os.listdir(path) if x.endswith("xml") and len(x.split("-")) == 3]
  
if __name__ == "__main__":
  BURNEY_DB = "burney.db.fullscan"
  
  db = BurneyDB(BURNEY_DB)
  
  with db:
    newspapers = [x['titleAbbreviation'] for x in db.list_all_newspapers()]
      
    for newspaper in newspapers:
      title_md = db.get_title_row(titleAbbreviation = newspaper)
      for row in db.list_all_entries(title_id = title_md['id']):
        ppath = row['filepath']
        year = row['year']
        month = row['month']
        day = row['day']
        
        if not os.path.isfile(os.path.join(STORE, newspaper, year, "{0}_{1}.json".format(month, day))):
          print("Rendering out text for {0} - {3}/{2}/{1}".format(newspaper, year, month, day))
          arts = get_article_list(ppath)
          doc = {}
          for art in arts:
            _,pg, artno = art.split("-")
            try:
              doc["{0}_{1}".format(pg, artno[:-4])] = get_page_text(os.path.join(ppath, art))
            except CorruptXML as e:
              # failed to parse the article XML
              db.mark_corrupt({'newspaper': newspaper,
                              'filepath': ppath,
                              'day': day,
                              'month': month,
                              'year': year,
                              'xmlfile': os.path.join(ppath, art)})
          store_paper(newspaper, year, month, day, doc)
        else:
          print("Done {0} - {3}/{2}/{1} already".format(newspaper, year, month, day))