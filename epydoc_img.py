import sys
import os
import re

regexp = re.compile(r"^(\s*)# image:([^:]*):")

for filename in sys.argv[1:]:
	try:
		file = open(filename, 'r')
	except:
		continue

	changed = False
	out = open('tmp', 'w')
	for line in file:
		line = regexp.sub(r'\1<img src="\2" alt="">', line, 1) 
		out.write(line)
	
	out.close()
	os.rename('tmp', filename)

try:
	os.remove('tmp')
except:
	pass

# vim: ts=4 sw=4
