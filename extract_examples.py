import os

start_sig = "# file:"
end_sig   = "# eof"

file = None
for line in open('gui.py'):
	if file == None:
		idx = line.find(start_sig)
		if idx > 0:
			filename	= line[idx+len(start_sig):].strip()
			indent		= len(line) - len(line.lstrip())
			file		= open(filename, 'w')
			print filename
	else:
		idx = line.find(end_sig)
		if idx > 0:
			file.close()
			file = None
		else:
			file.write(line[indent:].rstrip()+os.linesep)

# vim: ts=4 sw=4
