# -*- coding: utf-8 -*-
import json, os

from burney_data import BurneyDB

ARCHIVE = "/datastore/burneyjson"
AREASARCHIVE = "/datastore/burneyareas"

def papertopath(newspaper, year = None, month = None, day = None, archive = ARCHIVE):
    if year == None:
        return os.path.join(archive, newspaper)
    elif day == None or month == None:
        return os.path.join(archive, newspaper, year)
    else:
        if len(month) != 2:
            month = "{0:02d}".format(int(month))
        if len(day) != 2:
            try:
                day = "{0:02d}".format(int(day))
            except ValueError as e:
                pass
        return os.path.join(archive, newspaper, year, month + "_" + day + ".json")

    
class NewspaperAccessError(Exception):
    pass

class NoSuchDocumentFound(NewspaperAccessError):
    pass

class NoSuchPage(NewspaperAccessError):
    pass

class NoSuchNewspaper(NewspaperAccessError):
    def __init__(self, newspaper):
        # print("Couldn't find '{0}' in the Newspaper mapping".format(newspaper))
        ...

NEWSPAPERMAPPING = {}

NEWSPAPERS = list(set(NEWSPAPERMAPPING.values()))

class TextAreas(object):
    def __init__(self, archive = AREASARCHIVE, cachelimit = 5):
        self.archive = archive
        self.CACHELIMIT = cachelimit
        self._cache = {}
        self._cachelist = []

    def papertopath(self, newspaper, year = None):
        if year == None:
            return os.path.join(self.archive, newspaper)
        else:
            return os.path.join(self.archive, newspaper, year + ".json")
        
    def _cachename(self, newspaper, year):
        return newspaper + year
    
    def _fpathtodate(self, fpath):
        _, newspaper, year, month, day, service = fpath.rsplit("/", 5)
        if service == "service":
            return newspaper, year, month, day
        else:
            print("What is this?")
            print(fpath)
            raise Exception
    
    def _addtocache(self, jsondoc, newspaper, year):
        if len(self._cachelist) > self.CACHELIMIT:
            # remove the oldest jsondoc from memory
            oldest = self._cachelist.pop(0)
            del self._cache[oldest]
            
        cname = self._cachename(newspaper, year)
        self._cache[cname] = jsondoc
        self._cachelist.append(cname)
    
    def exists(self, newspaper, year, month, day, page = None, **otherkwparams):
            
        ppath = self.papertopath(newspaper, year)
        if os.path.isfile(ppath):
            return True
        else:
            try:
                doc = self.get(newspaper, year, month, day)
                return False
            except (NoSuchPage, NoSuchDocumentFound, NoSuchNewspaper) as e:
                return False
    
    def years_available(self, newspaper):
        if newspaper not in NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        return os.listdir(os.path.join(self.archive, newspaper))
    
    def get(self, newspaper, year, month, day, page=None, *params, **otherkwparams):
        doc = {}
        
        if len(month) != 2 or isinstance(month, int):
            month = "{0:02d}".format(int(month))
        if len(day) != 2 or isinstance(day, int):
            day = "{0:02d}".format(int(day))
            
        ppath = self.papertopath(newspaper, year)
        cname = self._cachename(newspaper, year)
        docid = year+month+day
        
        if cname in self._cachelist:
            doc = self._cache[cname]
        else:
            if os.path.exists(ppath):
                print("Loading {0} from disc".format(ppath))
                with open(ppath, "r") as jd:
                    basedoc = json.load(jd)
                    for fpathnewsp in basedoc:
                        tnewspaper, tyear, tmonth, tday = self._fpathtodate(fpathnewsp)
                        tdocid = tyear + tmonth + tday
                        if tdocid not in doc:
                            doc[tdocid] = {}
                            
                        for item in basedoc[fpathnewsp]:
                            try:
                                docpage, article = item.split("_")
                                if docpage not in doc[tdocid]:
                                    doc[tdocid][docpage] = {}
                                    
                                doc[tdocid][docpage][article] = basedoc[fpathnewsp][item]
                            except ValueError as e:
                                print(newspaper, year, month, day)
                                print(item, basedoc.keys())
                                print(ppath)
                                raise e
                                
                    self._addtocache(doc, newspaper, year)
            else:
                raise NoSuchDocumentFound()
                
        if page != None and page != "":
            if len(page) != 4 or isinstance(page, int):
                page = "{0:04d}".format(int(page))
            if page in doc[docid]:
                return doc[page]
            else:
                raise NoSuchPage()
        try: 
            return doc[docid]
        except KeyError as e:
            print(docid)
            print(doc.keys())
            print(doc[list(doc.keys())[0]])

class NewspaperArchive(object):
    def __init__(self, archive = ARCHIVE, cachelimit = 5, db = "burney.db", textareas = AREASARCHIVE):
        self._conn = BurneyDB(db)
        self.TA = TextAreas(textareas)
        
        self.NEWSPAPERS = []
        self.NEWSPAPERMAPPING = {}
        self._cache_newspaper_titles()
        
        self.archive = archive
        self.CACHELIMIT = cachelimit
        self._cache = {}
        self._cachelist = []
        
    
    def _cache_newspaper_titles(self):
        for md in self._conn.list_all_newspapers():
            shorttitle = md['title'].replace(" ", "").replace("&", "").replace("'", "").replace("-", "").lower()
            self.NEWSPAPERMAPPING[shorttitle] = md['titleAbbreviation']
            if shorttitle.startswith("the"):
                self.NEWSPAPERMAPPING[shorttitle[3:]] = md['titleAbbreviation']
        self.NEWSPAPERS = list(set(self.NEWSPAPERMAPPING.values()))
    
    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()
  
    def __enter__(self):
        return self
  
    def __exit__(self, type, value, traceback):
        self._conn.commit()
        self._conn.close()        
        
    def guess_newspaper(self, newspapertitle):
        shortened = newspapertitle.replace(" ", "").replace("&", "").replace("'", "").replace("-", "").lower()
        if shortened in self.NEWSPAPERMAPPING:
            return self.NEWSPAPERMAPPING[shortened]
        elif "the" + shortened in self.NEWSPAPERMAPPING:
            return self.NEWSPAPERMAPPING["the"+shortened]
        elif shortened.startswith("the") and shortened[3:] in self.NEWSPAPERMAPPING:
            return self.NEWSPAPERMAPPING[shortened[3:]]
        raise NoSuchNewspaper(newspapertitle)
    
    def isnewspaper(self, newspaper):
        if newspaper not in self.NEWSPAPERS:
            try:
                newspaper = self.guess_newspaper(newspaper)
            except NoSuchNewspaper as e:
                return False
        return os.path.isdir(papertopath(newspaper))
    
    def _cachename(self, newspaper, year, month, day):
        return newspaper + year + month + day
    
    def _addtocache(self, jsondoc, newspaper, year, month, day):
        if len(self._cachelist) > self.CACHELIMIT:
            # remove the oldest jsondoc from memory
            del self._cache[self._cachelist.pop(0)]
        
        self._cache[self._cachename(newspaper, year, month, day)] = jsondoc
        self._cachelist.append(self._cachename(newspaper, year, month, day))
    
    def exists(self, newspaper, year, month, day, page = None, **otherkwparams):
        if newspaper not in self.NEWSPAPERS:
            try:
                newspaper = self.guess_newspaper(newspaper)
            except NoSuchNewspaper as e:
                return False
            
        ppath = papertopath(newspaper, year, month, day, archive = self.archive)
        if os.path.isfile(ppath):
            return True
        else:
            try:
                doc = self.get(newspaper, year, month, day)
                return False
            except (NoSuchPage, NoSuchDocumentFound, NoSuchNewspaper) as e:
                return False
    
    def years_available(self, newspaper):
        if newspaper not in self.NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        return list(set([x['year'] for x in self._conn.list_all_entries(titleAbbreviation=newspaper)]))
    
    def months_available(self, newspaper, year):
        if newspaper not in self.NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        return list(set([x['month'] for x in self._conn.list_all_entries(titleAbbreviation=newspaper, year = year)]))
    
    def days_available(self, newspaper, year, month):
        if newspaper not in self.NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        return list(set([x['day'] for x in self._conn.list_all_entries(titleAbbreviation=newspaper, year = year, month = month)]))
    
    def get(self, newspaper, year, month, day, page=None, *params, **otherkwparams):
        doc = {}
        if newspaper not in self.NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        cname = self._cachename(newspaper, year, month, day)
        if cname in self._cachelist:
            doc = self._cache[cname]
        else:
            ppath = papertopath(newspaper, year, month, day, archive = self.archive)
            if os.path.exists(ppath):
                with open(ppath, "r") as jd:
                    basedoc = json.load(jd)
                    self._addtocache(doc, newspaper, year, month, day)
                    for item in basedoc:
                        try:
                            docpage, article = item.split("_")
                            if docpage not in doc:
                                doc[docpage] = {}
                            doc[docpage][article] = basedoc[item]
                        except ValueError as e:
                            print(newspaper, year, month, day)
                            print(item, basedoc.keys())
                            print(ppath)
                            raise e
            else:
                raise NoSuchDocumentFound()
        if page != None and page != "":
            if len(page) != 4 or isinstance(page, int):
                page = "{0:04d}".format(int(page))
            if page in doc:
                return doc[page]
            else:
                raise NoSuchPage()
        return doc
    
    def get_areas(self, **kwparams):
        return self.TA.get(**kwparams)
    
    def all_available_newspaper_dates(self, newspaper, daterange = [1798, 1901]):
        if newspaper not in self.NEWSPAPERS:
            newspaper = self.guess_newspaper(newspaper)
        ydx = daterange[1] - daterange[0]
        for year in sorted(self.years_available(newspaper)):
            if 0 <= (int(year) - daterange[0]) < ydx:
                for month in sorted(self.months_available(newspaper, year)):
                    for day in sorted(self.days_available(newspaper, year, month)):
                        yield {'newspaper': newspaper, 
                               'year': year,
                               'month': month,
                               'day': day}
                    
    def all_available_newspapers(self, newspapers = [], daterange = [1798, 1901]):
        if newspapers == []:
            newspapers = self.NEWSPAPERS
            
        for newspaper in sorted(self.NEWSPAPERS):
            if newspaper in newspapers:
                for ref in self.all_available_newspaper_dates(newspaper, daterange):
                    yield ref

if __name__ == "__main__":
                        
    def get_weighted_list():
        n = NewspaperArchive()
        weighted_newspapers = []
        for newspaper in n.NEWSPAPERS:
            try:
                numb = int(len(n.years_available(newspaper)) / 10.0)
                if numb < 1: 
                    numb = 1
                weighted_newspapers.extend([newspaper] * numb)
            except FileNotFoundError as e:
                ...
        return weighted_newspapers

    WEIGHTED_NEWSPAPERS = get_weighted_list()

