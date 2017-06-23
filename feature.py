from newspaperaccess import NEWSPAPERS, NewspaperArchive, NewspaperAccessError, NoSuchDocumentFound
from Levenshtein import distance as Ldistance

from random import randint, choice, shuffle, getstate, setstate

import pickle

import os, json, re, string

import itertools

import codecs

import csv

from training_profiles import profile_list

import nltk
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder, BigramAssocMeasures

WORDLIST = "WORDLIST.json"

n = NewspaperArchive()

# Initially informed from a comparison of abolitionist speech writing and
# non-abolitionist speech wordlists.
PRIMED_WORDLIST = ["slavery",
                   "pro-slavery",
                   "slave",
                   "fugitive",
                   "slaveholder",
                   "slaveholding",
                   "respectable",
                   "detersive",
                   "abolition",
                   "coloured",
                   "negro",
                   "american",
                   "lynching",
                   "lecturer",
                   "talk",
                   "meeting",
                   "gathering", # following are good signals for the other labels
                   "chartist",
                   "seccesion",
                   "union",
                   "confederates",
                   "lincoln",
                   "white",
                   "emancipation",
                   "bondsman",
                  ]
KEY_BIGRAMS = ["pro slavery",
               "fugitive slave",
               "negro slave",
               "negro lecturer",
               "black lecturer",
               "black slave",
               ]

stopword_list = stopwords.words('english') + [x for x in "'/-!.\"~#_=+*abcdefghijklmnopqrstuvwxyz"]

# Month list to convert a name to a number:
MONTHS = {"january": "01", "february": "02", "march": "03", "april": "04", "may": "05", "june": "06", 
          "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"}

class ListHandler(object):
    def __init__(self):
        self.WORDLIST_JSON = {}
        self.BIGRAM_JSON = {}

    def get_wordlist_json(self, wordlist_json_filename = "wordlist_with_errors.json"):
        if wordlist_json_filename not in self.WORDLIST_JSON:
            with open(wordlist_json_filename, "r") as wjfp:
                self.WORDLIST_JSON[wordlist_json_filename] = json.load(wjfp)
        return self.WORDLIST_JSON[wordlist_json_filename]

    def get_bigram_json(self, bigram_filename = "bigram.json"):
        if bigram_filename not in self.BIGRAM_JSON:
            with open(bigram_filename, "r") as wjfp:
                self.BIGRAM_JSON[bigram_filename] = json.load(wjfp)
        return self.BIGRAM_JSON[bigram_filename]

LISTS = ListHandler()
    
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
            row["month"] = MONTHS.get(row['month'].lower().strip(), row['month'])
            try:
                row["day"] = "{0:02d}".format(int(row["day"]))
            except ValueError as e:
                # likely one of the weird _S/_V references:
                if row["day"][-2:] not in ["_S", "_V"]:
                    raise NoSuchDocumentFound
                    
            row["year"] = row["year"].strip()
            # we also don't need the article title so remove this:
            # del row['article title']
            references.append(row)
    return references

def hash_profile(profile):
    txt = ""
    for item in sorted(profile.keys()):
        if profile[item] != None:
            txt += str(profile[item])
            
    return txt

def store_classifier(profile, classifier):
    if not os.path.isdir("classifiers"):
        os.mkdir("classifiers")
    
    with open(os.path.join("classifiers", hash_profile(profile)), "wb") as cpk:
        pickle.dump(classifier, cpk)
        
def get_classifier(profile):
    hn = os.path.join("classifiers", hash_profile(profile))
    if os.path.isfile(hn):
        with open(hn, "rb") as cpk:
            classifier = pickle.load(cpk)
        return classifier
        
def random_day():
    year = str(randint(1799,1900))
    month = "{0:02d}".format(randint(1,12))
    day = "{0:02d}".format(randint(1,12))
    return year, month, day

def get_random_valid_date(newspaper):
    year = choice(n.years_available(newspaper))
    month = choice(n.months_available(newspaper, year))
    day = choice(n.days_available(newspaper, year, month))
    return (year, month, day)

def get_random_ref():
    ref = {'newspaper': choice(NEWSPAPERS)}
    ref['year'], ref['month'], ref['day'] = get_random_valid_date(**ref)
    return ref

def get_random_article():
    ref = get_random_ref()
    doc = n.get(**ref)
    ref['page'] = choice(list(doc.keys()))
    ref['article'] = choice(list(doc[ref['page']].keys()))
    return ref

def create_samplelist(newspaper, samples = 30):
    samplelist = []
    while(samples>0):
        date = get_random_valid_date(newspaper)
        if n.exists(newspaper, *date):
            samplelist.append(date)
            samples -= 1
    return samplelist

def get_samplelist_from_all(samples = 50):
    newslists = []
    
    for newspaper in NEWSPAPERS:
        if n.isnewspaper(newspaper):
            print("Generating list for {0}".format(newspaper))
            for year, month, day in create_samplelist(newspaper, samples):
                newslists.append({'newspaper': newspaper, 'year': year, 'month': month, 'day': day})
        else:
            print("Couldn't find a directory for the newspaper '{0}'".format(newspaper))
    
    return newslists

def get_article_samplelist(samples = 100):
    newslists = []
    
    while(len(newslists) < samples):
        try:
            newslists.append(get_random_article())
        except Exception as e:
            pass
    return newslists

def get_sample_newspaper_common_wordlist(newspapers = NEWSPAPERS):
    if not os.path.isfile(WORDLIST):
        print("Creating the initial Wordlist file. This will take some time")
        # make sure the samplelog folder is there
        if not os.path.isdir("samplelogs"):
            os.mkdir("samplelogs")
    
        wordlists = {}
    
        # create the per-newspaper and then aggregate wordlistings
        for newspaper in newspapers:
            print("Creating sample list for {0}".format(newspaper))
            samplelist = create_samplelist(newspaper)

            # commit that list to a log? Maybe should.
            with open(os.path.join("samplelogs", "samplelist_" + newspaper + ".json"), "w") as fp:
                print("Saving log file for {0}".format(newspaper))
                json.dump(samplelist, fp)
            
            total = nltk.FreqDist()
            
            for date in samplelist:
                try:
                    c = get_wordlist(newspaper, date)
                    total.update(c)
                except NewspaperAccessError as e:
                    print("There was an issue accessing the '{0}' for date '{1}'".format(newspaper, date))
                    print(e)
            wordlist[newspaper] = list(total)[:2000]
        with open(WORDLIST, "w") as wfp:
            json.dump(wordlist, wfp)
            
    with open(WORDLIST, "r") as wfp:
        doc = json.load(wfp)
        
    return doc

def get_common_wordlist(items):
    commons = nltk.FreqDist()
    tally = 1
    for idx, (newspaper, *date) in enumerate(items):
        try:
            wordlist = get_wordlist(newspaper, date)
            commons.update({w:1 for w in list(wordlist)})
        except NewspaperAccessError as e:
            print("There was an issue accessing the '{0}' for date '{1}'".format(newspaper, date))
            print(e)
            tally -= 1
    return commons, idx+tally


def get_wordlist_byref(newspaper, year, month, day, page=None, article=None, verbose=False, *args, **kwargs):
    return get_wordlist(newspaper, [year, month, day], page, article, verbose)

def wordtest(word):
    if word and len(word.strip()) > 2 and word.strip().lower() not in stopword_list:
        return True
    return False

def _b(item):
    if not item:
        return ''
            
    return item.translate({ord(x):"" for x in string.punctuation})

def get_words(newspaper, year, month, day, page = None, article = None, **kwargs):
    try:
        npaper = n.get(newspaper, year, month, day)
        if page != None and page != "" and page in npaper:
            if article and article in npaper[page]:
                # parse just the one article
                return (w.lower() for t in npaper[page][article] for w in _b(t).split(" ") if wordtest(w))
            # parse just the page:
            return (w.strip().lower() for t in npaper[page].values() for x in t for w in _b(x).split(" ") if wordtest(w))
        #parse the whole paper... eurgh
        return (w.lower() for page in npaper.keys() for t in npaper[page].values() for x in t for w in _b(x).split(" ") if wordtest(w))
    except NewspaperAccessError as e:
        # Maybe handle this more gracefully here...
        raise e

def get_wordlist(newspaper, date, page = None, article = None, verbose=False):
    if verbose:
        print("{0} {1} {3}/{2}".format(newspaper, *date))
    return nltk.FreqDist(get_words(newspaper, date[0], date[1], date[2], page, article))


def get_flat_wordlist(wordsets = ["0", "1"], wordlist_json_filename = "wordlist_with_errors.json"):
    # load or get ref to the wordlist
    wlist = LISTS.get_wordlist_json(wordlist_json_filename)
    
    wordset = set()
    
    # create the flat word list
    # 0-distance words:
    if "0" in wordsets and "0" in wlist:
        wordset.update([x for x in wlist["1"].keys()])
    
    if "1" in wordsets and "1" in wlist:
        # 1-distance words:
        wordset.update([y for x in wlist["1"].keys() for y in wlist["1"][x].keys()])
        
    if "2" in wordsets and "2" in wlist:
        # 1-distance words:
        wordset.update([y for x in wlist["2"].keys() for y in wlist["2"][x].keys()])
                
    if "contextual" in wordsets and "contextual" in wlist.keys():
        # add contextual words:
        wordset.update([x for x in wlist["contextual"].keys()])
        
    return wordset

def get_useful_bigrams(doc_wordlist, wordlist_json_filename = "wordlist_with_errors.json", wordsets = ["0", "1"]):
    # load or get ref to the wordlist
    wordset = get_flat_wordlist(wordlist_json_filename = wordlist_json_filename, wordsets = wordsets)
    # FIXME filter wordset against a blacklist? eg "back" may prove problematic
    
    context_words = nltk.FreqDist()
    bigramsf = BigramCollocationFinder.from_words(doc_wordlist, window_size = 3)
    for k,v in bigramsf.ngram_fd.items():
        for x in range(2):
            if k and k[x] in wordset:
                # context_words[k[1-x]] += v
                context_words[" ".join(k)] += v
                break
    return context_words

def get_wordlist_fd_matches(doc_wordlist, wordlist_json_filename = "wordlist_with_errors.json", wordsets = ["0", "1", "2"]):
    # load or get ref to the wordlist
    wordset = get_flat_wordlist(wordsets = wordsets, wordlist_json_filename = wordlist_json_filename)
    
    featureset_wordset = {x:0 for x in wordset}
    
    # FIXME filter wordset against a blacklist? eg "back" may prove problematic
    doc_fd = nltk.FreqDist(doc_wordlist)
    
    for k in doc_fd:
        if k in wordset:
            featureset_wordset[k] = doc_fd[k]
    return featureset_wordset

def get_bigram_fd_matches(doc_wordlist, bigram_filename = "bigram.json"):
    # load or get ref to the wordlist
    bigram_list = set([x for x,y in LISTS.get_bigram_json(bigram_filename = bigram_filename)])
    
    featureset_bset = nltk.FreqDist({x:0 for x in bigram_list})
    
    bigramsf = BigramCollocationFinder.from_words(doc_wordlist, window_size = 3)
    
    bigram_fd = nltk.FreqDist()
    
    for k,v in bigramsf.ngram_fd.items():
        if " ".join(k) in bigram_list:
            featureset_bset[" ".join(k)] += v
            
    return featureset_bset

def proximal_measure(wordlist_json_filename, wordsets, newspaper, year, month, day, page = None, article = None):
    # skip words til the first hit from our wordlist. Then count the words between hits
    try:
        wordlist = get_flat_wordlist(wordsets = wordsets, wordlist_json_filename = wordlist_json_filename)
        doc_wordlist = get_words(newspaper, year, month, day, page, article)
        hit = 0
        hits = []
        for word in doc_wordlist:
            if hit == 0:
                if word in wordlist:
                    hit = 1
            else:
                if word in wordlist:
                    hits.append(hit)
                    hit = 1
                else:
                    hit += 1
        return hits
    except NewspaperAccessError as e:
        return []
    
def get_banded_proximals(proximals, prox_divisions, featureset):
    for pd in prox_divisions:
        featureset['prox_below_{0}'.format(pd)] = 0
    prox_fd = nltk.FreqDist(proximals)
    cur = 0
    ld = len(prox_divisions)
    for sk in sorted(prox_fd.keys()):
        if cur < ld and sk <= prox_divisions[cur]:
            featureset['prox_below_{0}'.format(prox_divisions[cur])] += prox_fd[sk]
        else:
            fl = False
            while(not fl and cur < ld -1):
                cur += 1
                if cur < ld and sk <= prox_divisions[cur]:
                    fl = True
                    featureset['prox_below_{0}'.format(prox_divisions[cur])] += prox_fd[sk]
    return featureset
    
def get_featureset_primed(newspaper, year, month, day, page = None, article = None,  wordlist_json_filename = "wordlist_with_errors.json",
                          wordsets = ["0", "1"], bigram_filename = None, has_f = True, contains_f = True, md_f = True, 
                          prox_f = True, prox_divisions = [1, 2, 3, 5, 10, 20], **kwargs):
    try:        
        doc_wordlist = get_words(newspaper, year, month, day, page, article)
        
        # word hits:
        docfd = get_wordlist_fd_matches(doc_wordlist, wordlist_json_filename = wordlist_json_filename, wordsets = wordsets)
        
        # bigram hits:
        if bigram_filename != None:
            bigramfd = get_bigram_fd_matches(doc_wordlist, bigram_filename = bigram_filename)
        
        featureset = {}
        
        if md_f == True:
            featureset = {'newspaper': newspaper, 'year': year, "page": page}
        
        if prox_f == True:
            proximals = proximal_measure(wordlist_json_filename, wordsets, newspaper, year, month, day, page, article)
            
            featureset = get_banded_proximals(proximals, prox_divisions, featureset)
        
        if has_f:
            for k,v in docfd.items():
                featureset['has({0})'.format(k)] = v > 0
                
            if bigram_filename != None:
                for k,v in bigramfd.items():
                    if v > 0:
                        featureset['bhas({0})'.format(k)] = True
                
        if contains_f:
            for k,v in docfd.items():
                featureset['contains({0})'.format(k)] = v
                
            if bigram_filename != None:
                for k,v in bigramfd.items():
                    featureset['bcontains({0})'.format(k)] = v
        
        return featureset
    except NewspaperAccessError as e:
        return {}

def filtered_refs(refs, only_articles = True):
    
    if only_articles:
        for ref in refs:
            if "article" in ref and ref['article'] != "":
                yield ref
    else:
        for ref in refs:
            yield ref            

def make_sets(reflist, ratio, random_state = None):
    # randomise:
    if random_state != None:
        # should cause the same shuffle reordering to occur.
        setstate(random_state)

    shuffle(reflist)
    # base figures:
    t = sum(ratio)
    lt = len(reflist)
    a,b,c = ratio
    
    return reflist[:int(a*lt/t) - 1], \
           reflist[int(a*lt/t) - 1:int((a + b)*lt/t) - 1], \
           reflist[int((a + b)*lt/t) - 1:-1]

def make_pn_sets(reflists, ratio, only_articles = True, randomset = [], random_state = None):
    reflist = []
    labels = []
    
    for refdoc in reflists:
        
        label = refdoc[:-4]
        
        if label not in labels:
            labels.append(label)
            
        refs = get_references(refdoc)
        
        for ref in filtered_refs(refs, only_articles):
            if n.exists(**ref):
                reflist.append((ref, label))
        
    if len(randomset) > 0:
        print("Adding random set")
        for ref in randomset:
            reflist.append((ref, "control"))
        
    print("{0} - total references. Labels: {1}".format(len(refs), labels))
    print("Ratio - {0} [Training:testing:final test]".format(ratio))
    
    
    return make_sets(reflist, ratio, random_state)    
    
def train_set(w_file, wordsets, b_file, contains_f, has_f, md_f = True, sets = [], **kwargs):
       
    train, test1, test2 = sets
    
    #train = list([(x, "pos") for x in ptrain]) + list([(y, "neg") for y in ntrain])
    #test1 = list([(x, "pos") for x in ptest]) + list([(y, "neg") for y in ntest])
    #test2 = list([(x, "pos") for x in pfinaltest]) + list([(y, "neg") for y in nfinaltest])
    
    def f_set(ref):
        return get_featureset_primed(wordlist_json_filename = w_file, wordsets = wordsets, bigram_filename = b_file,  \
                                          has_f = has_f, contains_f = contains_f, md_f = md_f, **ref)
    
    train_set = [(f_set(ref), label) for ref, label in train]
    test_set1 = [(f_set(ref), label) for ref, label in test1]
    test_set2 = [(f_set(ref), label) for ref, label in test2]
    
    classifier = nltk.NaiveBayesClassifier.train(train_set)
    
    print("Classifer created. \n Accuracy?")
    print("Test1: {0}".format(nltk.classify.accuracy(classifier, test_set1)))
    print("Test2: {0}".format(nltk.classify.accuracy(classifier, test_set2)))
    print("Classifier: Most informative features?")
    print(classifier.show_most_informative_features(15))
    
    return classifier
    
def train_sets(references = ["abomentions.csv", "misc.csv", "nonabospeeches.csv"], ratio = [60,20,20], profile = "articles", include_random = 100):
    # save the PRND seed to let it regenerate the list for each classifier
    shuffle_state = getstate()
    
    random_refs = []
    
    if include_random > 0:
        if profile == "allsets":
            random_refs = get_samplelist_from_all(include_random)
        else:
            random_refs = get_article_samplelist(include_random)
    
    print("Random set included: size {0}".format(len(random_refs)))
    
    classifysets = {}
    classifysets['articles'] = make_pn_sets(references, ratio, only_articles = True, randomset = random_refs, random_state = shuffle_state)
    classifysets['allrefs'] = make_pn_sets(references, ratio, only_articles = False, randomset = random_refs, random_state = shuffle_state)
    
    cls = []
    
    profiles = profile_list(profile)
    
    for profile in profiles:
        print("Wordsets used: {wordsets}, bfile: {b_file}, has:{has_f}, contains:{contains_f}".format(**profile))
        cl = get_classifier(profile)
        if cl == None:
            print("No stored classifier found for this profile - creating")
            cl = train_set(sets = classifysets[profile["refs"]], **profile)
            store_classifier(profile, cl)
        
        cls.append((profile, cl))
    
    return cls
    
def get_context_words_from_bigrams(positive_references, wordlist_json_filename = "wordlist_with_errors.json",
                                   store_as = "bigram.json", threshold = 2000, wordsets = ["0", "1"]):
    context_words = nltk.FreqDist()
    
    for refdoc in positive_references:
        refs = get_references(refdoc)
        for ref in refs:
            # print("Attempting: {newspaper} {year} {month}/{day} {page}pg, article {article}".format(**ref))
            try:
                nc = get_useful_bigrams(get_words(**ref), wordlist_json_filename = wordlist_json_filename, wordsets = wordsets)
                context_words.update(nc)
            except NewspaperAccessError as e:
                print("Failed to load {0}".format(ref))
                
    if store_as:
        with open(store_as, "w") as bifp:
            json.dump(context_words.most_common(threshold), bifp, indent=4)
    return context_words

def get_primed_wordlist_levenshtein(positive_references, store_as = "wordlist_with_errors.json"):
    key_words= {x:{word: nltk.FreqDist() for word in PRIMED_WORDLIST} for x in range(3)}
    for refdoc in positive_references:
        refs = get_references(refdoc)
        for ref in refs:
            try:
                wlist = get_wordlist_byref(**ref)
                # With some thought, this step could be optimised
                # It's tricky though and might be best to fuzz input text for a probabilistic match to prime words
                # brute forcing til I can work it out
                for pword in PRIMED_WORDLIST:
                    # print("Checking for similar matches to '{0}'".format(pword))
                    for ocrword, freq in wlist.items():
                        if Ldistance(pword, ocrword) < 3: # close hits.
                            # print("Match: P({0}) ~= OCR({1})".format(pword, ocrword))
                            key_words[Ldistance(pword, ocrword)][pword][ocrword] += freq
            except NewspaperAccessError as e:
                print("Couldn't load reference '{0}' - moving on".format(ref))
    if store_as:
        with open(store_as, "w") as ofp:
            json.dump(key_words, ofp, indent=4, sort_keys=True)
    return key_words

def add_contextual_words(wordlist_json_filename, wordsets, bigram_filename, store_as):
    wordset = get_flat_wordlist(wordsets = wordsets, wordlist_json_filename = wordlist_json_filename)
    wlist = LISTS.get_wordlist_json(wordlist_json_filename).copy()
    
    bigram_words = [x.split(" ") for x,y in LISTS.get_bigram_json(bigram_filename = bigram_filename)]
    
    bi_fd = nltk.FreqDist(itertools.chain.from_iterable(bigram_words))
    
    wlist['contextual'] = {}
    
    for k, v in bi_fd.items():
        if k not in wordset:
            print("Adding '{0}'".format(k))
            if k not in wlist['contextual']:
                wlist['contextual'][k] = 0
            wlist['contextual'][k] += v
        
    if store_as:
        with open(store_as, "w") as ofp:
            json.dump(wlist, ofp, indent=4, sort_keys=True)
    return wlist


def create_lists(positive_references = ["abomentions.csv", "misc.csv"], negative_references = ["nonabospeeches.csv"], force_refresh = False):
    import os
    # Create the base wordlist:
    if force_refresh or not os.path.isfile("wordlist_with_errors.json"):
        print("Creating base word list from the PRIMED_WORD_LIST, with the 1- and 2- distance words harvested")
        wl = get_primed_wordlist_levenshtein(positive_references + negative_references, store_as = "wordlist_with_errors.json")
        
    # create base bigram files, if they don't already exist:
    if force_refresh or not os.path.isfile("bigram_exact.json"):
        print("Creating bigram_exact.json (just the exact matches from '{0}'".format(positive_references))
        cw = get_context_words_from_bigrams(positive_references, wordsets = ["0"], store_as = "bigram_exact.json", threshold = 5000)
        
    if force_refresh or not os.path.isfile("bigram.json"):
        print("Creating bigram_exact.json (just the exact matches, and 1-distant from '{0}')".format(positive_references))
        cw = get_context_words_from_bigrams(positive_references, wordsets = ["0", "1"], store_as = "bigram.json", threshold = 5000)
    
    if force_refresh or not os.path.isfile("bigram_1distant.json"):
        print("Creating bigram_exact.json (just the 1-distant words from '{0}')".format(positive_references))
        cw = get_context_words_from_bigrams(positive_references, wordsets = ["1"], store_as = "bigram_1distant.json", threshold = 5000)

    if force_refresh or not os.path.isfile("wordlist_with_errors_w_bigram.json"):
        print("Creating a wordlist with words derived from the bigram 0- and 1- distance file")
        add_contextual_words("wordlist_with_errors.json", wordsets = ["0", "1"], 
                             bigram_filename = "bigram.json", store_as = "wordlist_with_errors_w_bigram.json")

def deep_scan(daterange = [1845, 1895], newspapers = NEWSPAPERS, codeword = "mk1", threshold = 50.0):
    cls = train_sets(profile = "articles")
    labels = ["abomentions", "nonabospeeches", "misc", "control"]
    with open("deepscan_{0}.csv".format(codeword), "w") as hfp:
        fields = ['newspaper', 'year', 'month', 'day','page','article'] + [hash_profile(x)+"__"+label for x,_ in cls for label in labels]
        doc = csv.DictWriter(hfp, fieldnames = fields)
        
        doc.writerow({f:f for f in fields})
        
        for ref in n.all_available_newspapers(newspapers, daterange):            
            try:
                ndoc = n.get(**ref)
                for page in ndoc:
                    for article in ndoc[page]:
                        refl = ref.copy()
                        refl['page'] = page
                        refl['article'] = article
                        results = []
                        triggered_threshold = False
                        for p, cl in cls:
                            refl.update(p)
                            pd = cl.prob_classify(get_featureset_primed(**refl))
                            for l in labels:
                                refl[hash_profile(p)+"__"+l] = "{0:2f}".format(pd.prob(l) * 100)
                                results.append(refl[hash_profile(p)+"__"+l])
                                if l == "abomentions" or l == "misc":
                                    if float(results[-1]) > threshold:
                                        triggered_threshold = True
                        if triggered_threshold != False:
                            doc.writerow({k:v for k,v in refl.items() if k in fields})
                            print("{newspaper} {year}/{month}/{day} pg{page} art{article} - {results}".format(results = results, **refl))
                        else:
                            print("TOO LOW {newspaper} {year}/{month}/{day} pg{page} art{article} - {results}".format(results = results, **refl))
            except (NoSuchDocumentFound, ValueError) as e:
                print("NOT FOUND {newspaper} {year}/{month}/{day}".format(**ref))
        
def hunt_for_matches():
    cls = train_sets(profile = "articles")
    newslist = get_samplelist_from_all(30)
    
    labels = ["abomentions", "nonabospeeches", "misc", "control"]
    
    with open("articlehunt_w_prox.csv", "w") as hfp:
        fields = ['newspaper', 'year', 'month', 'day','page','article'] + [hash_profile(x)+"__"+label for x,_ in cls for label in labels]
        doc = csv.DictWriter(hfp, fieldnames = fields)
        
        doc.writerow({f:f for f in fields})
        
        for ref in newslist:
            try:
                ndoc = n.get(**ref)
                for page in ndoc:
                    for article in ndoc[page]:
                        refl = ref.copy()
                        refl['page'] = page
                        refl['article'] = article
                        results = []
                        for p, cl in cls:
                            refl.update(p)
                            pd = cl.prob_classify(get_featureset_primed(**refl))
                            for l in labels:
                                refl[hash_profile(p)+"__"+l] = "{0:2f}".format(pd.prob(l) * 100)
                                results.append(refl[hash_profile(p)+"__"+l])
                        doc.writerow({k:v for k,v in refl.items() if k in fields})
                        print("{newspaper} {year}/{month}/{day} pg{page} art{article} - {results}".format(results = results, **refl))
            except (NoSuchDocumentFound, ValueError) as e:
                print("NOT FOUND {newspaper} {year}/{month}/{day}".format(**ref))