#!/usr/bin/env python

import hashlib
import os
import os.path
import re
import yaml

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
def md5_or_unknown(fname):
	if os.path.isfile(fname) and os.access(fname, os.R_OK):
		return md5(fname)
	else:
		return 'unknown'
		
def sanitize_key(key):
	return re.sub(r'[.-]', '_', key)

with open("/compose.yml", 'r') as f:
	try:
		doc = yaml.load(f)
		secrets = doc["secrets"]
		# print(secrets)
		for key, value in secrets.items():
			if 'file' in value:
				file = value['file']
				sanitized_key = sanitize_key(key)
				print("# " + key + " " + file)
				print("SECRET_SUM_" + sanitized_key + '=' + md5_or_unknown(file))
				# print(value['file'])
				# print(md5('/compose.yml'))
			
	except yaml.YAMLError as exc:
		print(exc)