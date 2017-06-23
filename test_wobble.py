from textareasweep import get_columns, get_article_list
servfn = "//p12l-nas6/JISC2_VOL1_C0/097/2001-0346/WO1/LEMR/1873/01/04/service"
a = get_article_list(servfn)
b = a[10]
d = get_columns(servfn + "/" + b)
