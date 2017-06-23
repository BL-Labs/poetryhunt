from newspaperaccess import NewspaperArchive

from sklearn.feature_extraction import DictVectorizer
from sklearn.cluster import KMeans

import os
import sqlite3

CL_CACHE_FOLDER = "/datastore/cluster_cache_dbs"

class ClusterDB(object):
  def __init__(self, dbfile = "area_cache.db"):
    self._conn = sqlite3.connect(os.path.join(CL_CACHE_FOLDER, dbfile))
    
    # Dict responses:
    self._conn.row_factory = sqlite3.Row
    
    self._cur = self._conn.cursor()
    self._vector_keys = ["id", "x1ave_ledge", "redge_x2ave", "ltcount", "x1_var1", "x1_var2", "x2_var1", "x2_var2", "density"]
    self._item_keys = ["id", "newspaper", "year", "month", "day", "page", "article", "block_number", "vector_id"]
    self._cluster_result = ["id", "label", "item_id"]
    
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
      DROP TABLE IF EXISTS vector;
      CREATE TABLE vector(id INTEGER PRIMARY KEY,
                          x1ave_ledge INTEGER, 
                          redge_x2ave INTEGER,
                          ltcount INTEGER,
                          x1_var1 FLOAT, 
                          x1_var2 FLOAT, 
                          x2_var1 FLOAT, 
                          x2_var2 FLOAT, 
                          density FLOAT);
      DROP TABLE IF EXISTS item;
      CREATE TABLE item(id INTEGER PRIMARY KEY,
                        newspaper TEXT,
                        year TEXT,
                        month TEXT,
                        day TEXT,
                        page TEXT,
                        article TEXT,
                        block_number TEXT,
                        vector_id INTEGER,
                        FOREIGN KEY(vector_id) REFERENCES vector(id));
      DROP TABLE IF EXISTS cluster;
      CREATE TABLE cluster(id INTEGER PRIMARY KEY,
                           label INTEGER,
                           item_id INTEGER,
                           FOREIGN KEY(item_id) REFERENCES item(id));
      """)
  def vectors(self):
    for md in self._cur.execute("SELECT * from vector ORDER BY id;").fetchall():
      yield dict(md)
    
  def vector(self, vid):
    if vid != None:
      r = self._cur.execute("SELECT * FROM vector WHERE id = ? LIMIT 1;", (vid,))
      return r.fetchone()
  def vecidtoitem(self, id = None, **md):
    if id != None:
      r = self._cur.execute("SELECT * FROM item WHERE vector_id = ? LIMIT 1;", (id,))
      return r.fetchone()

  def add_vector(self, **params):
    
    vlist = ", ".join(self._vector_keys[1:])
    vallist = ", ".join([":{0}".format(x) for x in self._vector_keys[1:]])
    sql = """INSERT INTO vector({0}) VALUES({1});""".format(vlist, vallist)
    self._cur.execute(sql, params)
    id = self._cur.lastrowid
    return id
  
  def add_item(self, **params):
    
    vlist = ", ".join(self._item_keys[1:])
    vallist = ", ".join([":{0}".format(x) for x in self._item_keys[1:]])
    self._cur.execute("""INSERT INTO item({0}) VALUES({1});""".format(vlist, vallist), params)
    id = self._cur.lastrowid
    return id  
  
  def add_cluster(self, label, item_id):
    
    self._cur.execute("""INSERT INTO cluster(label, item_id) VALUES(?, ?);""", (label, item_id))
    id = self._cur.lastrowid
    return id

def blockarea(a):
  if a['box'] == []:
    return 0
  else:
    return (a['box'][2] - a['box'][0]) * (a['box'][3] - a['box'][1])
    
def get_vectrow(a):
  vect = {}
  # redo box calculations, due to ocr discrepancies. Only if enough lines though
  if len(a['lines']) > 5:
    xs, ys = map(lambda x: sorted(list(x))[2:-2], zip(*a['lines']))
    a['box'] = [min(xs), min(ys), max(xs), max(ys)]  # x1, y1, x2, y2
    
    vect['x1ave_ledge'] = a['col_mean_and_var']['x1'][0] - min(xs)
    vect['redge_x2ave'] = max(xs) - a['col_mean_and_var']['x2'][0]
  else:
    vect['x1ave_ledge'] = a['col_mean_and_var']['x1'][0] - a['box'][0]
    vect['redge_x2ave'] = a['box'][2] - a['col_mean_and_var']['x2'][0]
  vect['ltcount'] = a['ltcount']
  vect['x1_var1'] = a['col_mean_and_var']['x1'][1]
  vect['x1_var2'] = a['col_mean_and_var']['x1'][2]
  vect['x2_var1'] = a['col_mean_and_var']['x2'][1]
  vect['x2_var2'] = a['col_mean_and_var']['x2'][2]
  if blockarea(a) > 0:
    # number of letters found by the OCR / pixel area of the block.
    vect['density'] = a['ltcount']/blockarea(a)
  else:
    vect['density'] = 0
  
  return vect

def create_cluster_dataset(n, daterange = [1744, 1756], dbfile = "1744_1756_cluster.db", refresh = False):
  # create a sklearn vector db from the area data
  # cache a flat db copy as a speed up for later iterations
  
  doc = []
  id_list = []
  if not os.path.isfile(os.path.join(CL_CACHE_FOLDER, dbfile)) or refresh == True:
    print("No cache file found. Creating.")
    
    db = ClusterDB(dbfile)
    with db:
      # recreate tables:
      db.create_tables(True)
      
      # run through all entries
      # pull the text areas data for each, create vector and label files:
      # vector: x1ave-l_edge, redge-x2ave, ltcount, x1_var1, x1_var2, x2_var1, x2_var2, wordareas/boxarea
      # label: newspaper, year, month, day, page, article, block_number
      # row x of vector csv is linked to row x of label csv
      for newspaper in n.NEWSPAPERS:
        for md in n.all_available_newspaper_dates(newspaper, daterange):
          areadoc = n.get_areas(**md)
          print("{newspaper} - {year}/{month}/{day}".format(**md))
          for page in sorted(areadoc.keys()):
            for art in sorted(areadoc[page].keys()):
              for block_id, block in enumerate(areadoc[page][art]):
                if blockarea(block) > 500:
                  vectrow = get_vectrow(block)
                  vect_id = db.add_vector(**vectrow)
                  item_id = db.add_item(page = page, article = art, block_number = block_id, vector_id = vect_id, **md)
                
  db = ClusterDB(dbfile)  
  print("Loading from db cache '{0}'".format(dbfile))
  idx = 0
  for vect in db.vectors():
    if vect['x1_var1'] and vect['x2_var1']:
      id_list.append(vect['id'])
      del vect['id']
      doc.append(vect)
      idx += 1
  print("{0} vectors loaded.".format(idx+1))
  transformer = DictVectorizer()
  ds = transformer.fit_transform(doc)
  return ds, transformer, id_list

if __name__ == "__main__":
  n = NewspaperArchive()
  dataset, transform, id_list = create_cluster_dataset(n)
  