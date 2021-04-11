# Prints the following from a LE save file:
# * Passive skill tree
# * Abilities & ability skill trees
# * equipment

# TODO  : Collect all stats from gear + passive tree
# TODO 2: Collect additional stats from ability trees
# TODO 3: Compute dps

import json
import sys
import os
import re
import Database

def print_mod(p, type, min, max, roll : int, modifier : float, display : str):
	final = (min + ((max - min) * (roll / 255))) * modifier

	reduced = 0
	if final < 0:
		final = -final
		reduced = 1

	if not (p and p["dontDisplayPlus"] == 1) and type == Database.ModType.Added:
		print('+', end='')

	if isinstance(min, float):
		if p and p["displayAddedAsTenthOfValue"] == 1:
			final = round(final * 10, 1)
		else:
			final = round(final * 100)
		print(str(final) + '%', end='')
	else:
		final = round(final)
		print(str(final), end='')

	if type == Database.ModType.Increased:
		if reduced:
			print(" reduced", end='')
		else:
			print (" increased", end='')
	elif type == Database.ModType.More:
		if reduced:
			print(" less", end='')
		else:
			print (" more", end='')

	if p and p["displayAsPercentageOf"]:
		print(" of", end='')
	elif p and p["displayAsAddedTo"]:
		print(" to", end='')

	print(' ' + display)

def parse_mod_implicit(db, imp, roll : int):
	mod = db.get_affix_property(imp["property"], imp["tags"])
	p = db.get_property(imp["property"], imp["tags"], imp["specialTag"])
	if not p:
		return

	display = p["propertyName"]
	type = imp["type"]
	# Not perfect. Should sometimes use the property name even if a mod is found (e.g +X potion slots)
	if mod:
		if "affixProperties" in mod:
			for ap in mod["affixProperties"]:
				if ap["property"] == imp["property"] and ap["tags"] == imp["tags"]:
					display = ap["modDisplayName"]
					break
		else:
			display = mod["affixDisplayName"]

	min = imp["implicitValue"]
	max = imp["implicitMaxValue"]
	print_mod(p, type, min, max, roll, 1, display)

def parse_mod_unique(db, m, roll : int):
	if m["hideInTooltip"]:
		return

	mod = db.get_affix_property(m["property"], m["tags"])
	p = db.get_property(m["property"], m["tags"], m["specialTag"])
	if not p:
		return

	display = p["propertyName"]
	type = Database.ModType.Added
	if mod:
		display = mod["affixDisplayName"]
		type = mod["modifierType"]

	min = m["value"]
	max = m["maxValue"]
	print_mod(p, type, min, max, roll, 1, display)

def parse_mod(db, data : int, affix_id : int, roll : int, modifier : float):
	mod = db.get_affix(affix_id + 256*(data & 0x0F))
	tier = (data & 0xF0) >> 4
	modifier = modifier - mod["standardAffixEffectModifier"]
	props = []
	if "property" in mod:
		props.append(db.get_property(mod["property"], mod["tags"], mod["specialTag"]))
	else:
		for ap in mod["affixProperties"]:
			props.append(db.get_property(ap["property"], ap["tags"], ap["specialTag"]))

	if tier >= len(mod["tiers"]):
		tier = len(mod["tiers"]) - 1
	for (i, p) in zip(range(0, 8), props):
		type = Database.ModType.Added
		display = ""
		if i == 0:
			min = mod["tiers"][tier]["minRoll"]
			max = mod["tiers"][tier]["maxRoll"]
			if len(props) > 1:
				display = mod["affixProperties"][0]["modDisplayName"]
				type = mod["affixProperties"][0]["modifierType"]
			else:
				display = mod["affixDisplayName"]
				type = mod["modifierType"]
		else:
			min = mod["tiers"][tier]["extraRolls"][i - 1]["minRoll"]
			max = mod["tiers"][tier]["extraRolls"][i - 1]["maxRoll"]
			display = mod["affixProperties"][i]["modDisplayName"]
			type = mod["affixProperties"][i]["modifierType"]

		print_mod(p, type, min, max, roll, modifier, display)

def parse_unique(db, item, basetype, subtype, d):
	u = db.get_unique(d[8])
	print(u["name"])
	print(basetype["displayName"])
	if not subtype["displayName"]:
		print(subtype["name"])
	else:
		print(subtype["displayName"])

	for (i, m) in zip(range(9, 17), u["mods"]):
		parse_mod_unique(db, m, d[i])

	for td in u["tooltipDescriptions"]:
		print(td["description"])

	print()

def parse_item(db, item):
	# skip inventory and buyback
	if item["containerID"] in [1, 32]:
		return

	d = item["data"]
	basetype = db.get_item_basetype(d[1])
	if not basetype:
		return
	subtype = Database.get_item_subtype(basetype, d[2])
	if not subtype:
		return

	if len(d) >= 4 and d[3] == 7: # unique
		parse_unique(db, item, basetype, subtype, d)
		return

	print(basetype["displayName"])
	if not subtype["displayName"]:
		print(subtype["name"])
	else:
		print(subtype["displayName"])

	if len(d) < 4:
		return

	# implicits
	if "implicits" in subtype:
		for (i, imp) in zip(range(4, 7), subtype["implicits"]):
			parse_mod_implicit(db, imp, d[i])

	# explicits
	print("------------")
	for i in range(0, d[8]):
		parse_mod(db, d[9 + i*3], d[10 + i*3], d[11 + i*3], 1 + basetype["affixEffectModifier"])

	print()

re_node_value = re.compile('(\+?)([0-9]+)(%?)')
def parse_node(root, nid : int, npoints : int):
	node = Database.get_node(root["nodeList"], nid)
	print("------------")
	print(node["nodeName"] + " " + str(npoints) + "/" + str(node["maxPoints"]))
	for s in node["stats"]:
		if s["value"]:
			se = re_node_value.search(s["value"])
			v = int(se.group(2))
			if not s["noScaling"]:
				v = v * npoints
			print(se.group(1) + str(v) + se.group(3) + " ", end='')
		print(s["statName"])

def parse_character_tree(c, s):
	for (nid, npoints) in zip(s["nodeIDs"], s["nodePoints"]):
		parse_node(c, nid, npoints)
	print()

def parse_skilltree(db, skilltree):
	at = db.get_abilitytree_by_id(skilltree["treeID"])
	print(at["ability"]["abilityName"])
	for (nid, npoints) in zip(skilltree["nodeIDs"], skilltree["nodePoints"]):
		parse_node(at, nid, npoints)
	print()

def parse_save(path, db):
	with open(path) as fd:
		fd.seek(5) # skip EPOCH magic
		save_json = json.load(fd)

	c = db.classes[save_json["characterClass"]]
	print("Class: " + c["characterClass"]["className"])
	print("Mastery: " + c["characterClass"]["masteries"][save_json["chosenMastery"]]["name"])
	print()

	parse_character_tree(c, save_json["savedCharacterTree"])

	for skilltree in save_json["savedSkillTrees"]:
		parse_skilltree(db, skilltree)

	for item in save_json["savedItems"]:
		parse_item(db, item)


if len(sys.argv) <= 1:
	print("Usage: " + sys.argv[0] + " <save_file_path>")
	sys.exit()

db = Database.Database()
parse_save(sys.argv[1], db)
