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
from enum import IntEnum

with open("Data/Affixes.json", encoding='utf-8') as fd:
	affixes = json.load(fd)
with open("Data/Items.json", encoding='utf-8') as fd:
	items = json.load(fd)
with open("Data/Properties.json", encoding='utf-8') as fd:
	properties = json.load(fd)
with open("Data/PlayerProperties.json", encoding='utf-8') as fd:
	player_properties = json.load(fd)
with open("Data/Uniques.json", encoding='utf-8') as fd:
	uniques = json.load(fd)

classes = {}
for entry in os.scandir("Data/ClassTrees"):
	with open(entry, encoding='utf-8') as fd:
		tmp = json.load(fd)
		classes[tmp["characterClass"]["classID"]] = tmp

ability_trees = []
for entry in os.scandir("Data/AbilityTrees"):
	with open(entry, encoding='utf-8') as fd:
		tmp = json.load(fd)
		ability_trees.append(tmp)

# Affix["modifierType"] ; Affix["affixProperties"]["modifierType"] ; Properties["altTextOverrides"]["modType"]
class ModType(IntEnum):
	FLAT = 0
	INC = 1
	MORE = 2

def get_unique(id : int):
	for u in uniques["uniques"]:
		if u["uniqueID"] == id:
			return u
	print("Couldn't find unique " + str(id))
	return None

def get_property(id : int, tags : int = 0):
	if id == 98:
		return player_properties["list"][tags]
	for p in properties["propertyInfoList"]:
		if p["property"] == id:
			return p
	return None

def get_affix_property(pid : int, tags : int):
	for affix in affixes["singleAffixes"]:
		if affix["property"] == pid and affix["tags"] == tags:
			return affix
	for affix in affixes["multiAffixes"]:
		for ap in affix["affixProperties"]:
			if ap["property"] == pid and ap["tags"] == tags:
				return affix
	return None

def get_affix(id : int):
	for affix in (affixes["singleAffixes"] + affixes["multiAffixes"]):
		if affix["affixId"] == id:
			return affix
	print("Couldn't find affix " + str(id))
	return None

def get_item_basetype(id : int):
	for base in (items["EquippableItems"] + items["nonEquippableItems"]):
		if base["baseTypeID"] == id:
			return base
	print("Couldn't find basetype " + str(id))
	return None

def get_item_subtype(base, sub_id : int):
	for sub in base["subItems"]:
		if sub["subTypeID"] == sub_id:
			return sub
	print("Couldn't find subtype" + sub_id + " (base " + base["baseTypeID"])
	return None

def get_node(nodelist, nid : int):
	for n in nodelist:
		if n["id"] == nid:
			return n
	return None

def get_abilitytree_by_id(id : str):
	for at in ability_trees:
		if at["ability"]["playerAbilityID"] == id:
			return at
	return None

def print_mod(p, type, min, max, roll : int, modifier : float, display : str):
	final = (min + ((max - min) * (roll / 255))) * modifier

	reduced = 0
	if final < 0:
		final = -final
		reduced = 1

	if not (p and p["dontDisplayPlus"] == 1) and type == ModType.FLAT:
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

	if type == ModType.INC:
		if reduced:
			print(" reduced", end='')
		else:
			print (" increased", end='')
	elif type == ModType.MORE:
		if reduced:
			print(" less", end='')
		else:
			print (" more", end='')

	if p and p["displayAsPercentageOf"]:
		print(" of", end='')
	elif p and p["displayAsAddedTo"]:
		print(" to", end='')

	print(' ' + display)

def parse_mod_implicit(imp, roll : int):
	mod = get_affix_property(imp["property"], imp["tags"])
	p = get_property(imp["property"], imp["tags"])
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

def parse_mod_unique(m, roll : int):
	if m["hideInTooltip"]:
		return

	mod = get_affix_property(m["property"], m["tags"])
	p = get_property(m["property"], m["tags"])
	if not p:
		return

	display = p["propertyName"]
	type = ModType.FLAT
	if mod:
		display = mod["affixDisplayName"]
		type = mod["modifierType"]

	min = m["value"]
	max = m["maxValue"]
	print_mod(p, type, min, max, roll, 1, display)

def parse_mod(data : int, affix_id : int, roll : int, modifier : float):
	mod = get_affix(affix_id + 256*(data & 0x0F))
	tier = (data & 0xF0) >> 4
	modifier = modifier - mod["standardAffixEffectModifier"]
	props = []
	if "property" in mod:
		props.append(get_property(mod["property"], mod["tags"]))
	else:
		for ap in mod["affixProperties"]:
			props.append(get_property(ap["property"], ap["tags"]))

	if tier >= len(mod["tiers"]):
		tier = len(mod["tiers"]) - 1
	for (i, p) in zip(range(0, 8), props):
		type = ModType.FLAT
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

def parse_unique(item, basetype, subtype, d):
	u = get_unique(d[8])
	print(u["name"])
	print(basetype["displayName"])
	if not subtype["displayName"]:
		print(subtype["name"])
	else:
		print(subtype["displayName"])

	for (i, m) in zip(range(9, 17), u["mods"]):
		parse_mod_unique(m, d[i])

	for td in u["tooltipDescriptions"]:
		print(td["description"])

	print()

def parse_item(item):
	# skip inventory and buyback
	if item["containerID"] in [1, 32]:
		return

	d = item["data"]
	basetype = get_item_basetype(d[1])
	if not basetype:
		return
	subtype = get_item_subtype(basetype, d[2])
	if not subtype:
		return

	if len(d) >= 4 and d[3] == 7: # unique
		parse_unique(item, basetype, subtype, d)
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
			parse_mod_implicit(imp, d[i])

	# explicits
	print("------------")
	for i in range(0, d[8]):
		parse_mod(d[9 + i*3], d[10 + i*3], d[11 + i*3], 1 + basetype["affixEffectModifier"])

	print()

def parse_node(root, nid : int, npoints : int):
	node = get_node(root["nodeList"], nid)
	print("------------")
	print(node["nodeName"] + " " + str(npoints) + "/" + str(node["maxPoints"]))
	for s in node["stats"]:
		if s["value"]:
			print(s["value"] + " ", end='')
		print(s["statName"])

def parse_character_tree(c, s):
	for (nid, npoints) in zip(s["nodeIDs"], s["nodePoints"]):
		parse_node(c, nid, npoints)
	print()

def parse_skilltree(skilltree):
	at = get_abilitytree_by_id(skilltree["treeID"])
	print(at["ability"]["abilityName"])
	for (nid, npoints) in zip(skilltree["nodeIDs"], skilltree["nodePoints"]):
		parse_node(at, nid, npoints)
	print()

def parse_save(path):
	with open(path) as fd:
		fd.seek(5) # skip EPOCH magic
		save_json = json.load(fd)

	c = classes[save_json["characterClass"]]
	print("Class: " + c["characterClass"]["className"])
	print("Mastery: " + c["characterClass"]["masteries"][save_json["chosenMastery"]]["name"])
	print()

	parse_character_tree(c, save_json["savedCharacterTree"])

	for skilltree in save_json["savedSkillTrees"]:
		parse_skilltree(skilltree)

	for item in save_json["savedItems"]:
		parse_item(item)


if len(sys.argv) <= 1:
	print("Usage: " + sys.argv[0] + " <save_file_path>")
	sys.exit()

parse_save(sys.argv[1])
