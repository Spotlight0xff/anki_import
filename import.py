#!/usr/bin/env python
#   Copyright 2016 @spotlight0xff
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys, getopt, os, regex,re
from PIL import Image
import shutil
import hashlib

images = []
ifile = None
ofile = None
ankimedia = None
media = None
verbose = False

def print_list(l):
    for k in l:
        print(k)
    print("\n")

def items2anki(items, keywords):
    global images,media
    (title, lines_old) = items
    lines = lines_old.splitlines()
    lines_new = []
    count_itemize = 1

    for line in lines:
        if line.isspace() or line == '':
            continue
        if line.strip().startswith('%'):
            continue

        # handle encapsulated lists
        count_itemize += line.count("\\begin{itemize}")
        count_itemize -= line.count("\\end{itemize}")
        # if line.find("\\begin{itemize}") != -1:
            # count_itemize += 1

        # some visibility replaces
        line = line.replace("<", "&lt;")
        line = line.replace(">", "&gt;")
        line = line.replace("\t","    ") # \t is our separator

        for k in keywords:
            if title != k and line.count('\\includegraphics') == 0: # if not itself...
                #line = line.replace(k.strip(), "\\textcolor[rgb]{1,0,0}{"+k.strip()+"}")
                subst = re.compile(re.escape(k.strip()), re.IGNORECASE)
                line = subst.sub(r"\\textcolor[rgb]{1,0,0}{"+k.strip()+"}", line)

        # remove \autoref{.*}, replace with figurename
        match = regex.search(r'\\autoref\{fig:(.*?)\}', line)
        if match: # we only want the alphanumeric figure name( elsewise latex crashes)
            fig = match.group(1)
            fig = re.sub(r'[^a-zA-Z0-9]', '', fig)
            line = regex.sub(r'\\autoref\{fig:(.*?)\}', fig, line)

        # make images work
        matches = regex.finditer(r'\\includegraphics(\[.*?\])?\{(.*?)\}', line)
        for match in matches:
            # TODO: os.path.splitext
            if match.group(2).endswith('.png'):
                image = media+match.group(2)
            else:
                image = media+match.group(2)+".png"
            # TODO: probably doesn't work if there are initially no options
            if os.path.exists(image): # replace includegraphics with more verbosed version (to make latex work)
                images.append(image)
                im = Image.open(image)
                (width, height) = im.size
                options = match.group(1).rstrip(']')+",natwidth="+str(width)+",natheight="+str(height)+']'
                if verbose:
                    print(match.group(2)+": "+options)
                pat = '\\includegraphics'+match.group(1)+'{'+match.group(2)+'}'
                repl = '\includegraphics'+options+'{'+image+'}'
                line = line.replace(pat, repl)


        lines_new.append(line)

    txt = "[latex]"
    txt += "\\begin{itemize}"
    txt += "".join(lines_new)
    txt += "\\end{itemize}"*count_itemize
    txt += "[/latex]"
    return txt


def get_paragraphs(text):
    length = len(text)
    it = 0
    #anki = ''
    paras_content = []
    paras_start = []
    paras = []

    for para in re.finditer(r'\\(section|subsection|subsubsection|paragraph)\*?{', text):
        start = para.start()
        end = para.end()
        paras_start.append(start)

    count = 0
    for start in paras_start:
        if count < len(paras_start)-1:
            # print(str(start)+":"+str(paras_start[count+1]))
            para = text[start:paras_start[count+1]]
        else: # last
            para = text[start:]
        paras_content.append(para)
        count += 1

    # print("count paragraphs: "+str(count))
    count = 0
    for para in paras_content:

        # fuck off, Lennard-Jones-Potential!
        first_itemize = re.search(r'\\begin\{itemize\}', para)
        if first_itemize:
            para_title = re.search(r'\\paragraph\*?{(.*)}', para[:first_itemize.start()])
            if para_title:
                # print(para_title.group(1))
                match = re.search(r'\\begin\{itemize\}(\[.*?\])?([\s\S]*)\\end\{itemize\}', para[first_itemize.start():])
                if match:
                    title = para_title.group(1).rstrip(':')
                    paras.append((title, match.group(2)))
                    count += 1


    return paras

def hash(fname):
    hash = hashlib.sha512()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()

def copy_images():
    global images, media, ankimedia, verbose
    count = 0
    if verbose:
        print("Copying "+str(len(images))+" images")
    for image in images:
        filename = os.path.basename(image)
        if verbose:
            print("Copy "+filename+" from "+media+" to "+ankimedia)
        src = os.path.join(media, filename)
        dst = os.path.join(ankimedia, filename)
        if os.path.exists(dst):
            hash_src = hash(src)
            hash_dst = hash(dst)
            if hash_src == hash_dst:
                if verbose:
                    print("same file exists there already, skipping")
                continue

        if verbose:
            print("copy "+src+" -> "+dst)
        try:
            shutil.copy(src, dst)
            count += 1
        except Exception as e:
            print(e)
    print("Copied "+str(count)+" files")


def extract_keywords(paras):
    keywords = []
    for para in paras:
        title = para[0]
        tmp = title.split('\mathrm{oder}')
        for t in tmp:
            t = re.sub('\$', '', t)
            t = re.sub('\s+', ' ', t)
            t = re.sub('\\\\mathrm{(.*?)}', '\\1', t)
            t = re.sub('\\\\[a-z]*\{(.*?)\}', '\\1', t)
            t = re.sub('\((.*?)\)', '\\1', t)
            t = re.sub('\[(.*?)\]', '\\1', t)
            t = re.sub('\{(.*?)\}', '\\1', t)
            t = re.sub('\\\\[a-z]+','', t)
            t = re.sub('(^|\s+)\w($|\s+)', '', t) # remove single words
            t = re.sub('(^|\s+)[A-Z_\-]+($|\s+)', '', t) # remove words like SL, B_C etc.
            t = t.strip()
            keywords.append(t)
            # print("-"+t+"-")
    return keywords

def main(argv):
    global ifile,ofile,ankimedia,media,verbose
    if (len(argv)) == 0:
        usage()
        sys.exit(0)

    try:
        opts, args = getopt.getopt(argv, 'hvi:o:m:a:', ['ifile=', 'ofile=','media=','ankimedia=','verbose'])
    except getopt.GetoptError:
        usage()
        sys.exit(0)
    for opt,arg in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-i', '--ifile'):
            ifile = arg
        elif opt in ('-o', '--ofile'):
            ofile = arg
        elif opt in ('-m', '--media'):
            media = arg
        elif opt in ('-a', '--ankimedia'):
            ankimedia = arg

    if not ifile:
        print("Input file argument is mandatory.")
        usage()
        sys.exit(1)

    if not ofile: # but ifile is provided
        try:
            ofile = ifile.split('.')[-2] + '.txt'
        except:
            print("input file is not formatted correctly")
            usage()
            sys.exit(2)

    if not os.path.exists(ifile):
        print('Input file "'+ifile+'" not existing.')
        usage()
        sys.exit(3)

    if not media:
        # no media dir, lets guess
        media = os.path.abspath(os.path.dirname(ifile))+"/"
        print("Using "+media+" as media directory.")

    if not ankimedia:
        # lets try to guess it.
        home = os.path.expanduser("~")
        anki_dir = os.path.join(home, "Anki")
        if not os.path.exists(anki_dir):
            # lets try something else
            anki_dir = os.path.join(os.path.join(home,"Documents"), "Anki")
            if not os.path.exists(anki_dir):
                print("Could not guess anki media directory.")
                print("Please provide it with -a")
                usage()
                sys.exit(4)

        # so, we've got now the anki-dir, lets enumerate profiles.
        candidates = []
        for d in os.listdir(anki_dir):
            if not os.path.isdir(os.path.join(anki_dir, d)):
                continue
            profile_dir = os.path.join(anki_dir, d)
            col_media = os.path.join(profile_dir, "collection.media")
            if os.path.exists(col_media):
                if os.path.isdir(col_media):
                    candidates.append(d)

        if not len(candidates) == 1:
            print("guessed anki directory: "+anki_dir)
            print("multiple profiles with media collections found:")
            for profile in candidates:
                print("* "+profile)
            print("please provide a media collection directory with -a")
            usage()
            sys.exit(4)
        else: # choosen one
            ankimedia = os.path.join(os.path.join(anki_dir, candidates[0]), "collection.media")


            
    print('Input file is '+ifile)
    print('Output file is '+ofile)
    print('Anki media directory is '+ankimedia)

    text = ''

    try:
        f = open(ifile, 'r')
        text = f.read()
        f.close()
    except Exception as e:
        print('error while reading input file:')
        print(e)
        sys.exit(0);

    # lets do the work
    paras = get_paragraphs(text)
    anki = ''
    keywords = extract_keywords(paras)
    for para in paras:
        txt = items2anki(para, keywords)
        anki += "[latex]"+para[0]+"[/latex]"+"\t"+txt+"\n"
    copy_images()
    f = open(ofile, 'w')
    f.write(anki)
    f.close()
    print("Written output to "+ofile)



def usage():
    print("Usage: "+__file__+" -i <inputfile> -o <outputfile> -m <media directory> -a <anki media directory>")
    print("\t-i,--ifile=<inputfile>")
    print("\t-o,--ofile=<outfilefile> (optional)")
    print("\t-m,--media=<media directory> (optional)")
    print("\t-a,--anki=<anki media directory> (optional)")

if __name__ == '__main__':
    main(sys.argv[1:])
