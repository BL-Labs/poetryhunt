from xml.etree import ElementTree as ET
import os, csv, json
from Levenshtein import distance as LD
import numpy as np
import sys
import errno

from burney_data import BurneyDB

STORE = "textareajson"

P_WORDS = ["poem", "poetry", "poet", "verse", "stanza", "sonnet"]
ENC_P_WORDS = [x.encode("utf-8") for x in P_WORDS]

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def store_paper(newspaper, year, obj):
  mkdir_p(os.path.join(STORE, newspaper))
  with open(os.path.join(STORE, newspaper, "{0}.json".format(year)), "w") as ofp:
    json.dump(obj, ofp)
   
def load_paper(newspaper, year):
  with open(os.path.join(STORE, newspaper, "{0}.json".format(year)), "r") as ofp:
    try:
      return json.load(ofp)
    except ValueError as e:
      print(os.path.join(STORE, newspaper, "{0}.json".format(year)))
      return {}

def get_article_list(path):
  return [x for x in os.listdir(path) if x.endswith("xml") and len(x.split("-")) == 3]

def rect_area(rect):
  return (rect[2] - rect[0]) * (rect[3] - rect[1])

def get_rect(areas):
  allocated = 0
  for area in areas:
    allocated += rect_area(area)
  b = list(zip(*areas))
  coord = [min(b[0]), min(b[1]), max(b[2]), max(b[3])]
  return coord, allocated, rect_area(coord)

def drift_correction(datalist):
  gap_mean = np.array([y-x for x,y in zip(datalist, datalist[1:])]).mean()
  return datalist - (np.array(list(range(len(datalist)))) * gap_mean), gap_mean
  
def swankymeanandvarience(datalist):
  if datalist:
    a = np.array(datalist)
    drift_cor_a, gap_mean = drift_correction(a)
    m = drift_cor_a.mean()
    c = drift_cor_a-m
    return (m, (np.dot(c,c) / a.size), gap_mean)
  return (0,0,0)
  
def compute_wobble(lx1, lx2):
  return {'x1': swankymeanandvarience(lx1), 'x2': swankymeanandvarience(lx2)}
  
def get_columns(filename):
  assert(os.path.isfile(filename))
  cols = []
  with open(filename, "r") as fl:
    try:
      r = fl.read()
      doc = ET.fromstring(r)
    except Exception as e:
      print("Corrupt: {0}".format(filename))
      raise e

  y_val = 0
  areas = []
  letters = 0
  trigger = False
  
  lines = {'lx1': [], 'lx2': []}
  lnx2 = []
  lineends = []
  lncur = -10
  lnwidth = 0
  lnstart = 0
  for word in doc.findall("BL_article/image_metadata/articleImage/articleText/articleWord"):
    x1,y1,x2,y2 = [int(x) for x in word.attrib['coord'].split(",")]
    if lncur == -10:
      lncur = y1
      lnstart = y1
      lines["lx1"].append(x1)
    if lnwidth == 0:
      lnwidth = y2-y1
      
    # new line?
    if (y1 != lncur and y1 - lncur > lnwidth) or (y1 - lnstart > lnwidth and x1 - lines["lx1"][-1] < 100):
      # new line!
      lines["lx1"].append(x1)
      lines["lx2"].append(max(lnx2))
      lnwidth = y2-y1 # risky but eh.
      lnstart = y1
  
    if (y_val - y1) > 100:          # should be negative in a column
      # store current column
      maxrect, wordareas, area = get_rect(areas)
      
      # new line!
      lines["lx2"].append(max(lnx2))
        
      cols.append({"box":maxrect, "wordareas":wordareas, 
                   "total":area, "ltcount":letters, "col_mean_and_var": compute_wobble(**lines), "lines": list(zip(lines['lx1'], lines['lx2'])), "trigger": trigger})
    
      # start new column:
      areas = []
      letters = 0
      trigger = False
      
      lines = {'lx1': [], 'lx2': []}
      lines["lx1"].append(x1)
      lnx2 = []
      lncur = y1
      lnwidth = y2-y1 # risky but eh.
      lnstart = y1
      
    if word.text != None:
      T_words = ENC_P_WORDS
      if isinstance(word.text.lower(), str):
        T_words = P_WORDS
      if word.text in T_words or min([LD(word.text.lower(), x) for x in T_words]) < 2:
        trigger = True
      letters += len(word.text)
    areas.append([x1,y1,x2,y2])
    
    lnx2.append(x2)
    lncur = y1
    y_val = y1
  
  # add column
  if areas:
    maxrect, wordareas, area = get_rect(areas)
  else:
    maxrect, wordareas, area = [[], 0, 0]
  
  if lnx2 != []:
    # finish the line
    lines["lx2"].append(max(lnx2))

  cols.append({"box":maxrect, "wordareas":wordareas, 
               "total":area, "ltcount":letters, "col_mean_and_var": compute_wobble(**lines), "lines": list(zip(lines['lx1'], lines['lx2'])), "trigger": trigger})
  return cols
  
if __name__ == "__main__":
  BURNEY_DB = "burney.db"
  
  db = BurneyDB(BURNEY_DB)
  
  with db:
    
    newspapers = "*"
    if len(sys.argv) > 1:
      newspapers = [int(x) for x in sys.argv[1:]]

    if newspapers == "*":
      newspapers = [x['titleAbbreviation'] for x in db.list_all_newspapers()]
      
    for newspaper in newspapers:
      title_md = db.get_title_row(titleAbbreviation = newspaper)
      doc = {}
      year_o = 0
      n_o = ""
      adjusted = False
      for row in db.list_all_entries(title_id = title_md['id']):
        ppath = row['filepath']
        year = row['year']
        month = row['month']
        day = row['day']
        
        if year_o !=0 and year_o != year:
          if adjusted:
            print("STORING {1} -> {0}".format(year_o, n_o))
            store_paper(n_o, year_o, doc)
          else:
            print("Nothing added. Continuing.")
          doc = {}
          year_o = year
          n_o = newspaper
          adjusted = False
          
          if os.path.isfile(os.path.join(STORE, newspaper, "{0}.json".format(year))):
            # file exists...
            print("Previous json file for {0} - {1} exists. Loading.".format(newspaper, year))
            doc = load_paper(newspaper, year)
            adjusted = False
        elif year_o == 0:
          year_o = year
          n_o = newspaper
          if os.path.isfile(os.path.join(STORE, newspaper, "{0}.json".format(year))):
            # file exists...
            print("Previous json file for {0} - {1} exists. Loading.".format(newspaper, year))
            doc = load_paper(newspaper, year)
            adjusted = False
  
        if ppath not in doc:
          print("Rendering out columns for {0} - {3}/{2}/{1}".format(newspaper, year, month, day))
          arts = get_article_list(ppath)
          for art in arts:
            _,pg, artno = art.split("-")
            try:
              if ppath not in doc:
                doc[ppath] = {}
                adjusted = True
              if "{0}_{1}".format(pg,artno[:-4]) not in doc[ppath]:
                doc[ppath]["{0}_{1}".format(pg,artno[:-4])] = get_columns(os.path.join(ppath, art))
                adjusted = True
            except Exception as e:# failed to parse the article XML
              db.mark_corrupt({'newspaper': newspaper,
                              'filepath': ppath,
                              'day': day,
                              'month': month,
                              'year': year,
                              'xmlfile': os.path.join(ppath, art)})
        else:
          print("Done {0} - {3}/{2}/{1} already".format(newspaper, year, month, day))
      print("STORING {0}".format(year))
      store_paper(newspaper, year, doc)