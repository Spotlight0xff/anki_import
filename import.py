#!/usr/bin/env python
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


def items2anki(items):
    global images,media
    lines = items.splitlines()
    lines_new = []
    count_itemize = 1

    for line in lines:
        if line.isspace() or line == '':
            continue

        # handle encapsulated lists
        if line.find("\\begin{itemize}") != -1:
            count_itemize += 1

        # some visibility replaces
        line = line.replace("<", "&lt;")
        line = line.replace(">", "&gt;")
        line = line.replace("\t","    ") # \t is our separator

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
    anki = ''
    matches = regex.findall('\\\\(paragraph|section|subsection|subsubsection)\*?\{(.*?):?\}\s*\\\\begin\{itemize\}(\[.*?\])?((.|\s)*?)\\\\end\{itemize}', text)
    for match in matches:
        title = match[1]
        items = match[3]
        txt = items2anki(items)
        anki += "[latex]"+title+"[/latex]"+"\t"+txt+"\n"
    return anki

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
    anki = get_paragraphs(text)
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
