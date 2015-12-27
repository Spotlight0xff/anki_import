# Anki Import script

## Installation
No Installation of the software, just use the import.py script.


But to support \includegraphics, you have to change the Anki sourcecode:

* download Anki sourcecode from [github.com](https://github.com/dae/anki)
* edit anki/latex.py, change `tmplatex = latex.replace("\\includegraphics", "")` to `tmplatex = latex`
* run anki from the runanki script in the anki directory (always, create a shortcut)


To support LaTeX packages, use these following steps:
* open Anki (desktop version)
* Tools -> Manage Note Types
* select a note type or create a new one
* click on options while selected
* add your LaTeX packages in the header field:
```
\usepackage{siunitx}
\usepackage{graphicx}
\usepackage{color}
\usepackage[autostyle=true,german=quotes]{csquotes}
```
* enjoy some juicy LaTeX

## Usage
./import.py -i <inputfile> -o <outputfile> -m <media directory> -a <anki media directory>

	-i,--ifile=<inputfile>
	
	-o,--ofile=<outfilefile> (optional)
	
	-m,--media=<media directory> (optional)
	
	-a,--anki=<anki media directory> (optional)

## Disclaimer
Quick & Dirty script, may burn your computer.
