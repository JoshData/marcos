import json, random

def gen(tok, pos, db, depth=0, force_base=False):
	# Base case?
	if depth > 3 or tok not in db or force_base:
		return { "-LSB-": "[", "-RSB-": "]" }.get(tok, tok)

	# Choose a frame.
	if pos and pos in db[tok]:
		frames = db[tok][pos]
	else:
		frames = random.choice(list(db[tok].values()))
	frame = random.choice(frames)

	# Generate.
	def pre_token(rel):
		if "_" in rel:
			return rel.split("_")[1] + " "
		else:
			return ""
	return " ".join(
		pre_token(relationship)
		+ gen(lex, pos, db, depth=depth+1, force_base=relationship == "HEAD")
		for relationship, pos, lex in frame
		if relationship != "HEAD" or lex != "ROOT"
	)

with open("db.json") as f:
	db = json.load(f)

print(gen("ROOT", None, db))
