#!/usr/bin/env python
import sys, getopt, os, regex,re

def items2anki(items, mdir):
    lines = items.splitlines()
    lines_new = []
    images = []

    for line in lines:
        if line.isspace() or line == '':
            continue
        line = line.strip()
        # remove "\item "
        if line.startswith('\item '):
            line = line[6:]

        # remove \autoref{.*},
        match = regex.search(r'\\autoref\{fig:(.*?)\}', line)
        if match: # we only want the alphanumeric figure name( elsewise latex crashes)
            fig = match.group(1)
            fig = re.sub(r'[^a-zA-Z0-9]', '', fig)
            line = regex.sub(r'\\autoref\{fig:(.*?)\}', fig, line)

        # make images work
        # TODO:
        # * check if image exists (+ autodetect extension)
        # * validate mdir properly
        match = regex.search(r'\\includegraphics(\[.*?\])?\{(.*?)\}', line)
        if match:
            line = regex.sub(r'\\includegraphics(\[.*?\])?\{(.*?)\}', '\\2', line)
            images.append(match.group(2)+".png")

        if re.match(r'bravais', line):
            print(line)
        lines_new.append(line)

    txt = "[latex]"+"\\\\".join(lines_new)+"[/latex]"
    txt += "<br>"
    for image in images:
        txt += '<img src="'+image+'" /><br>'
    return txt


def get_paragraphs(text, mdir):
    length = len(text)
    it = 0
    anki = ''
    # todo r'', never change a running system... :/
    matches = regex.findall('\\\\(paragraph|section|subsection|subsubsection)\*?\{(.*?):?\}\s*\\\\begin\{itemize\}(\[.*?\])?((.|\s)*?)\\\\end\{itemize}', text)
    for match in matches:
        title = match[1]
        items = match[3]
        txt = items2anki(items, mdir)
        #print(title+":\n"+txt+"\n\n\n")
        anki += "[latex]"+title+"[/latex]"+";"+txt+"\n"
    return anki


def main(argv):
    if (len(argv)) == 0:
        usage()
        sys.exit(0)

    ifile = None
    ofile = None
    mdir = None
    try:
        opts, args = getopt.getopt(argv, 'hi:o:m:', ['ifile=', 'ofile=','media='])
    except getopt.GetoptError:
        usage()
        sys.exit(0)
    for opt,arg in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        elif opt in ('-i', '--ifile'):
            ifile = arg
        elif opt in ('-o', '--ofile'):
            ofile = arg
        elif opt in ('-m', '--media'):
            mdir = arg

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

    if not mdir:
        mdir = '.'
        print('media directory is mandatory.')
        #usage()
        #sys.exit(4) 
        ## TODO


    print('Input file is '+ifile)
    print('Output file is '+ofile)

    text = ''

    try:
        f = open(ifile, 'r')
        text = f.read()
        f.close()
    except Exception as e:
        print('error while reading input file:')
        print(e)
        sys.exit(0);

    anki = get_paragraphs(text, mdir)
    f = open(ofile, 'w')
    f.write(anki)
    f.close()



def usage():
    print("Usage: "+__file__+" -i <inputfile> -o <outputfile> -m <media directory>")
    print("\t-i,--ifile=<inputfile>")
    print("\t-o,--ofile=<outfilefile>")
    print("\t-m,--media=<media directory>")

if __name__ == '__main__':
    main(sys.argv[1:])
