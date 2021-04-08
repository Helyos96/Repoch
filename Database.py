import json
import os
from enum import IntEnum, auto

class ModType(IntEnum):
	Added = 0
	Increased = auto()
	More = auto()
	Quotient = auto()

class ModTags(IntEnum):
	Undefined = 0,
	Physical = 1,
	Lightning = 2,
	Cold = 4,
	Fire = 8,
	Void = 16,
	Necrotic = 32,
	Poison = 64,
	Elemental = 128,
	Spell = 256,
	Melee = 512,
	Throwing = 1024,
	Bow = 2048,
	DoT = 4096,
	Minion = 8192,
	Totem = 16384,
	PetResisted = 32768,
	Potion = 65536,
	Buff = 131072,
	Channelling = 262144,
	Transform = 524288,
	LowLife = 1048576,
	HighLife = 2097152,
	FullLife = 4194304,
	Hit = 8388608,
	Curse = 16777216,

class Container(IntEnum):
	Undefined = 0
	Inventory = auto()
	Eq_Helmet = auto()
	Eq_Armor = auto()
	Eq_Weapon = auto()
	Eq_Offhand = auto()
	Eq_Gloves = auto()
	Eq_Belt = auto()
	Eq_Boots = auto()
	Eq_Rightring = auto()
	Eq_Leftring = auto()
	Eq_Amulet = auto()
	Eq_Relic = auto()
	Ma_Shattering = auto()
	Ma_Refinement = auto()
	Ma_Removal = auto()
	Ma_Cleansing = auto()
	Ma_Guardian = auto()
	Ma_Stability = auto()
	Cursor = auto()
	Swap_Buffer = auto()
	Stash = auto()
	Shop = auto()
	Crafting_Main = auto()
	Crafting_Modifier = auto()
	Crafting_Support = auto()
	Gambling = auto()
	Ma_Shaping = auto()
	Arena_Key = auto()
	Idols = auto()
	Legacy_Equipment_Redirect = auto()
	Legacy_Materials_Redirect = auto()
	Shop_Buyback = auto()
	Blessing_0 = auto()
	Blessing_1 = auto()
	Blessing_2 = auto()
	Blessing_3 = auto()
	Blessing_4 = auto()
	Blessing_5 = auto()
	Blessing_6 = auto()
	Blessing_Option_1 = auto()
	Blessing_Option_2 = auto()
	Blessing_Option_3 = auto()
	Blessing_7 = auto()
	Blessing_8 = auto()
	Blessing_9 = auto()

class Database:
	def __init__(self):
		with open("Data/Affixes.json", encoding='utf-8') as fd:
			self.affixes = json.load(fd)
		with open("Data/Items.json", encoding='utf-8') as fd:
			self.items = json.load(fd)
		with open("Data/Properties.json", encoding='utf-8') as fd:
			self.properties = json.load(fd)
		with open("Data/PlayerProperties.json", encoding='utf-8') as fd:
			self.player_properties = json.load(fd)
		with open("Data/Uniques.json", encoding='utf-8') as fd:
			self.uniques = json.load(fd)

		self.classes = {}
		for entry in os.scandir("Data/ClassTrees"):
			with open(entry, encoding='utf-8') as fd:
				tmp = json.load(fd)
				self.classes[tmp["characterClass"]["classID"]] = tmp

		self.ability_trees = []
		for entry in os.scandir("Data/AbilityTrees"):
			with open(entry, encoding='utf-8') as fd:
				tmp = json.load(fd)
				self.ability_trees.append(tmp)

	def get_unique(self, id : int):
		for u in self.uniques["uniques"]:
			if u["uniqueID"] == id:
				return u
		print("Couldn't find unique " + str(id))
		return None

	def get_property(self, id : int, tags : int = 0):
		if id == 98:
			return self.player_properties["list"][tags]
		for p in self.properties["propertyInfoList"]:
			if p["property"] == id:
				return p
		return None

	def get_affix_property(self, pid : int, tags : int):
		for affix in self.affixes["singleAffixes"]:
			if affix["property"] == pid and affix["tags"] == tags:
				return affix
		for affix in self.affixes["multiAffixes"]:
			for ap in affix["affixProperties"]:
				if ap["property"] == pid and ap["tags"] == tags:
					return affix
		return None

	def get_affix(self, id : int):
		for affix in (self.affixes["singleAffixes"] + self.affixes["multiAffixes"]):
			if affix["affixId"] == id:
				return affix
		print("Couldn't find affix " + str(id))
		return None

	def get_item_basetype(self, id : int):
		for base in (self.items["EquippableItems"] + self.items["nonEquippableItems"]):
			if base["baseTypeID"] == id:
				return base
		print("Couldn't find basetype " + str(id))
		return None

	def get_abilitytree_by_id(self, id : str):
		for at in self.ability_trees:
			if at["ability"]["playerAbilityID"] == id:
				return at
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