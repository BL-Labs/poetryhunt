def profile_list(listname = "all"):
    if listname == "all":
        return [{"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0"], 
                "b_file": "bigram_exact.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0"], 
                "b_file": "bigram_exact.json",
                "contains_f": True, 
                "has_f": False, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0"], 
                "b_file": None,
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["1"], 
                "b_file": None,
                "contains_f": True, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0", "1"], 
                "b_file": "bigram_1distant.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0", "1", "2"], 
                "b_file": "bigram_1distant.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors_w_bigram.json", 
                "wordsets": ["0", "1", "contextual"], 
                "b_file": "bigram.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               {"w_file": "wordlist_with_errors_w_bigram.json", 
                "wordsets": ["0", "contextual"], 
                "b_file": "bigram.json",
                "contains_f": True, 
                "has_f": True, 
                "md_f": False,
                "refs": "allrefs"},
               ]
    elif listname == "articles":
        return [
      #         {"w_file": "wordlist_with_errors.json", 
      #          "wordsets": ["0"], 
      #          "b_file": "bigram_exact.json",
      #          "contains_f": False, 
      #          "has_f": True, 
      #          "md_f": False,
      #          "refs": "articles",
      #          "prox_f": False},
                {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0"], 
                "b_file": "bigram_exact.json",
                "contains_f": True, 
                "has_f": False, 
                "md_f": False,
                "refs": "articles",
                "prox_f": True},
      #         {"w_file": "wordlist_with_errors.json", 
      #          "wordsets": ["0"], 
      #          "b_file": "bigram_exact.json",
      #          "contains_f": True, 
      #          "has_f": False, 
      #          "md_f": False,
      #          "refs": "articles"},
      #         {"w_file": "wordlist_with_errors.json", 
      #          "wordsets": ["0"], 
      #          "b_file": None,
      #          "contains_f": False, 
      #          "has_f": True, 
      #          "md_f": False,
      #          "refs": "articles"},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["1"], 
                "b_file": None,
                "contains_f": True, 
                "has_f": True, 
                "md_f": False,
                "refs": "articles",
                "prox_f": True},
       #        {"w_file": "wordlist_with_errors.json", 
       #         "wordsets": ["1"], 
       #         "b_file": None,
       #         "contains_f": True, 
       #         "has_f": True, 
       #         "md_f": False,
       #         "refs": "articles",
       #         "prox_f": False},
       #        {"w_file": "wordlist_with_errors.json", 
       #         "wordsets": ["0", "1"], 
       #         "b_file": "bigram_1distant.json",
       #         "contains_f": False, 
       #         "has_f": True, 
       #         "md_f": False,
       #         "refs": "articles"},
       #        {"w_file": "wordlist_with_errors.json", 
       #         "wordsets": ["0", "1", "2"], 
       #         "b_file": "bigram_1distant.json",
       #         "contains_f": False, 
       #         "has_f": True, 
       #         "md_f": False,
       #         "refs": "articles",
       #         "prox_f": False},
               {"w_file": "wordlist_with_errors.json", 
                "wordsets": ["0", "1", "2"], 
                "b_file": "bigram_1distant.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "articles",
                "prox_f": True},
               {"w_file": "wordlist_with_errors_w_bigram.json", 
                "wordsets": ["0", "1", "contextual"], 
                "b_file": "bigram.json",
                "contains_f": False, 
                "has_f": True, 
                "md_f": False,
                "refs": "articles",
                "prox_f": True},
       #        {"w_file": "wordlist_with_errors_w_bigram.json", 
       #         "wordsets": ["0", "1", "contextual"], 
       #         "b_file": "bigram.json",
       #         "contains_f": False, 
       #         "has_f": True, 
       #         "md_f": False,
       #         "refs": "articles",
       #         "prox_f": False},
       #        {"w_file": "wordlist_with_errors_w_bigram.json", 
       #         "wordsets": ["0", "contextual"], 
       #         "b_file": "bigram.json",
       #         "contains_f": True, 
       #         "has_f": True, 
       #         "md_f": False,
       #         "refs": "articles",
       #         "prox_f": False},
               ]
   
    