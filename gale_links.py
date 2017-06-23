import os
import sqlite3

GALE_FILE = "/datastore/gale_links/link.db"

class GaleLinks(object):
  def __init__(self, dbfile = GALE_FILE):
    self._conn = sqlite3.connect(dbfile)
    
    # Dict responses:
    self._conn.row_factory = sqlite3.Row
    
    self._cur = self._conn.cursor()
    self._lookup_keys = ["int_id", "id", "link", "asset_id", "issue", "newspaper_id", "year", "month", "day", "page", "article"]
    
  def commit(self):
    return self._conn.commit()

  def close(self):
    return self._conn.close()
  
  def __enter__(self):
    return self
  
  def __exit__(self, type, value, traceback):
    self._conn.commit()
    self._conn.close()

  def create_tables(self, sure_about_this = False):
    if sure_about_this:
      print("Creating tables")
      self._cur.executescript("""
      DROP TABLE IF EXISTS lookup;
      CREATE TABLE lookup(int_id INTEGER PRIMARY KEY,
                          id TEXT,
                          link TEXT,
                          title TEXT,
                          asset_id TEXT,
                          issue TEXT,
                          newspaper_id TEXT,
                          year TEXT,
                          month TEXT,
                          day TEXT,
                          page TEXT,
                          article TEXT);
      """)
  
  def add_row(self, id, asset_id, link, issue, title):
    try:
      rd = {'asset_id': asset_id, "link": link, "issue": issue, "title": title, "id": id}
      _, rd['newspaper_id'], rd['year'], rd['month'], daypagearticle = id.split("_")
      rd['day'], rd['page'], rd['article'] = daypagearticle.split("-")
    except Exception as e:
      print(rd)
      raise e
    
    vlist = ", ".join(self._lookup_keys[1:])
    vallist = ", ".join([":{0}".format(x) for x in self._lookup_keys[1:]])
    sql = """INSERT INTO lookup({0}) VALUES({1});""".format(vlist, vallist)
    self._cur.execute(sql, rd)
    id = self._cur.lastrowid
    return id
  
  def get_link(self, newspaper_id, year, month, day, page, article):
    r = self._cur.execute("""SELECT link, asset_id FROM lookup WHERE newspaper_id="{0}" AND year="{1}" AND month="{2}" AND day="{3}" AND page="{4}" AND article="{5}"  LIMIT 1;""".format(newspaper_id, year, month, day, page, article))
    resp = self._cur.fetchone()
    if resp != None:
      return dict(resp)

  def build_db(self, gale_links = "/datastore/bl_links.txt"):
    import csv
    with open(gale_links, "r") as glf:
      doc = csv.DictReader(glf)
      self.create_tables(sure_about_this = True)
      for row in doc:
        if row['id'] != None and row['id'] != "" and row['assetID'] != None and row['Link'] != "":
          new_id = self.add_row(id = row['id'], asset_id = row['assetID'], link = row['Link'], issue = row['is'], title = row['ti'])
          if not (new_id % 1000):
            print("Processed {0} rows".format(new_id))
    print("Build complete")
    self.commit()
    print("Building Indexes:")
    self._cur.execute("CREATE INDEX Lookup_newspaper_id on lookup(newspaper_id)")
    self._cur.execute("CREATE INDEX Lookup_year on lookup(year)")
    self._cur.execute("CREATE INDEX Lookup_month on lookup(month)")
    self._cur.execute("CREATE INDEX Lookup_year_month_day on lookup(year,month,day)")
    self._cur.execute("CREATE INDEX Lookup_year_month_day_pa on lookup(year,month,day,page,article)")
    self.commit()
    print("Complete")

if __name__ == "__main__":
  import sys, csv
  if len(sys.argv) > 1:
    fns = [x for x in sys.argv[1:] if x.endswith("csv")]
    g = GaleLinks()
    for fn in fns:
      hits = 0
      misses = 0
      with open(fn, "r") as fnh:
        print("Hits: {0}   Misses: {1}".format(hits, misses))
        print("Processing {0}".format(fn))
        with open(fn[:-4] + "_glinks.csv", "w") as outh:
          doc = csv.DictReader(fnh)
          fieldnames = None
          outdoc = None
          for idx,docrow in enumerate(doc):
            row = docrow.copy()
            if not fieldnames:
              fieldnames = ["gale_link"] + list(row.keys())
              outdoc = csv.DictWriter(outh, fieldnames = fieldnames)
              outdoc.writerow({x:x for x in fieldnames})
            gl = g.get_link(row['titleAbbreviation'], row['year'], row['month'], row['day'], row['page'], row['article'])
            if not gl:
              misses += 1
              row['gale_link'] = "No match"
            else:
              hits += 1
              row['gale_link'] = gl['link']
            outdoc.writerow(row)
            if not (idx+1) % 100:
              print("Hits: {0}   Misses: {1}".format(hits, misses))