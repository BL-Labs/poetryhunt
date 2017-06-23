from burney_data import BurneyDB

import csv

BURNEY = "burney.db"
EXPORT = "issues_{0}_{1}.csv"

db = BurneyDB(BURNEY)

FIELDS = ["title", "issueNumber", "year", "month", "day", "printedDate", "typeOfPublication", "pageCount", "number_of_articles"]

with db:  
  for x in range(0,10):
    start_year = 1700 + 10 * x
    end_year = start_year + 10
    print("Doing {0} to {1}".format(str(start_year), str(end_year)))
    with open(EXPORT.format(str(start_year), str(end_year)), "w") as cdoc:
      csvd = csv.DictWriter(cdoc, fieldnames = FIELDS)
      csvd.writerow(dict([(x,x) for x in FIELDS]))
      for item in db.list_all_entries():
        y = int(item['year'])
        if y<end_year and y>=start_year:
          t_md = db.get_title_row(id=item['title_id'])
          i_md = db.get_issue_row(id=item['issue_id'])
          record = {}
          record.update(item)
          record.update(t_md)
          record.update(i_md)
          row = dict([(x, record[x]) for x in FIELDS])
          csvd.writerow(row)
