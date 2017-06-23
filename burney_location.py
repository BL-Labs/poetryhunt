import os
from burney_data import BurneyDB
from xml.etree import ElementTree as ET

# Speedup os.walk by importing the py 3.5 version
from scandir import scandir, walk

BURNEY_DB = "burney.db"

ROOT = "/cygdrive/w/APEX"

_root_host = "p8l-nas2"

SHARES = ["burney/APEX"]

LOCATIONS = ["//{0}/{1}".format(_root_host, x) for x in SHARES]

def get_metadata(doc, xpath = "BL_page/title_metadata"):
  md = {}
  el = doc.find(xpath)
  for item in el.getchildren():
    md[item.tag] = item.text
  return md

def handle_page_metadata(filepath, conn):
  with open(filepath, "r") as f:
    try:
      doc = ET.fromstring(f.read())
      tm_d = get_metadata(doc, "BL_page/title_metadata")
      title_id = conn.add_title_row(tm_d)
      tm_d['id'] = title_id
    
      issue_d = get_metadata(doc, "BL_page/issue_metadata")
      issue_d['title_id'] = title_id
      issue_id = conn.add_issue_row(issue_d)
      issue_d['id'] = issue_id
    except (UnicodeDecodeError, ET.ParseError) as e:
      print("Corrupt text in {0}".format(filepath))
      raise e
    
  return tm_d, issue_d

def add_service_dir_to_db(t_md, i_md, year, month, day, dirpath, fns, conn):
  pkg = {}
  pkg['number_of_articles'] = len([x for x in fns if x.endswith("xml") and x.count("-") == 2])
  pkg['filepath'] = dirpath
  pkg['year'] = year
  pkg['month'] = month
  pkg['day'] = day
  pkg['title_id'] = t_md['id']
  pkg['issue_id'] = i_md['id']

  conn.add_service_dir(pkg)

def scan_for_service_dirs(root, conn):
  title = ""
  onewspaper = ""
  oyear = ""
  skipping = False
  
  # short stop for profiling reasons:
  #scans = 40
  
  for (dirpath, subdirs, fns) in walk(root):
    if dirpath.endswith("service"):
      _, newspaper, year, month, day, service = dirpath.rsplit("/", 5)
      
      #profiling short circuit
      #scans -= 1

      if conn.scanned(dirpath, skipping) != True:
      # first xml that corresponds to page scan 0001
        pageone_file = [x for x in fns if x.endswith("0001.xml")]
        if pageone_file:
          pageone = os.path.join(dirpath, pageone_file[0])
          try:
            t_md, i_md = handle_page_metadata(pageone, conn)
            if t_md['title'] != title:
              print("----- '{title}', ({datesOfPublication}) (Abbr: {titleAbbreviation}) -----".format(**t_md))
              title = t_md['title']
              conn.commit()
            if oyear != year:
              print(year)
              oyear = year
            add_service_dir_to_db(t_md, i_md, year, month, day, dirpath, fns, conn)
            #print(dirpath, t_md['titleAbbreviation'], year, month, day)
          except (UnicodeDecodeError, ET.ParseError) as e:
            conn.mark_corrupt({'filepath': dirpath, 'day': day, 'month':month, 'year':year, 'newspaper': newspaper, 'xmlfile': pageone.split("/")[-1]})
            
        else:
          print("Couldn't find a relevant page one in {0}".format(dirpath))
          print(fns)
          conn.mark_corrupt({'filepath': dirpath, 'day': day, 'month':month, 'year':year, 'newspaper': newspaper, 'xmlfile': "NOT FOUND"})
      else:
        if not skipping:
          print("Skipping directories already scanned")
          skipping = True
        if onewspaper != newspaper:
          print(newspaper)
          onewspaper = newspaper
  
    # short scan for profiling.
    #if scans == 0:
    #  break    
  conn.commit()

if __name__ == "__main__":
  create = False
  if not os.path.isfile(BURNEY_DB):
    create =  True
  
  conn = BurneyDB(BURNEY_DB)
  
  with conn:
    conn.create_tables(create)
    
    scan_for_service_dirs(ROOT, conn)
    