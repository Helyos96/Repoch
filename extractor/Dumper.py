# Generic tools to create JSON data from monobehaviours extracted from Unity assets.
# Depends on a type tree file generated by TypeTreeGenerator.exe (UABE)

# dep: pip install UnityPy

import json
import re
import os
import io
import struct
import traceback
from abc import ABC, abstractmethod
import UnityPy

debug = 0

def get_indent(line):
	ret = 0
	for i in range(0, len(line)):
		if line[i] != ' ':
			break
		ret = ret + 1
	return ret

def align_fd(fd):
	fd.seek((fd.tell() + 3) & ~3)

def get_int(fd):
	return struct.unpack('i', fd.read(4))[0]

def get_float(fd):
	return struct.unpack('f', fd.read(4))[0]

def get_s64(fd):
	return struct.unpack('q', fd.read(8))[0]

def get_u32(fd):
	return struct.unpack('I', fd.read(4))[0]

def get_u16(fd):
	return struct.unpack('H', fd.read(2))[0]

def get_u8(fd):
	return struct.unpack('B', fd.read(1))[0]

def get_char(fd):
	return struct.unpack('c', fd.read(1))[0]

def get_string(fd):
	size = get_int(fd)
	ret = fd.read(size)
	align_fd(fd)
	return ret.decode('UTF-8')

class ExtractorInterface(ABC):
	@abstractmethod
	def dump_mb_python_id(self, objref, file_id : int, path_id : int, pptrs, parse_go = True):
		raise NotImplementedError

class Node:
	# Dump a raw monobehaviour fd as a python object according to the node's hierarchy
	def dump(self, fd, ignore_pptr = False, extractor : ExtractorInterface = None, align = True, pptrs = [], parse_go = True, objref = None, keep_only = []):
		ret = 0
		if debug:
			print(str(hex(fd.tell())) + " : " + self.name + " (" + self.type + ")")

		if self.type == "string":
			ret = get_string(fd)
			if debug:
				print(ret)
		elif len(self.children) == 1 and self.children[0].type == "Array":
			ret = self.children[0].dump(fd, ignore_pptr, extractor, pptrs = pptrs, parse_go = parse_go, objref = objref, keep_only = keep_only)
		elif self.type == "Array":
			ret = []
			size = get_int(fd)
			if debug:
				print("size: " + str(size))
			for i in range(0, size):
				for n in self.children[1:]:
					tmp = n.dump(fd, ignore_pptr, extractor, align=("aligned" in self.flags), pptrs = pptrs, parse_go = parse_go, objref = objref, keep_only = keep_only)
					if tmp != [] and tmp != {}:
						ret.append(tmp)
		elif self.type == "SInt64":
			ret = get_s64(fd)
		elif self.type == "int":
			ret = get_int(fd)
		elif self.type == "UInt16":
			ret = get_u16(fd)
		elif self.type == "UInt8":
			ret = get_u8(fd)
		elif self.type == "char":
			ret = get_char(fd)
		elif self.type == "float":
			ret = get_float(fd)
			if ret.is_integer():
				ret = int(ret)
		elif self.type == "unsigned" and self.name == "int":
			ret = get_u32(fd)
		elif len(self.type) > 7 and self.type[:4] == "PPtr":
			ret = {}
			file_id = get_int(fd)
			path_id = get_s64(fd)
			if extractor and not ignore_pptr and path_id not in pptrs:
				ret = extractor.dump_mb_python_id(objref, file_id, path_id, pptrs + [ path_id ], parse_go = parse_go)
				if ret:
					ret = ret[0]
				else:
					ret = {}
		else: # some unimplemented types might fall in there, be careful
			ret = {}
			for n in self.children:
				tmp = n.dump(fd, ignore_pptr, extractor, pptrs = pptrs, parse_go = parse_go, objref = objref, keep_only = keep_only)
				if keep_only and n.name not in keep_only:
					continue
				if tmp != [] and tmp != {}:
					ret[n.name] = tmp

		if align:
			align_fd(fd)
		return ret

	# Initialize the node from a line in the type tree
	def parse_line(self):
		tmp = self.line[self.indent:]
		tmp = tmp.split()
		if self.indent == 0:
			self.type = "Base"
			self.name = tmp[0]
		else:
			self.type = tmp[0]
			self.name = tmp[1]
			# Flags are usually "array" or "aligned"
			for i in range(2, len(tmp)):
				self.flags.append(tmp[i].replace(',','').replace('(','').replace(')',''))

	def __init__(self, fd):
		self.flags = []
		self.children = []
		self.line = fd.readline()
		self.indent = get_indent(self.line)
		self.parse_line()

		while True:
			restore = fd.tell()
			line = fd.readline()
			if not line:
				break
			fd.seek(restore, os.SEEK_SET)
			if get_indent(line) != self.indent + 1:
				break
			self.children.append(Node(fd))

class Dumper(ExtractorInterface):
	def get_script_classname(self, sid : int):
		if sid in self.scripts:
			return self.scripts[sid]
		return None

	def load_files(self, assetfolder, assetnames):
		print("Loading assets..")
		paths = []
		for f in assetnames:
			paths.append(os.path.join(assetfolder, f))
		print(paths)
		self.env = UnityPy.load(*paths)

	def build_monoscript(self):
		print("Loading scripts..")
		self.scripts = {}
		for obj in self.env.objects:
			if obj.type == "MonoScript":
				data = obj.read()
				self.scripts[obj.path_id] = data.class_name
		print("Loaded " + str(len(self.scripts)) + " scripts")

	def __init__(self, typetreepath, assetfolder, assetnames, seek_override = {}, blacklist = [], whitelist = [], pptr_override = {}):
		print("Loading typetree..")
		self.nodes = []
		with open(typetreepath, 'r') as typetreefd:
			while typetreefd.tell() != os.fstat(typetreefd.fileno()).st_size:
				self.nodes.append(Node(typetreefd))
		self.load_files(assetfolder, assetnames)
		self.build_monoscript()
		self.seek_override = seek_override
		self.blacklist = blacklist
		self.whitelist = whitelist
		self.pptr_override = pptr_override

	def get_basenode(self, name : str):
		for n in self.nodes:
			if n.name == name:
				return n
		return None

	# Dump a raw monobehaviour (fd) as a python object using basename script class
	def dump_mb_python(self, fd, basename, ignore_pptr, pptrs = [], parse_go = True, objref = None, keep_only = []):
		basenode = self.get_basenode(basename)
		if not basenode:
			return None
		return basenode.dump(fd, ignore_pptr, self, pptrs = pptrs, parse_go = parse_go, objref = objref, keep_only = keep_only)

	def dump_obj(self, obj, ignore_pptr = False, ignore_lists = False, pptrs = [], parse_go = True):
		data = obj.read()
		raw = data.get_raw_data()
		fd = io.BytesIO(raw)
		fd.seek(0x14)

		script_id = get_int(fd)
		script_name = self.get_script_classname(script_id)
		if not script_name:
			return None

		keep_only = []
		if not ignore_lists:
			if (self.whitelist and script_name not in self.whitelist) or script_name in self.blacklist:
				return None
		else:
			if script_name in self.pptr_override:
				keep_only = self.pptr_override[script_name]

		fd.seek(0x1C)
		namelen = get_int(fd)
		seekpos = max(0x20, (0x1C + 4 + namelen + 3) & ~3)
		if script_name in self.seek_override:
			seekpos = self.seek_override[script_name]
		fd.seek(seekpos)
		return [ self.dump_mb_python(fd, script_name, ignore_pptr, pptrs = pptrs, parse_go = parse_go, objref = obj, keep_only = keep_only), script_name ]

	# Dump an object (MB or GO) with specific file_id;path_id as a python object
	def dump_mb_python_id(self, objref, file_id : int, path_id : int, pptrs, parse_go = True):
		if path_id == 0:
			return None

		obj = None
		manager = None
		if file_id == 0:
			manager = objref.assets_file
		elif file_id > 0 and file_id - 1 < len(objref.assets_file.externals):
			external_name = objref.assets_file.externals[file_id - 1].name
			parent = objref.assets_file.parent
			if parent is not None:
				if external_name not in parent.files:
					external_name = external_name.upper()
				if external_name in parent.files:
					manager = parent.files[external_name]
			else:
				if external_name not in env.files:
					typ, reader = ImportHelper.check_file_type(external_name)
					if typ == FileType.AssetsFile:
						env.files[external_name] = files.SerializedFile(reader)
				if external_name in env.files:
					manager = env.files[external_name]

		if manager and path_id in manager.objects:
			obj = manager.objects[path_id]
		else:
			return None

		if obj.type == "MonoBehaviour":
			try:
				ret = self.dump_obj(obj, ignore_lists = True, pptrs = pptrs, parse_go = parse_go)
				if not ret:
					return None
				return ret
			except:
				traceback.print_exc()
				return None
		elif parse_go and obj.type == "GameObject":
			data = obj.read()
			ret = {}
			for (i, p) in zip(range(0, 1000), data.components):
				if p.path_id in pptrs:
					continue
				try:
					tmp = self.dump_mb_python_id(p, p.file_id, p.path_id, pptrs + [ p.path_id ], parse_go = False)
					if tmp and tmp[1] not in self.blacklist:
						ret[tmp[1]] = tmp[0]
				except:
					traceback.print_exc()
					continue
			return [ret, "dummy"]
		return None

	def dump_all_json(self, outputfolder, ignore_pptr = True):
		for obj in self.env.objects:
			if obj.type == "MonoBehaviour":
				try:
					d = self.dump_obj(obj, ignore_pptr)
					if not d:
						continue
				except:
					print("Failed generating " + str(obj.path_id))
					traceback.print_exc()
					continue

				if not os.path.isdir(os.path.join(outputfolder, d[1])):
					os.mkdir(os.path.join(outputfolder, d[1]))
				jsonpath = os.path.join(outputfolder, d[1], d[1] + "-" + str(obj.path_id) + ".json")
				with open(jsonpath, 'w', encoding='utf8') as json_file:
					json.dump(d[0], json_file, sort_keys=True, indent='\t', ensure_ascii=False)