import sqlite3

class BurneyDB(object):
  class MissingLinkedIDs(Exception):
    pass
    
  def __init__(self, dbfile = "burney.db", json_archive = "/datastore/burneyjson", areas_archive = "/datastore/burneyareas"):
    self._conn = sqlite3.connect(dbfile)
    
    # Dict responses:
    self._conn.row_factory = sqlite3.Row
    
    self._cur = self._conn.cursor()
    self._title_keys = ["id", "title", "titleAbbreviation", "titleContinues", "titleContinuedBy", "placeOfPublication", "datesOfPublication", "typeOfPublication", "earliest_issue", "last_issue"]
    self._issue_keys = ["id", "volumeNumber", "issueNumber", "printedDate", "normalisedDate", "pageCount", "ESTC", "title_id"]
    self._pages_keys = ["id", "number_of_articles", "day", "month", "year", "filepath", "title_id", "issue_id"]
    self._corrupt_keys = ["id", "filepath", "day", "month", "year", "newspaper", "xmlfile"]
    
    self.create_scanned_cache()
    
  def create_scanned_cache(self):
    self._cached_scanned = [x[0] for x in self._cur.execute("""SELECT filepath FROM pages;""").fetchall()]
    self._cached_scanned += [x[0] for x in self._cur.execute("""SELECT filepath FROM corrupt;""").fetchall()]
  
  def create_tables(self, sure_about_this = False):
    if sure_about_this:
      self._cur.executescript("""
      DROP TABLE IF EXISTS title_metadata;
      CREATE TABLE title_metadata(id INTEGER PRIMARY KEY,
                                title TEXT,
                                titleAbbreviation TEXT,
                                titleContinues TEXT,
                                titleContinuedBy TEXT,
                                placeOfPublication TEXT,
                                datesOfPublication TEXT,
                                typeOfPublication TEXT,
                                earliest_issue TEXT,
                                last_issue TEXT);
      
      DROP TABLE IF EXISTS issue_metadata;
      CREATE TABLE issue_metadata(id INTEGER PRIMARY KEY, 
                                  volumeNumber TEXT,
                                  issueNumber TEXT,
                                  printedDate TEXT,
                                  normalisedDate TEXT,
                                  pageCount TEXT,
                                  ESTC TEXT,
                                  title_id INTEGER,
                                  FOREIGN KEY(title_id) REFERENCES title_metadata(id)
                                  );
                                  
      DROP TABLE IF EXISTS pages;
      CREATE TABLE pages(id INTEGER PRIMARY KEY,
                         number_of_articles INTEGER,
                         day TEXT,
                         month TEXT,
                         year TEXT,
                         filepath TEXT,
                         title_id INTEGER,
                         issue_id INTEGER,
                         FOREIGN KEY(title_id) REFERENCES title_metadata(id),
                         FOREIGN KEY(issue_id) REFERENCES issue_metadata(id)
                         );

      DROP TABLE IF EXISTS corrupt;
      CREATE TABLE corrupt(xmlfile TEXT UNIQUE,
                           id INTEGER PRIMARY KEY,
                           filepath TEXT,
                           day TEXT,
                           month TEXT,
                           year TEXT,
                           newspaper TEXT);
      """)
      self._conn.commit()
  
  def commit(self):
    return self._conn.commit()

  def close(self):
    return self._conn.close()
  
  def __enter__(self):
    return self
  
  def __exit__(self, type, value, traceback):
    self._conn.commit()
    self._conn.close()

  def get_title_row(self, **kwds):
    where_filters = ['{0} = "{1}"'.format(k,v) for k,v in kwds.items() if k in self._title_keys]
    self._cur.execute("""SELECT {0} FROM title_metadata WHERE {1}
                 LIMIT 1;""".format(",".join(self._title_keys), " AND ".join(where_filters)))
    resp = self._cur.fetchone()
    if resp != None:
      return dict(resp)

  def add_title_row(self, md):
    # does it exist already? match titleAbbreviation, the title and the date range.
    # create new if no match is found.
    for item in self._title_keys[1:]:  # everything but the id column
      if item not in md:
        md[item] = ""

    self._cur.execute("""SELECT id FROM title_metadata WHERE
                   titleAbbreviation="{titleAbbreviation}" AND
                   title="{title}" AND
                   datesOfPublication="{datesOfPublication}"
                   LIMIT 1;""".format(**md))
    
    resp = self._cur.fetchone()
    if resp == None:
      # create new record
      
      self._cur.execute("""INSERT INTO title_metadata(title, titleAbbreviation, titleContinues, titleContinuedBy, placeOfPublication, datesOfPublication, typeOfPublication) VALUES(:title, :titleAbbreviation, :titleContinues, :titleContinuedBy, :placeOfPublication, :datesOfPublication, :typeOfPublication);""", md)
      id = self._cur.lastrowid
    else:
      id = resp[0]
    
    return id

  def get_issue_row(self, **kwds):
    where_filters = ['{0} = "{1}"'.format(k,v) for k,v in kwds.items() if k in self._issue_keys]
    self._cur.execute("""SELECT {0} FROM issue_metadata WHERE {1}
                 LIMIT 1;""".format(",".join(self._issue_keys), " AND ".join(where_filters)))
    resp = self._cur.fetchone()
    if resp != None:
      return dict(resp)

  def get_entry_row(self, **kwds):
    where_filters = ['{0} = "{1}"'.format(k,v) for k,v in kwds.items() if k in self._pages_keys]
    self._cur.execute("""SELECT {0} FROM pages WHERE {1}
                 LIMIT 1;""".format(",".join(self._pages_keys), " AND ".join(where_filters)))
    resp = self._cur.fetchone()
    if resp != None:
      return dict(resp)

  def add_issue_row(self, md):
    # does it exist already? match titleAbbreviation, the title and the date range.
    # create new if no match is found.
    for item in self._issue_keys[1:]:  # everything but the id column
      if item not in md:
        md[item] = ""
    
    if not md['title_id']:
      raise MissingLinkedIDs
    
    self._cur.execute("""SELECT id FROM issue_metadata WHERE
                   ESTC="{ESTC}" AND
                   issueNumber="{issueNumber}" AND
                   normalisedDate="{normalisedDate}" AND
                   title_id={title_id}
                   LIMIT 1;""".format(**md))
    
    resp = self._cur.fetchone()
    if resp == None:
      # create new record
      self._cur.execute("""INSERT INTO issue_metadata(volumeNumber, issueNumber, printedDate,normalisedDate,pageCount,ESTC,title_id) VALUES(:volumeNumber, :issueNumber, :printedDate,:normalisedDate,:pageCount,:ESTC,:title_id);""", md)
      id = self._cur.lastrowid
    else:
      id = resp[0]
      
    return id

  def add_service_dir(self, md):
    for item in self._pages_keys[1:]:
      if item not in md:
        md[item] = ""
  
    if not md['title_id'] or not md['issue_id']:
      raise MissingLinkedIDs
    
    self._cur.execute("""INSERT INTO pages(number_of_articles, day, month, year, filepath, title_id, issue_id) VALUES (:number_of_articles, :day, :month, :year, :filepath, :title_id, :issue_id)""", md)
    
    id = self._cur.lastrowid
    
    return id
  
  def list_all_newspapers(self):
    self._cur.execute("""SELECT * from title_metadata;""")
    for md in self._cur.fetchall():
      yield dict(md)

  def list_all_issues(self):
    self._cur.execute("""SELECT * from issue_metadata;""")
    for md in self._cur.fetchall():
      yield dict(md)
    
  def list_all_entries(self, titleAbbreviation = None, title_id = None, issue_id = None, **kwds):
    if titleAbbreviation != None:
      t_md = self.get_title_row(titleAbbreviation = titleAbbreviation)
      if t_md != None:
        title_id = t_md['id']
    
    where_filters = []
    
    if title_id != None:
      where_filters.append('title_id = "{0}"'.format(title_id))
    if issue_id != None:
      where_filters.append('issue_id = "{0}"'.format(issue_id))
    
    for key in kwds:
        if key in self._pages_keys:
            where_filters.append('{0} = "{1}"'.format(key, kwds[key]))
    
    if where_filters != []:
      self._cur.execute("""SELECT {0} from pages WHERE {1};""".format(",".join(self._pages_keys), " AND ".join(where_filters)))
    else:
      self._cur.execute("""SELECT {0} from pages;""".format(",".join(self._pages_keys)))
    
    for md in self._cur.fetchall():
      yield dict(md)

  def scanned(self, filepath, skipping=False):
    if skipping:
      # only hit the cache:
      return filepath in self._cached_scanned
    self._cur.execute("""SELECT id FROM pages WHERE filepath="{0}";""".format(filepath))
    if self._cur.fetchone():
      return True
    # not there. Is it corrupt then?
    self._cur.execute("""SELECT id FROM corrupt WHERE filepath="{0}";""".format(filepath))
    if self._cur.fetchone():
      return True
    return False
  
  def mark_corrupt(self, md):
    for item in self._corrupt_keys[1:]:
      if item not in md:
        md[item] = ""
        
    self._cur.execute("""INSERT OR IGNORE INTO corrupt(filepath, day, month, year, newspaper, xmlfile)
                         VALUES (:filepath, :day, :month, :year, :newspaper, :xmlfile);""", md)
    id = self._cur.lastrowid
    
    return id
  
  def list_corrupt_files(self, title_id = None):
    if title_id == None:
      self._cur.execute("""SELECT * from corrupt;""")
    else:
      t_md = self.get_title_row(id = title_id)
      self._cur.execute("""SELECT * from corrupt WHERE newspaper = "{0}";""".format(t_md['titleAbbreviation']))
    return self._cur.fetchall()

  def update_title_row(self, **kwds):
    if 'id' not in kwds and 'titleAbbreviation' not in kwds:
      print("Cannot update title information without some key identifier.")
      return
    else:
      data_line = ",".join(['{0}="{{{0}}}"'.format(x) for x in kwds.keys() if x not in ['id', 'titleAbbreviation'] and x in self._title_keys])
      wheres = []
      if 'id' in kwds:
        wheres.append("id={id}")
      if 'titleAbbreviation' in kwds:
        wheres.append("titleAbbreviation=:titleAbbreviation")
      where_line = " AND ".join(wheres)
      q = "UPDATE title_metadata SET " + data_line + " WHERE " + where_line + ";"
      self._cur.execute(q.format(**kwds))
      
  def update_issue_row(self, **kwds):
    if 'id' not in kwds:
      print("Cannot update issue information without some key identifier.")
      return
    else:
      data_line = ",".join(['{0}="{{{0}}}"'.format(x) for x in kwds.keys() if x != "id" and x in self._issue_keys])
      q = "UPDATE issue_metadata SET " + data_line + " WHERE id={id};"
      self._cur.execute(q.format(**kwds))

  def _update_newspaper(self, id):
    from datetime import datetime
    dates = []
    printed_dates = {}
    for entry in self.list_all_entries(title_id = id):
      try:
        if entry['month'] == "00" or entry['month'] == "0":
          dates.append(datetime(int(entry['year']),1,1))
        elif entry['day'] == "00" or entry['day'] == "0":
          dates.append(datetime(int(entry['year']), int(entry['month']),1))
        else:
          dates.append(datetime(int(entry['year']), int(entry['month']), int(entry['day'])))
        printed_dates[dates[-1]] = "{year}-{month}-{day}".format(**dict(entry))
      except ValueError as e:
        print("Couldn't form date from:")
        print(dict(entry))
    
    dates.sort()
    
    self.update_title_row(id = id, earliest_issue = printed_dates[dates[0]],
                          last_issue = printed_dates[dates[-1]])
    return printed_dates[dates[0]], printed_dates[dates[-1]]
      
  def regenerate_earliest_latest_records(self):
    # Update the convenience columns in 'title_metadata' to reflect the earliest and latest
    # issue we have scanned for a given newspaper run
    for md in list(self.list_all_newspapers()):
      e,l = self._update_newspaper(md['id'])
      print("Updating {0} - id={1} with {2} -> {3}".format(md['title'], md['id'], e, l))
      
  def export_newspaper_data(self, filename):
    import csv
    with open(filename, "w") as co:
      doc = csv.DictWriter(co, fieldnames = self._title_keys)
      doc.writerow(dict([(x,x) for x in self._title_keys]))
      for md in self.list_all_newspapers():
        doc.writerow(dict(md))
    
if __name__ == "__main__":
  # load the backup db as 'db'
  print("Loading 'burney.db.devuse' as db. (Won't have full corrupt file logs but has up to date metadata/filepaths.)")
  db = BurneyDB("burney.db.devuse")