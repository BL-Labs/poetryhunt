#python3
import re, os

text_p = re.compile(r"CONTENT=\"([^\"]*)\"", re.U)
line_p = re.compile(r"</TextLine>", re.U)

def get_text(alto_filepath):
  current = ""
  text_content = ""
  words = []
  with open(alto_filepath, "r", encoding="utf-8") as alto:
    for line in alto:
      if line_p.search(line) != None:
        if current != "":
          words.append(current)
        text_content += " ".join(words)
        text_content += "\n"
        words = []
        current = ""
      else:
        g = text_p.search(line)
        if g != None:
          txt = g.groups()[0]
          if current != "":
            # if two words are 'joined' by a hyphen, concat.
            # if 1st ends with hyphen, but not reciprocated, return both as separate words
            # Also, some ALTO XML marks this up:
            #  <String ID="P13_ST00253" HPOS="1167" VPOS="1886" WIDTH="75" HEIGHT="36" CONTENT="shap" SUBS_TYPE="HypPart1" SUBS_CONTENT="shaping" WC="0.82" CC="07100"/>
            #  <HYP CONTENT="-"/>
            #</TextLine>
		  		  #<TextLine ID="P13_TL00028" HPOS="132" VPOS="1935" WIDTH="1110" HEIGHT="40">
			  	  #  <String ID="P13_ST00254" HPOS="132" VPOS="1941" WIDTH="51" HEIGHT="34" CONTENT="ing" SUBS_TYPE="HypPart2" SUBS_CONTENT="shaping" WC="0.66" CC="360"/>
            #FIXME - deal with this form of markup additionally.
            if txt.startswith("-"):
              words.append(current[:-1] + txt[1:])
              current = ""
            else:
              words.append(current)
              words.append(txt)
              current = ""
          elif txt.endswith("-"):
            current = txt
          else:
            words.append(txt)
    if current != "":
      words.append(current)
    text_content += " ".join(words)
  return text_content

def get_book(book_id, directorypath, txtfilepath):
  with open(txtfilepath, "w", encoding="utf-8") as txtout:
    for item in sorted([x for x in os.listdir(directorypath) if x.startswith(book_id)]):
      txtout.write(get_text(os.path.join(directorypath, item)))
      txtout.write("\n")
