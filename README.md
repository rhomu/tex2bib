# tex2bib
Fetches bibtex citations from multiple tex files and prints to stdout.
We are using the very good [arix2bib](https://github.com/nathangrigg/arxiv2bib) by Nathan Grigg shamelessly.

This script searches all latex citations of the form `\cite{xxx:yyy}`, where `xxx` denotes the source (see below) and `yyy` is the document identifier, then fetches and prints the relevant citations with the bibtex identifier replaced by `xxx:yyy`. This means that you can use the bibtex ctation directly with your document. See examples in [example.tex](example.tex).

Available sources:
- `doi`, using [crossref.org](http://search.crossref.org)
- `arXiv`, using [arix2bib](https://github.com/nathangrigg/arxiv2bib)
- `inspire`, using [inspirehep.net](https://inspirehep.net/)

Very basic usage:

    $ python tex2bib.py file1 file2 ...

Wildcards can be used.
