markos
======

A generative model for natural language using a markov chain over syntactic relations, rather than serial order.

Overview
--------

With a typical markov chain sentence generator, each word maximizes the liklihood of that word ocurring given the previous word. That is, you start with a word. Then to generate subsequent words, you take the previous word, consult an existing body of text (the training corpus), and find the most frequent word that follows the previous word. And repeat.

The insight of the markov chain generator is that by making only local decisions, and doing so recursively, can produce a sentence that looks overall sort of like a person might have said it.

In `markos`, the local decision isn't about the serial order of words but instead about the possible syntactic relations between words. Each word is chosen to maximize the liklihood that it will be in a dependent relation (argument/complement/modifier) with the previous word (and it is positioned according to syntatic structure).Generation of new sentences works by descending a syntactic tree, starting at the root, rather than moving left to right.

Example
-------

Here's an example of how generation works. A sentence unfolds from the top.

	                 (ROOT)
	                   ⇓
	              [(uses/VBZ)]
	                   ⇓
	    [(Senate/NNP) uses (voting/NN)]
	         ⇓
	[(the/DT) Senate] uses (voting/NN)
	       ⇓
	     [the] Senate uses (voting/NN)
	                               ⇓
	       the Senate uses [(electronic/JJ) voting]
	                             ⇓
	       the Senate uses [electronic] voting

	The Senate uses electronic voting.

In each step, a placeholder is replaced by a random "frame," which includes exactly one actual word and zero or more placeholders around it. I'm using "frame" loosely but in the sense of a "verb frame", which describes the possible arguments a verb has. Here I mean a word's local syntactic structure. (This is analogous to a context free grammar production or a tree adjoining grammar lexical entry.) This process repeats until there are no placeholders left.

The training step uses the Stanford Parser to parse a corpus of text in order to infer the syntactic frames. The frames in this example were:

	(Senate/NNP) uses (voting/NN)
	(the/DT) Senate
	(electronic/JJ) voting

Note that each frame selects the lexical items in the next step, but the frame of that lexical item is up to chance.

Installation
------------

You will need [Java 8](http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) to run the Stanford Parser.

You will need the [Stanford Parser](http://nlp.stanford.edu/software/lex-parser.shtml), a statistical syntactic parser. The `markos` algorithm doesn't depend on anything proprietary to the way the Standard Parser works, but it was the first parser I tried and it worked well, so `markos` is built around its particular output. Download the Stanford Parser and extract it into a directory named `standford-parser` inside this project's directory (i.e. you'll have `markos/stanford-parser/stanford-parser.jar`):

	wget http://nlp.stanford.edu/software/stanford-parser-full-2014-10-31.zip
	unzip stanford-parser-full-2014-10-31.zip
	mv stanford-parser-full-2014-10-31 stanford-parser

Optionally install `tqdm` which provides a nice progress meter while training:

	pip3 install tqdm

Training
--------

Copy a large amount of text into a file named `sample.txt`. By large I mean on the order of about 10,000 words or 50 kilobytes. So not that large.

Build the training database by passing `train.py` some text on standard input:

	python3 train.py < sample.txt 

It will write `db.json` containing the language model. On a 10,000 word page from Wikipedia, this took about 5 minutes.

Each sentence is parsed one by one by launching the Stanford Parser (a Java process) for each. It is slow. A future enhancement could be to chunk the input (the parser can handle multiple sentences at once, but it is more likely to run out of memory and die).

Generation
----------

To generate a new sentence:

	python3 gen.py

This starts with the (ROOT) frame always and unfolds a sentence from there.

Copying
-------

This repository is dedicated to the public domain using the Creative Commons Zero 1.0 Public Domain Dedication.
