from build_lookup_cache import lookup
from os.path import isfile, join as osjoin
from os import listdir
import shutil

import csv, codecs

NEWSPAPERMAPPING = {"aberdeenjournal": "ANJO",
                    "birminghamdailypost": "BDPO",
                    "bristolmercury": "BLMY",
                    "baner": "BNER",
                    "belfastnewsletter": "BNWL",
                    "belfastnews-letter": "BNWL",
                    "brightonpatriot": "BRPT",
                    "caledonianmercury": "CNMR",
                    "thecaledonianmercury": "CNMR",
                    "champion": "CHPN",
                    "charter": "CHTR",
                    "chartist": "CHTT",
                    "chartistcircular": "CTCR",
                    "cobbetsweeklypoliticalregister": "CWPR",
                    "cobbets": "CWPR",
                    "dailynews": "DNLN",
                    "derbymercury": "DYMR",
                    "thederbymercury": "DYMR",
                    "theera": "ERLN",
                    "examiner": "EXLN",
                    "graphic": "GCLN",
                    "freemansjournal": "FRJO",
                    "genedl": "GNDL",
                    "goleuad": "GLAD",
                    "glasgowherald": "GWHD",
                    "hampshire/portsmouthtelegraph": "HPTE",
                    "hampshiretelegraphandsussexchronicle": "HPTE",
                    "hampshiretelegraph&amp;portsmouthgazette": "HPTE",
                    "hampshiretelegraphportsmouthgazette": "HPTE",
                    "hampshiretelegraphandsussexchronicleetc": "HPTE",
                    "hullpacket": "HLPA",
                    "hullpacketandoriginalweeklycommercial,literaryandgeneraladvertiser": "HLPA",
                    "hullpacketandhumbermercury": "HLPA",
                    "hullpacketandeastridingtimes": "HLPA",
                    "illustratedpolicenews": "IPNW",
                    "ipswichjournal": "IPJO",
                    "jacksonsoxfordjournal": "JOJL",
                    "leedsmercury": "LEMR",
                    "theleedsmercury": "LEMR",
                    "liverpoolmercury": "LVMR",
                    "lloydsillustratednewspaper": "LINP",
                    "lloydsillustrated": "LINP",
                    "lloydsweeklynewspaper": "LINP",
                    "lloydsweeklylondonnewspaper": "LINP",
                    "londondispatch": "LNDH",
                    "manchestertimes": "MRTM",
                    "themanchestertimes": "MRTM",
                    "manchesterexaminer": "MREX",
                    "themanchesterexaminer": "MREX",
                    "manchesterexaminerandtimes": "MRET",
                    "morningchronicle": "MCLN",
                    "newcastlecourant": "NECT",
                    "northernecho": "NREC",
                    "northernliberator": "NRLR",
                    "northernstar": "NRSR",
                    "northwaleschronicle": "NRWC",
                    "oddfellow": "ODFW",
                    "operative": "OPTE",
                    "pallmallgazette": "PMGZ",
                    "poormansguardian": "PMGU",
                    "prestonchronicle": "PNCH",
                    "reynoldsnewspaper": "RDNP",
                    "southernstar": "SNSR",
                    "trewmansexeterflyingpost": "TEFP",
                    "westernmail": "WMCF",
}

def store_tif_page(fpath, ref):
  topath = "ocrtest/{quality}/{newspaper}/{year}/{month}_{day}_{page}.tif".format(**ref)
  if not isfile(topath):
    shutil.copy(fpath, topath)
  else:
    print("Skipping")

def store_tifs(ref):
  master = lookup(master = True, **ref)
  for item in listdir(master):
    ref["page"] = item.rsplit("-", 1)[-1][:-4]
    print("Storing page {0} - {1}".format(ref['page'], item))
    store_tif_page(osjoin(master, item), ref)
    

class NewspaperAccessError(Exception):
    pass

class NoSuchDocumentFound(NewspaperAccessError):
    pass

class NoSuchPage(NewspaperAccessError):
    pass

def guess_newspaper(newspapertitle):
  shortened = newspapertitle.replace(" ", "").replace("&", "").replace("'", "").replace("-", "").lower()
  if shortened in NEWSPAPERMAPPING:
    return NEWSPAPERMAPPING[shortened]
  elif "the" + shortened in NEWSPAPERMAPPING:
    return NEWSPAPERMAPPING["the"+shortened]
  elif shortened.startswith("the") and shortened[3:] in NEWSPAPERMAPPING:
    return NEWSPAPERMAPPING[shortened[3:]]
  raise NoSuchNewspaper(newspapertitle)

# Month list to convert a name to a number:
MONTHS = {"january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06", 
          "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"}

# a method to open the csv file, read it in and store the references in the list

def get_references(filename):
    
  # Start a list to hold the references
  references = []
   
  with codecs.open(filename, "r", encoding="utf-8") as pcsv:
    
    # this "DictReader" opens the csv file up and then uses the column headers
    # to work out what to call each bit of data
    reflist = csv.DictReader(pcsv)
    
    # now go through each row, adding them to the list
    for row in reflist:
      # a row will be something like:
      #   {"Newspaper": "Glasgow Herald", "Day": "24", "Month": "January", "Year": "1851", Page: "", etc}
        
      # change the month to be a number, not a name:
      row['newspaper'] = guess_newspaper(row['newspaper'])
      row["month"] = MONTHS.get(row['month'].lower().strip(), row['month'])
      row["day"] = "{0:02d}".format(int(row["day"]))
      row["year"] = row["year"].strip()
      row["quality"] = row["quality"].strip()
      # we also don't need the article title so remove this:
      # del row['article title']
      references.append(row)
  return references

  
if __name__ == "__main__":
  d = get_references("ocrtest/curatedocr.csv")
  for ref in d:
    print("Starting with {quality}: {newspaper}, {year}/{month}/{day}".format(**ref))
    fpath = lookup(**ref)
    if not fpath:
      print ref
    else:
      store_tifs(ref)
  #    store_tif_page(fpath, ref)
      print("Stored {0}".format(fpath))