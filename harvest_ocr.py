import csv, os, shutil

from jisc1_locations import SHARES, JISC1_LOCATIONS

N_FOLDERS = {}

STORE = "."
MISSINGPAGE_TOLERANCE = 3


def page_to_file_guess(n, y, m, d, page, prefix="WO1"):
  base = "_".join([prefix, n, y, m, d])
  return base + "-%04d" % page

def page_to_xml_guess(n,y,m,d,page, prefix="WO1"):
  return page_to_file_guess(n,y,m,d,page,prefix) + ".xml"

def get_newspaper_root(newspaper):
  l = os.path.join(STORE, newspaper)
  if newspaper in N_FOLDERS:
    return l
  if not os.path.isdir(l):
    os.mkdir(l)
  N_FOLDERS[newspaper] = []
  return l

def get_store(newspaper, year):
  n_root = get_newspaper_root(newspaper)
  l = os.path.join(n_root, year)
  if year in N_FOLDERS[newspaper]:
    return l
  if not os.path.isdir(l):
    os.mkdir(l)
  N_FOLDERS[newspaper].append(year)
  return l

if __name__ == "__main__":
  for share in SHARES:
    setheaders = os.path.isfile(share+".log")
    logf = open(share+".log", "a+")
    logfc = csv.writer(logf)
    if setheaders:
      logfc.writerow(["newspaper", "year", "month", "day", "pages"])
    with open(share+".csv", "r") as csvfile:
      doc = csv.reader(csvfile)
      for row in doc:
        i = 1
        missed = 0
        page_root, newspaper, year, month, day = row
        cpyto = get_store(newspaper, year)
        while(missed<MISSINGPAGE_TOLERANCE):
          xmlpage = page_to_xml_guess(newspaper, year, month, day, i, "WO2")
          location = os.path.join(page_root, xmlpage)
          if not os.path.isfile(os.path.join(cpyto, xmlpage)):
            if os.path.isfile(location):
              missed = 0
              print("Copying to NAS - {0}".format(xmlpage))
              shutil.copy(location, os.path.join(cpyto, xmlpage))
            else:
              missed +=1
          else: 
            print("Already got - {0}".format(xmlpage))
          i+=1
        # log page captures
        logfc.writerow([newspaper, year, month, day, str(i-missed)])
