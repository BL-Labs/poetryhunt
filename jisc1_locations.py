import os

_root_host = "w2k3-lonbit2"

SHARES = ["JISC1_VOL1_C0","JISC1_VOL2_C0","JISC1_VOL3_C1","JISC1_VOL4_C1","JISC2_VOL1_C0","JISC2_VOL2_C0","JISC2_VOL3_C1","JISC2_VOL4_C1","JISC3_VOL1_C0","JISC3_VOL2_C0","JISC3_VOL3_C1","JISC3_VOL4_C1"]

JISC1_LOCATIONS = ["//{0}/{1}".format(_root_host, x) for x in SHARES]

def scan_for_service_dirs(root, outputfilename):
  with open(outputfilename, "w") as op:
    for (dirpath, subdirs, fns) in os.walk(root):
      if dirpath.endswith("service"):
        _, newspaper, year, month, day, service = dirpath.rsplit("/", 5)
        op.write(u",".join([unicode(x) for x in [dirpath, newspaper, year, month, day]]).encode("utf-8"))
        op.write(u"\n".encode("utf-8"))
        print(dirpath, newspaper, year, month, day)

if __name__ == "__main__":
  for loc in JISC1_LOCATIONS:
    if not os.path.isfile("//192.168.15.153/ba/" + loc.rsplit("/")[-1] + ".csv"):
      scan_for_service_dirs(loc, "//192.168.15.153/ba/" + loc.rsplit("/")[-1] + ".csv")

