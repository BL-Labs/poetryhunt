from redis import Redis
import csv
from os.path import join as osjoin

from jisc1_locations import SHARES

_r = Redis()

def lookup(newspaper, year, month, day, page = None, master = None, *others, **kwargs):
  if not page:
    if master != None and master != "":
      serv = _r.get("{0}{1}{2}{3}".format(newspaper.upper(), year, month, day))
      return osjoin(serv, "../master")
    else:
      return _r.get("{0}{1}{2}{3}".format(newspaper.upper(), year, month, day))

  service = _r.get("{0}{1}{2}{3}".format(newspaper.upper(), year, month, day))
  if service:
    fname = "WO1_{0}_{1}_{2}_{3}-{4}.tif".format(newspaper.upper(), year, month, day, page)
    if master != None and master != "":
      return osjoin(service, fname)
    else:
      return osjoin(service, "../master", fname)

if __name__ == "__main__":
  p = _r.pipeline()
  cmdcount = 0

  for share in SHARES:
    print("Building reverse lookup for {0}".format(share))
    with open("{0}.csv".format(share), "r") as ffp:
      d = csv.reader(ffp)
      for path, paper, year, month, day in d:
        py = "{0}{1}".format(paper.upper(), year)
        pkey = "{0}{1}{2}{3}".format(paper.upper(), year, month, day)
        p.sadd(share, py)
        p.set(pkey, path)
        cmdcount += 2
      
        if cmdcount > 500:
          p.execute()
          cmdcount = 0
    p.execute()
    cmdcount = 0