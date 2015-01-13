import re, subprocess, json, sys

try:
	# Optional dependency. Shows nice progress.
	from tqdm import tqdm
except ImportError:
	def tqdm(iter):
		return iter

STANFORD_PARSER_PATH = "stanford-parser"

def parse(sentences):
	# Run the Stanford Parser to get a dependency parse. It will parse multiple
	# sentences and split them up into sentences for us.
	def run_stanford_parser(quiet):
		return subprocess.check_output(
			"java -mx768m -cp \"%s/*:\" edu.stanford.nlp.parser.lexparser.LexicalizedParser -outputFormat wordsAndTags,typedDependencies edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz /dev/stdin"
			% STANFORD_PARSER_PATH,
			input=sentences.encode("utf8"),
			shell=True,
			stderr=subprocess.DEVNULL if quiet else subprocess.STDOUT
			)
	try:
		output = run_stanford_parser(True)
	except subprocess.CalledProcessError as e:
		if e.returncode == 127:
			print("Is Java installed? Executing 'java' failed.", file=sys.stderr)
			sys.exit(1)
		if e.returncode == 1:
			# Run it again but don't squelch standard error so it can
			# print its own problem.
			try:
				run_stanford_parser(False)
			except subprocess.CalledProcessError as e:
				if b'Could not find or load main class' in e.output:
					print("Is the Stanford Parser in the %s directory?" % STANFORD_PARSER_PATH, file=sys.stderr)
				elif b'OUT OF MEMORY!' in e.output:
					print("Not enough memory to parse \"%s\". Skipping." % sentences, file=sys.stderr)
					return # return before 'yield'ing anything
				else:
					# Write the bytes output directly to stderr.
					sys.stderr.buffer.write(e.output)
			sys.exit(1)
		raise

	# Decode and split on newlines.
	output = output.decode("utf8").split("\n")

	# Parse output.
	while len(output) > 0:
		# For each sentence parsed...

		# The first line gives us part-of-speech tags. We get a line that looks like:
		#   word1/TAG1 word2/TAG2 . . .
		# Just get a list of the tags in order.
		pos_tagger = output.pop(0)
		if pos_tagger.strip() == "": continue
		words = pos_tagger.split(" ")
		pos_tags = [lex_tag.split('/')[1] for lex_tag in words]

		# Empty line.
		output.pop(0)

		# Parse the parser output to get the dependencies leaving
		# each head word. We get a list of dependency relations:
		#
		# relation(headword/INDEX1, dependentword/INDEX2)
		#
		# The indexes indicate the serial position of the word in
		# the sentence, also corresponding to the part-of-speech
		# tags above.

		def parse_tok(tok):
			# Take a 'token-index' string and return
			# (index, token, part of speech).
			tok = tok.replace("'", "")
			lex, index = tok.rsplit('-', 1)
			index = int(index)
			return (index, lex, pos_tags[index-1])

		heads = { }
		all_tokens = set()

		while len(output) > 0:
			line = output.pop(0)
			if len(heads) > 0 and line.strip() == "":
				# End of this sentence.
				break

			# Parse the line.
			m = re.match(r"([a-z_]+)\((.*), (.*)\)", line)
			if not m: raise ValueError(line)
			relation, tok1, tok2 = m.groups()
			try:
				tok1 = parse_tok(tok1)
				tok2 = parse_tok(tok2)
			except:
				print(line)
				raise

			# Now we have a relation, the head token (tok1), and the
			# dependent token (tok2). Start building a frame for tok1,
			# meaning the relations it has to other words in the sentence.
			if tok1 not in heads:
				# Create an array to hold the relations from tok1.
				# Add a dummy relation to represent the position
				# of the token relative to its dependencies.
				heads[tok1] = [ ]
				heads[tok1].append( ('HEAD', tok1) )

			# Add the relation into the frame.
			heads[tok1].append( (relation, tok2) )

			# Remember all of the dependents we see. 
			all_tokens.add(tok2)

		# Some tokens are just dependencies without dependents of their own,
		# and create degenerate frames for them too consisting of just the
		# word itself.
		for tok in all_tokens:
			if tok not in heads:
				heads[tok] = [ ('HEAD', tok) ]

		# Build syntactic frames by putting the dependencies of each head
		# into serial order.
		for head, dependencies in heads.items():
			# Put the dependencies in serial order.
			frame = sorted(dependencies, key = lambda x : x[1][0])

			# Remove the index of each token, so the frame is just a list
			# of tuples of (relation, part-of-speech, token).
			frame = [(f[0], f[1][2], f[1][1]) for f in frame]

			# Return a tuple of (head token, head part-of-speech, frame).
			yield (head[1], head[2], frame)

if __name__ == "__main__":
	# Train based on the content given on standard input.

	# Split corpus on what we think are sentences.
	corpus = sys.stdin.read().split(". ")

	# Parse each sentence and build a database of all of the
	# word frames we see, grouped by head word and its part
	# of speech,. e.g.
	# db = {
	#   "computes": {
	#     "VB": [ # ie. "the project computes markov chains"
	#        [("subj", "NN", "project")],
	#        [("obj",  "NN", "chains")],
	#     ]
	#   }
	# }
	db = { }
	for sentence in tqdm(corpus):
		for word, part_of_speech, frame in parse(sentence):
			db.setdefault(word, {})\
			  .setdefault(part_of_speech, [])\
			  .append(frame)

	# Save.
	with open("db.json", "w") as f:
		json.dump(db, f, sort_keys=True, indent=2)
