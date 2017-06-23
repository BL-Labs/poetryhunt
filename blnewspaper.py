from xml.etree import ElementTree as ET
import os
from collections import defaultdict

NEWSPAPERS = ["ANJO", "BDPO", "BLMY", "BNER", "BNWL", "BRPT", "CHPN", "CHTR", "CHTT", "CNMR", "CTCR", "CWPR", "DNLN", "DYMR", "ERLN", "EXLN", "FRJO", "GCLN", "GLAD", "GNDL", "GWHD", "HLPA", "HPTE", "IPJO", "IPNW", "JOJL", "LEMR", "LINP", "LNDH", "LVMR", "MCLN", "MRTM", "NECT", "NREC", "NRLR", "NRSR", "NRWC", "ODFW", "OPTE", "PMGU", "PMGZ", "PNCH", "RDNP", "SNSR", "TEFP", "WMCF"]

pageWord_regex = r"""^<pageWord coord="[0-9]+\,[0-9]+\,[0-9]+\,[0-9]+">[^<]*</pageWord>"""

class BLNewspaper(object):
  def __init__(self, newspaper = "ANJO", load_available_years = True, paper_root_dir = "."):
    if newspaper not in NEWSPAPERS:
      raise Exception("{0} is not a newspaper code in the archive".format(newspaper))
    self.newspaper = newspaper
    self.clear_date()
    
    self._archive = paper_root_dir
  
    self._data = self._fingerprint(newspaper = newspaper)
    
    if load_available_years:
      self._load_available_years()
  
  def _fingerprint(self, **kw):
    return {k: kw.get(k, self._data.get(k)) for k in ['newspaper', 'year', 'month', 'day', 'page']}

  def cursor(self):
    data = self._fingerprint()
    print("Newspaper:  '{0}'\nYear:  '{1}'\nMonth:  '{2}'\nDay:  '{3}'\nPage:  '{4}'".format(*[data.get(k, "") for k in ['newspaper', 'year', 'month', 'day', 'page']]))
    
  def decode_filename(self, filename):
    s = ""
    fn = filename.split("_")
    d = fn[4].split("-")[0]
    suffix = fn[-1].split("-")
    page = suffix[-1].split(".")[0]  # "aio_s_dj...oa_sjod-0001.xml" ==> "0001"
    if d != suffix[0]:
      s = suffix[0]
    return [fn[1], fn[2], fn[3], d, page, s]
    
  def encode_filename(self, prefix = "WO1", **kw):
    p = self._fingerprint(**kw)
    if kw.get('page','').lower().startswith("s") or kw.get('page','').lower().startswith("v"):
      return os.path.join(self._archive, p['newspaper'], p['year'], "{5}_{0}_{1}_{2}_{3}_{4}.xml".format(p['newspaper'], p['year'], p['month'], p['day'], p['page'], prefix))
    return os.path.join(self._archive, p['newspaper'], p['year'], "{5}_{0}_{1}_{2}_{3}-{4}.xml".format(p['newspaper'], p['year'], p['month'], p['day'], p['page'], prefix))
    
  def update_cursor(self, **kw):
    if 'clear' in kw and kw['clear']:
      self.clear_date()
    self._data = self._fingerprint(**kw)
    
  def clear_date(self):
    self._data = {'newspaper': self.newspaper, 'year':'', 'month':'', 'day':'', 'page':''}
    
    self.years = set()
    self.months = defaultdict(set)
    self.days = defaultdict(set)
    self.pages = defaultdict(set)
  
  def _newspaper_path(self):
    return os.path.join(self._archive, self.newspaper)

  def _year_path(self, **kw):
    p = self._fingerprint(**kw)
    return os.path.join(self._archive, p['newspaper'], p['year'])
  
  def _load_available_years(self):
    self.years = set([year for year in os.listdir(self._newspaper_path()) if len(year) == 4])
  
  def _refresh_yearlist(self):
    self.years = set()
    self.months = defaultdict(set)
    self.days = defaultdict(set)
    self.pages = defaultdict(set)
    
    for fn in os.listdir(self._year_path()):
      newspaper, year, month, day, page, supplement = self.decode_filename(fn)
      self.years.add(year)
      self.months[year].add(month)
      self.days[year+month].add(day)
      if supplement != "":
        self.pages[year+month+day].add(supplement + "-" + page)
      else:
        self.pages[year+month+day].add(page)
  
  def get_months(self, year = None):
    if year:
      self.update_cursor(year = year)
    if year not in self.months:
      self._refresh_yearlist()
    return self.months[year]
    
  def get_days(self, **kw):
    if kw:
      self.update_cursor(**kw)
    if kw.get("year", "") not in self.months:
      self._refresh_yearlist()
    year = self._data['year']
    month = self._data['month']
    return self.days[year+month]
    
  def get_pages(self, **kw):
    if kw:
      self.update_cursor(**kw)
    if kw.get("year", "") not in self.months:
      self._refresh_yearlist()
    year = self._data['year']
    month = self._data['month']
    day = self._data['day']
    return self.pages[year+month+day]
  
  def get_page_doc(self, **kw):
    fp = self.encode_filename(**kw)
    assert(os.path.isfile(fp))
    self.update_cursor(**kw)
    text = []
    with open(fp, "r") as fl:
      r = fl.read()
      doc = ET.fromstring(r)
    return doc
    
  def get_page_text(self, **kw):
    doc = self.get_page_doc(**kw)
    text = []
    for word in doc.findall("BL_page/pageText/pageWord"):
      text.append(word.text)
    return u" ".join([x for x in text if x])
  
  def get_article_text(self, **kw):
    doc = self.get_page_doc(**kw)
    text = []
    for word in doc.findall("BL_article/image_metadata/articleImage/articleText/articleWord"):
      text.append(word.text)
    return u" ".join([x for x in text if x])
  
  def get_article_metadata(self, **kw):
    doc = self.get_page_doc(**kw)
    md = {}
    for x in ["BL_article/title_metadata","BL_article/issue_metadata",
              "BL_article/article_metadata/dc_metadata"]:
      for el in doc.findall(x):
        md[el.tag] = el.text
    return md
  
if __name__ == "__main__":
  a = BLNewspaper()
  a.get_months(year = "1870")
  a.get_days(year = "1870", month = "06")
  a.get_pages(year = "1870", month = "06", day = "01")
  assert(os.path.isfile(a.encode_filename(year="1870", month="05", day="04", page="0004")))
  assert(os.path.isfile(a.encode_filename(year="1870", month="05", day="04", page="S-0001")))
  c = BLNewspaper("BNER")
  assert(os.path.isfile(c.encode_filename(year="1858", month="01", day="06", page="V-0001")))
  b = BLNewspaper("BRPT")
  doc = b.get_page_text(year="1839", month="01", day="01", page="0003")
  b.cursor()
  print("'doc' holds the text")