from blnewspaper import *

import json, sys

store = "/cygdrive/d/plaintext"

def fl(newspaper, year, month, day):
  return os.path.join(store, newspaper, year, "{0}_{1}.json".format(month, day))

if not os.path.isdir(store):
  os.mkdir(store)

papers = NEWSPAPERS[::-1]
  
if len(sys.argv) > 1:
  papers = sys.argv[1].split(",")
  
for newspaper in papers:
  a = BLNewspaper(newspaper)
  if not os.path.isdir(os.path.join(store, newspaper)):
    os.mkdir(os.path.join(store, newspaper))
  for year in a.years:
    if not os.path.isdir(os.path.join(store, newspaper, year)):
      os.mkdir(os.path.join(store, newspaper, year))
    for month in a.get_months(year = year):
      for day in a.get_days(year = year, month = month):
        if not os.path.isfile(fl(newspaper, year, month, day)):
          paper = {}
          for page in a.get_pages(year = year, month = month, day = day):
            try:
              paper[page] = a.get_page_text(year = year, month = month, day = day, page = page)
            except Exception as e:
              print("Failed. {0} - {1}: {2}/{3}/{4} - {5}".format(e, newspaper, year, month, day, page))
              raise e
          with open(fl(newspaper, year, month, day), "w") as o:
            json.dump(paper, o)
            print("Stored text for {0}".format(fl(newspaper, year, month, day)))