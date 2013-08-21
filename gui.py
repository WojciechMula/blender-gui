"""
GUI manager for Blender.

$Revision: 1.1.1.1 $

Introduction
============

	The built-in module C{Blender.Draw} gives access to basic GUI elements like
	buttons, sliders etc, it also manages user input. But programming interface
	is function-orientated and thus slightly primitive. Programmer have to write
	a lot of code, mostly redundant; the code is large, entangled, hard to read,
	extend, and maintain.

	I've decided to write an object orientated programming interface, that works
	at higher level of abstraction and makes almost all common actions. It is
	easy to use and understand, even for non-programmers.

	I hope that module will be useful for Blender users.

Installation
============

	Since gui is an external module, you have to tell python the path
	where C{gui.py} is placed. There are three ways to do this:

		1. Add the path to the environment variable PYTHONPATH.
		2. Copy the file (or do symlink) to any directory listed in
		   existing PYTHONPATH.
		3. Add the path inside a script::

			import sys
			sys.path.append('path')

			import gui
			# ...

Basic concepts
==============

	This section introduces basic concepts used in this documentation.

	L{Interface}
	------------

	Interface is a main object that manages events, widgets and containers.
	You have to create a B{single} object of the type L{Interface}.

	Example::

		import Blender
		import gui
		interface = gui.Interface('name-of-script') # script name is optional

		# create widgets and containers
		# bind events

		# register containers managed by interface
		interface.register_container( top-level container(s) )

		# run graphical interface
		interface.run()

	Events & Callbacks
	------------------

	Events are signals emitted by Blender as reaction for user action such as
	pressing a key, pressing mouse button, moving mouse, etc. Programmer can
	catch the signal and do adequate action. Method L{Interface.bind} registers
	a function, that is called on particular event(s).

	Currently there is a one default binding: pressing Q key causes exit.

	Widgets could also emit events, but in this case the only way to bind
	user function with widget event is to supply C{callback} argument on
	construction a widget. Callback function must fit certain conditions
	layed on by the widget.

	Containers
	----------

	Containers may grouping widget or other containers. At the moment
	there are two kinds of containers:

		1. Widget manager, that calculates size & position
		   of children widgets:

			- L{SingleWidget}
			- L{Rows}
			- L{Grid}

		2. Container manager, that manages size and position
		   of children containers:

		    - L{Tabs}
		    - L{Panels}

	Widget
	------

	Widgets are a low-level part of GUI, widgets are for example buttons,
	switches, sliders etc. User may bulid his own widgets if it is neccesary.

	Several widgets are defined:

		- L{Button} (push button)
		- L{Toggle} (switch)
		- L{RadioButtons} (multi-switch)
		- L{Menu} (pulldown menu)
		- L{MultipleToggle} (mutli-switch)
		- L{IntNumber}, L{FloatNumber} (number input)
		- L{IntSlider}, L{FloatSlider} (number input)
		- L{String} (text input)
		- L{Text} (single line of static text)
		- L{LargeText} (block of static text)

Examples
========

	There are some examples in the documentation. Examples can be simply
	extracted from the source file (C{gui.py}) with following utility::

		#file: extract_examples.py
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
		# eof

License
=======

	GNU GPL

Documentation
=============

	HTML documentation is done with U{epydoc<http://epydoc.sf.net>}, images
	were added with my own script.

Author
======

	Wojciech Mula <wojciech_mula@poczta.onet.pl>

	Any comments, suggestions and critique are welcome.

"""

try:
	import Blender
	import Blender.Draw
	import Blender.BGL
	import Blender.Window
except ImportError:
	pass

import types

class Interface(object):
	"""
	GUI manager.

	Interface manges containers and events. It draws registered containers
	(L{Interface.register_container}), call events handlers binded with events
	(L{Interface.bind}) and call button events handlers (L{Interface.bind_button_event}).

	Registering containers managed by other container (L{Tabs}, L{Panels})
	isn't needed.

	Pattern::

		import Blender
		import gui

		interface = gui.Interface('name of interface')

		# make widgets and containers, bind events etc.
		# ...

		# register top-level containers
		interface.register_container( containers )

		# run graphical interface
		interface.run()

	Interface object tracks also modifier keys, which states could be easly
	read with following attributes:
		- CapsLock
		- LeftShift
		- RightShift
		- LeftCtrl
		- RightCtrl
		- LeftAlt
		- RightAlt

	Example::

		# file: ex_mod.py
		import Blender
		import gui

		def keyA(event, pressed):
			if pressed:
				mod = []
				if interface.LeftCtrl or interface.RightCtrl: mod.append('Ctrl')
				if interface.LeftAlt  or interface.RightAlt:  mod.append('Alt')
				if mod:
					if interface.LeftShift or interface.RightShift: mod.append('Shift')
					mod.append('A')
					print "-".join(mod)
				else:
					if interface.LeftShift or interface.RightShift:
						print 'A'
					else:
						print 'a'

		interface = gui.Interface('Modifier keys example')
		interface.bind( keyA, Blender.Draw.AKEY )
		interface.run()
		# eof
	"""
	def __init__(self, name=''):
		"""
		@param name: optional name of interface
		@type name: string
		"""
		self.__events_lookup = {}			# list of events handlers
		self.__button_events_lookup = {}	# list of button events handlers
		self.__active_containers = []		# list of active containers
		self.name = str(name)

		for attr in self.__modifiers.itervalues():
			setattr(self, attr, False)

	def __bind_single(self, function, event):
		if event in self.__events_lookup:
			try:
				self.__events_lookup[event].index(function)
			except ValueError:
				self.__events_lookup[event].insert(0, function)
			else:
				pass # function is already registered
		else:
			self.__events_lookup[event] = [function]

	def bind(self, function, event):
		"""
		Adds C{function} to chain of handlers for given event(s).

		C{Function} is placed at front of chain, so last added function is
		executed first when event occur.

		Example::

			# file:ex_EventHandler.py
			import Blender
			import gui

			### Define handlers

			def AKEY(event, val):
				if val: # val == 1
					print "You've pressed key A"
				else: # val == 0
					print "You've released key A"

			def MouseKey(event, val):
				if val:
					what = "pressed"
				else:
					what = "released"

				if event == Blender.Draw.LEFTMOUSE:
					button = "left"
				elif event == Blender.Draw.RIGHTMOUSE:
					button = "right"
				else:
					button = "center"
				print "You've %s %s mouse button." % (what, button)

			# function prints mouse coordinates in
			# Blender screen (global) and script window (local)
			mouse_x, mouse_y = 0,0
			def MouseMove(event, val):
				global mouse_x, mouse_y

				# On mouse move the sequence of events MOUSEX, MOUSEY are generated.
				# Because of it, coordinates are printed only on MOUSEY event.
				if event == Blender.Draw.MOUSEX:
					mouse_x = val
				else: # event == Blender.Draw.MOUSEY:
					mouse_y = val

					win_id   = Blender.Window.GetAreaID()
					win_type = Blender.Window.Types.SCRIPT
					loc_x, loc_y = 0,0
					for info in Blender.Window.GetScreenInfo(type=win_type):
						if info['id'] == win_id: # it is our window!
							xmin, ymin, _, _ = info['vertices']
							loc_x = mouse_x - xmin
							loc_y = mouse_y - ymin
							break

					print "global coords: (%d,%d), local coords: (%d,%d)" % (mouse_x, mouse_y, loc_x, loc_y)

			### Make interface
			interface = gui.Interface('bind example')

			interface.bind(AKEY, Blender.Draw.AKEY)
			interface.bind(MouseKey, [
				Blender.Draw.LEFTMOUSE,
				Blender.Draw.RIGHTMOUSE,
				Blender.Draw.MIDDLEMOUSE])
			interface.bind(MouseMove, [
				Blender.Draw.MOUSEX,
				Blender.Draw.MOUSEY])
			interface.run()
			# eof

		@param event: Event number or list/tuple of them. It should be one of
			constants provided by module Blender.Draw, for example AKEY, WKEY,
			WHEELDOWN, etc.
		@type event: integer

		@param function: Function must accept two arguments.

			First argument is a event number. If a single function handles more
			then one event, the argument can be used to distinguish events.

			Second argument is optional value. Example above shows argument's
			meaning in different contexts.

			If function return None, then next handler in the chain is
			called, otherwise chain processing is breaking. Default bindings
			could be disabled in this way.

			Example::

				# file:ex_EventHandler2.py
				import Blender
				import gui

				print "Press key A, then B, and A once again"
				### Define handlers
				def A1(event, pressed):
					if pressed:
						print "A1 handler called"

				def A2(event, pressed):
					if pressed:
						print "A2 handler called"

				# A3 breaks the handlers chain -- previously binded functions
				# A1 and A2 are not called any more
				def A3(event, pressed):
					if pressed:
						print "A3 handler called"
						return "break"

				def B(event, pressed):
					if pressed:
						interface.bind(A3, Blender.Draw.AKEY)
						interface.unbind(B)

				interface = gui.Interface('bind example (2)')
				interface.bind(A1, Blender.Draw.AKEY)
				interface.bind(A2, Blender.Draw.AKEY)
				interface.bind(B, Blender.Draw.BKEY)
				interface.run()
				# eof
		@type function: callable
		"""
		if type(event) in [types.TupleType, types.ListType]:
			for e in event:
				self.__bind_single(function, e)
		else:
			self.__bind_single(function, event)

	def unbind(self, function):
		"""
		Unregister handler.
		"""

		unregistered = False
		for event in self.__events_lookup:
			try:
				self.__events_lookup[event].remove(function)
				unregistered = True
			except ValueError:
				pass

		return unregistered

	def bind_button_event(self, function, constant=None):
		"""
		Make a new slot for a button event.
		This function should be used only inside L{Widgets<Widget>}; please
		see how L{Widget} subclasses use it.

		@param function: Handler. Function must accept one required argument
		@type function: callable

		@param constant: Value passed to handler. If function handles more
			then one button event then the parameter could be used to
			distinguish events.
		@type constant: any

		@returns: assigned event number
		"""
		id = len(self.__button_events_lookup)+1
		self.__button_events_lookup[id] = (function, constant)
		return id

	__modifiers = {
		Blender.Draw.CAPSLOCKKEY	: 'CapsLock',
		Blender.Draw.LEFTSHIFTKEY	: 'LeftShift',
		Blender.Draw.RIGHTSHIFTKEY	: 'RightShift',
		Blender.Draw.LEFTCTRLKEY	: 'LeftCtrl',
		Blender.Draw.RIGHTCTRLKEY	: 'RightCtrl',
		Blender.Draw.LEFTALTKEY		: 'LeftAlt',
		Blender.Draw.RIGHTALTKEY	: 'RightAlt'
	}

	def __events_process(self, event, value):
		try:
			chain = self.__events_lookup[event]
		except KeyError:
			pass
		else:
			for handler in chain:
				if handler(event, value) != None:
					break

		# track modifiers:
		# Caps, LeftShift, RightShift, LeftCtrl, RightCtrl, LeftAlt, RightAlt
		try:
			setattr(self, self.__modifiers[event], value==True)
		except KeyError:
			pass

	def __button_events_process(self, event):
		try:
			function, extra =self. __button_events_lookup[event]
		except KeyError:
			pass
		else:
			function(extra)

	def __register_single_container(self, container):
		if isinstance(container, Container):
			# do not register container twice
			if container not in self.__active_containers:
				self.__active_containers.append(container)
		else:
			raise TypeError("Container is required")

	def register_container(self, container):
		"""
		Register L{container(s)<Container>}.

		Registered containers are managed by interface object, i.e.
		they are drawn and events emitted by children widgets
		are handled.

		@type container: L{Container} (and subclasses) or list of containers
		"""

		if type(container) in [types.TupleType, types.ListType]:
			for index, c in enumerate(container):
				try:
					self.__register_single_container(c)
				except TypeError:
					raise TypeError("Element %d: container is required." % index)
		else:
			self.__register_single_container(container)

	def unregister_container(self, container):
		"""
		Unregister container.

		@param	container: container to unregister
		@type	container: L{Container}

		@return: True if container was unregistered, False otherwise (probably
			container has never been registered)
		"""
		try:
			self.__active_containers.remove(container)
		except ValueError:
			return False
		else:
			return True

	def __draw(self):
		Blender.BGL.glClearColor(0.6, 0.6, 0.6, 1.0)
		Blender.BGL.glClear(Blender.BGL.GL_COLOR_BUFFER_BIT)
		Blender.BGL.glColor3f(0.0, 0.0, 0.0)
		for container in self.__active_containers:
			container.draw()

	def run(self):
		"""
		Enables GUI processing.

		In most cases this function should be run after constructing all
		containers and widgets. (Of course adding and removing widgets
		or containers while GUI is running is possible.)
		"""

		# default bindings
		def quit(event, value):
			self.exit()

		self.bind(quit, Blender.Draw.QKEY)

		# register main callback functions
		Blender.Draw.Register(self.__draw, self.__events_process, self.__button_events_process)

	def exit(self):
		"""
		Stops GUI processing.
		"""
		Blender.Draw.Exit()

class Container(object):
	"""
	Geometry manager (base, abstract class).

	Container manages layout of other widgets/containers.

	Widget-only containers are:
		- L{SingleWidget} - the simpliest container, that manages single widget
		- L{Rows} - widgets are placed in a rows; single row may be splitted
			horizontally in any way
		- L{Grid} - widgets are placed at cells of grid, and may span several
		    rows or columns.

	Container-only containers are:
		- L{Tabs} - displays single child container, user may change displayed
			container.
		- L{Panels} - displays a column of containers, user may hide/show them
			independently.

	"""
	def __init__(self, interface, left, bottom, width, height):
		"""
		@param interface: parent interface
		@type interface: L{Interface}

		@param left: x coordinate of left lower corner
		@type left: int

		@param bottom: y coordinate of left lower corner
		@type bottom: int

		@param width: width of container
		@type width: (unsigned) int

		@param height: height of container
		@type height: (unsigned) int
		"""
		self.__visible	= True
		self.interface	= interface

		for pos in ['left', 'bottom', 'width', 'height']:
			if not hasattr(self, pos):
				setattr(self, pos, 0)

		self.set_geometry(left, bottom, width, height)

	def set_geometry(self, left, bottom, width, height):
		"""
		Set new dimensions and position of container. If certain argument
		is C{None} then container parameter remains unchanged::

			c = gui.Container(interface, 10, 10, 300, 300)

			# set new position
			c.set_geometry(x,y, None, None)

			# change width
			c.set_geometry(None, None, new_width, None)

		Function returns four booleans, where True value means that
		parameter has changed::

			c = gui.Container(interface, 10, 10, 300, 300)
			left,bottom,width,height = c.get_geometry()

			# change bottom and width
			diff    = c.set_geometry(left, bottom+5, width-1, height)

			print diff # -> (False, True, True, False)

		Subclasses B{must keep} behaviour of this method, so it is a good practice
		to call C{Container.set_geometry} at the begining of overriding method::

			class Other(Container):
				# ...

				def set_geometry(self, left, bottom, width, height):
					diff = Container.set_geometry(self, left, bottom, width, height)

					if diff[3]: # width has changed:
						# recalculate width of children

					return diff

		@param left: x coordinate of left lower corner
		@type left: int or None

		@param bottom: y coordinate of left lower corner
		@type bottom: int or None

		@param width: width of container
		@type width: (unsigned) int or None

		@param height: height of container
		@type height: (unsigned) int or None
		"""

		lc, bc, wc, hc = False, False, False, False

		if left != None:
			nl = int(left)
			lc = (nl != self.left)
			self.left = nl

		if bottom != None:
			nb = int(bottom)
			bc = (nb != self.bottom)
			self.bottom	= nb

		if width != None:
			nw = int(abs(width))
			wc = (nw != self.width)
			self.width	= nw

		if height != None:
			nh = int(abs(height))
			hc = (nh != self.height)
			self.height	= nh

		return (lc, bc, wc, hc)

	def get_geometry(self):
		"""
		Returns container's geometry.

		@return: (left, bottom, width, height)
		"""
		return (self.left, self.bottom, self.width, self.height)

	def show(self, state):
		"""
		Show/hide container and it's children.

		@type state: boolean
		"""
		self.__visible = (state==True)

	def visible(self):
		"""
		Returns visibility of container.

		@return: boolean
		"""
		return self.__visible

	def draw(self):
		"""
		Draw container and it's content (if container is visible).
		"""
		raise RuntimeError('Abstract method called.')

class SingleWidget(Container):
	"""
	Single widget geometry manager (L{Container} subclass).

	Size and position of widget is just the same as container::

		# file:ex_SingleWidget.py
		import Blender
		import gui

		interface = gui.Interface()

		s1 = gui.SingleWidget( interface, gui.Button(interface, 'One'),   0, 0, 50, 30 )
		s2 = gui.SingleWidget( interface, gui.Button(interface, 'Two'),  20,30, 50, 30 )
		s3 = gui.SingleWidget( interface, gui.Button(interface, 'Three'),40,60, 50, 30 )

		interface.register_container( [s1, s2, s3] )
		interface.run()
		# eof

		# image:../img/ex_SingleWidget.png:

	"""
	def __init__(self, interface, widget, left, bottom, width, height):
		"""
		@type interface: L{Interface}

		@type widget: L{Widget}

		@param left: x coordinate of left lower corner
		@type left: int

		@param bottom: y coordinate of left lower corner
		@type bottom: int

		@param width: width of container
		@type width: (unsigned) int

		@param height: height of container
		@type height: (unsigned) int
		"""
		Container.__init__(self, interface, left, bottom, width, height)
		if not isinstance(widget, Widget):
			raise TypeError("Widget expeced, got '%s'" % str(type(widget)))
		self.children = widget

	def draw(self):
		self.children.draw(self.left, self.bottom, self.width, self.height)

class Rows(Container):
	"""
	Row geometry manager (L{Container} subclass).

	The base element of the container is a row of widgets, which is constructed
	with L{Rows.addrow}. Each row may be splitted horizontally in individual
	way.

	Example::

		# file:ex_Rows.py
		import Blender
		import gui

		interface = gui.Interface()

		rows	= gui.Rows(interface, 10, 10, 200, 18, 5)

		def setwidth(width):
			def fun():
				rows.set_geometry(None, None, width, None)
				Blender.Draw.Redraw()
			return fun

		a	= gui.Button(interface, '100px', tooltip='set width', callback=setwidth(100))
		b	= gui.Button(interface, '200px', tooltip='set width', callback=setwidth(200))
		c	= gui.Button(interface, '300px', tooltip='set width', callback=setwidth(300))
		d0	= gui.Button(interface, 'D0')
		d1	= gui.Button(interface, 'D1')
		d2	= gui.Button(interface, 'D2')
		e	= gui.Button(interface, 'E')
		f0	= gui.Button(interface, 'F0')
		f1	= gui.Button(interface, 'F1')

		# all perc_value
		rows.addrow( [ (a,0.2), (b,0.3), (c,0.5)] )
		rows.addvspace("half")

		# equal width
		rows.addrow( [f0, f1], "double" )
		rows.addvspace("half")

		# single widget
		rows.addrow( e, "triple" )
		rows.addvspace("half")

		# width of one widget is automaticly calculated
		rows.addrow( [ (d0,0.2), (d1,0.4), d2 ], "triple" )

		interface.register_container( rows )
		interface.run()
		# eof

		# image:../img/ex_Rows.png:

	"""
	def __init__(self, interface, left, bottom, width, row_height=15, padx=0):
		"""
		Define position and width of container.

		@type interface: L{Interface}

		@param left: x coordinate of left lower corner of grid
		@type left: integer

		@param bottom: x coordinate of left lower corner of grid
		@type bottom: integer

		@param width: width of container
		@type  width:  (unsigned) integer

		@param row_height: base height of B{single} row
		@type  row_height: (unsigned) integer

		@param padx: space inserted between adjacent widgets in a row (in pixels)
		@type padx: integer
		"""
		self.__row_height	= int(abs(row_height))
		self.__rows			= []
		self.__real_height	= 0
		self.__padx			= int(abs(padx))

		Container.__init__(self, interface, left, bottom, width, 0)

	def addrow(self, widgets, height="normal"):
		"""
		Add a single row of widget(s).

		@param widgets:

			It could be:
				1. Single L{Widget} - the widget span whole row.
				2. List of (L{Widgets<Widget>}, perc_width) - percentage width
				   (float value in range 0..1) of the widget. Sum of all
				   C{perc_width} in list must not be grater then 1.0.
				   C{perc_width} B{may be omitted}, and then width of widget
				   is calculated automaticly.

				3. None - simply add a vertical space; see L{addvspace}

		@type widgets: L{Widget}, list of (L{Widgets<Widget>}, width) or None

		@param height:
			Height of row:

				- integer (not less then C{row_height/4})
				- string:

					- "quarter" - C{row_height/4}
					- "half"    - C{row_height/2}
					- "normal"  - C{row_height}
					- "double"  - C{2*row_height}
					- "triple"  - C{3*row_height}
					- "quad"    - C{4*row_height}

			Defaults to "normal".

		@type height: int or string
		"""
		### Parse widgets
		tmp = [] # list of (perc_width, current_width, widget)
		if widgets == None:
			tmp = None
		elif isinstance(widgets, Widget):
			tmp = [(1.0, self.width, widgets)]
		elif type(widgets) in [types.ListType, types.TupleType]:

			# preprocess
			sum_perc_width		= 0.0
			unknown_width_count	= 0
			for index, item in enumerate(widgets):
				if isinstance(item, Widget):
					unknown_width_count += 1
				elif type(item)==types.TupleType:
					if len(item)==2 and isinstance(item[0], Widget) and type(item[1])==types.FloatType:
					 	if item[1] > 1.0 or item[0] < 0.0:
							raise ValueError("Element %d of widget: float value must lie in range 0..1." % index)
						else:
							sum_perc_width += item[1]
					else:
						raise TypeError("Element %d of 'widget': tuple must be (Widget, float)." % index)
				else:
					raise TypeError("Element %d of 'widget' must be a Widget or tuple (Widget, float)." % index)

			if sum_perc_width > 1.0:
				raise ValueError("Sum of perc_width must be less or equal 1.0, but is %f." % sum_perc_width)

			# calculate unknown widths
			available_width = self.width - (len(widgets)-1)*self.__padx
			if unknown_width_count:
				uw = (1.0 - sum_perc_width)/unknown_width_count
				rw = int(uw * available_width)

			# finally build list
			for index, item in enumerate(widgets):
				if isinstance(item, Widget):
					tmp.append( (uw, rw, item) )
				else:
					widget, perc_width = item
					real_width = int(available_width * perc_width)
					tmp.append( (perc_width, real_width, widget) )

		### Get height
		heights = {
			"quarter"	: self.__row_height/4,
			"half"		: self.__row_height/2,
			"normal"	: self.__row_height,
			"double"	: 2*self.__row_height,
			"triple"	: 3*self.__row_height,
			"quad"		: 4*self.__row_height
		}
		if type(height) is types.StringType:
			try:
				height = heights[height]
			except KeyError:
				height = heights["normal"]
		elif type(height) in [types.IntType, types.FloatType]:
			height = max(self.__row_height, int(height))
		else:
			raise TypeError("Height must be integer or string: %s." % height.keys())

		### Add new row
		self.__real_height += height
		self.__rows.insert( 0, (height, tmp) )

		return self

	def addvspace(self, height="normal"):
		"""
		Adds empty row.

		@param height:

			Height of row:

				- integer (not less then C{row_height/4})
				- string:

					- "quarter" - C{row_height/4}
					- "half"    - C{row_height/2}
					- "normal"  - C{row_height}
					- "double"  - C{2*row_height}
					- "triple"  - C{3*row_height}
					- "quad"    - C{4*row_height}

			Defaults to "normal".

		@type height: string
		"""
		return self.addrow(None, height)

	def draw(self):
		curY = self.bottom
		for row in self.__rows:
			if row[1] == None:	# vspace
				curY += row[0]
			else:
				curX = self.left
				height, widgets = row
				for _, real_width, widget in widgets:
					widget.draw(curX, curY, real_width, height)
					curX += real_width + self.__padx

				curY += height

	def set_geometry(self, left, bottom, width, height):
		diff = Container.set_geometry(self, left, bottom, width, height)

		if diff[2]: # width has changed, recalculate width of each widget
			for i, row in enumerate(self.__rows):
				if row[1] == None:
					continue

				available_width = self.width - (len(row[1])-1)*self.__padx
				for j, (perc_width, _, widget) in enumerate(row[1]):
					real_width = int(available_width * perc_width)
					self.__rows[i][1][j] = (perc_width, real_width, widget)

		return diff

	def get_geometry(self):
		return (self.left, self.bottom, self.width, self.__real_height)

class Grid(Container):
	"""
	Grid geometry manager.

	This manager places widgets at grid of rectangular cells, widget can span
	multiple adjacent cells. One cell may be occupied by one widget.

	Example 1 (numeric keyboard)::

		# file: ex_Grid1.py
		import Blender
		import gui

		interface = gui.Interface()
		grid = gui.Grid(interface, 10, 10, 200, 250, 4, 5, padx=4, pady=4)

		grid.add( gui.Button(interface, 'num'), 0, 0)
		grid.add( gui.Button(interface, '/'), 1, 0)
		grid.add( gui.Button(interface, '*'), 2, 0)
		grid.add( gui.Button(interface, '-'), 3, 0)

		grid.add( gui.Button(interface, '7'), 0, 1)
		grid.add( gui.Button(interface, '8'), 1, 1)
		grid.add( gui.Button(interface, '9'), 2, 1)
		grid.add( gui.Button(interface, '+'), 3, 1, rowspan=2)

		grid.add( gui.Button(interface, '4'), 0, 2)
		grid.add( gui.Button(interface, '5'), 1, 2)
		grid.add( gui.Button(interface, '6'), 2, 2)

		grid.add( gui.Button(interface, '1'), 0, 3)
		grid.add( gui.Button(interface, '2'), 1, 3)
		grid.add( gui.Button(interface, '3'), 2, 3)
		grid.add( gui.Button(interface, 'Ret'), 3, 3, rowspan=2)

		grid.add( gui.Button(interface, '0'), 0, 4, colspan=2)
		grid.add( gui.Button(interface, '.'), 2, 4)

		interface.register_container(grid)
		interface.run()
		# eof

		# image:../img/ex_Grid1.png:

	Example 2::

		# file: ex_Grid2.py
		import Blender
		import gui

		interface = gui.Interface()

		grid = gui.Grid(interface, 10, 10, 300, 300, [0.1, 0.2, '*'], [0.1,'*',0.1,0.3])
		for row in xrange(4):
			for col in xrange(3):
				grid.add( gui.Button(interface, "(%d,%d)" % (col,row) ), col, row)

		interface.register_container(grid)
		interface.run()
		# eof

		# image:../img/ex_Grid2.png:

	Example 3::

		# file: ex_Grid3.py
		import Blender
		import gui

		interface = gui.Interface()

		grid = gui.Grid(interface, 10, 10, 200, 200, [0.2,'*',0.2], [0.2,'*',0.2])

		grid.add( gui.Button(interface, 'A'), 0, 0, colspan=2)
		grid.add( gui.Button(interface, 'B'), 0, 1, rowspan=2)
		grid.add( gui.Button(interface, 'C'), 1, 2, colspan=2)
		grid.add( gui.Button(interface, 'D'), 2, 0, rowspan=2)

		grid.add( gui.Button(interface, 'X'), 1, 1)

		interface.register_container(grid)
		interface.run()
		# eof

		# image:../img/ex_Grid3.png:

	"""
	def __init__(self, interface, left, bottom, width, height, cols, rows, padx=5, pady=5):
		"""
		Define layout of grid.

		@type    interface: L{Interface}

		@param   left: x coordinate of left lower corner of grid
		@type    left: integer

		@param bottom: x coordinate of left lower corner of grid
		@type  bottom: integer

		@param  width: width of container
		@type   width: (unsigned) integer

		@param height: height of container
		@type  height: (unsigned )integer

		@param cols: columns description

			1. If type of C{cols} is integer, then grid has C{cols} columns
			   and width of all columns is just the same.

			2. If type of C{cols} is list, then grid has C{len(cols)} columns.
			   Each element of the list defines width of a column; type of
			   the element could be float or string:

				- B{float} - value must lie in range 0..1 and width is
				  calculated as C{I{float}*container_width}.

				  Sum of all float values B{must be} less or equal then 1.0.

				- B{string} - only string "*" is accepted and means
				  "any value". Width of all columns marked by asterisk
				  is same and is calculated as::

					width = (1.0 - sum(float_values))/number_of_asterisks

		@type cols: integer or list of floats/'*'

		@param rows: rows description; see description for C{cols} parameter
		@type rows: integer or list of floats

		@param padx: x padding (margin left, margin right) of cell in pixels
		@type padx: integer

		@param pady: y padding (margin top, margin bottom) of cell in pixels

		@type pady: integer
		"""

		def preprocess_layout_def(length):
			if type(length) == types.IntType:
				length = abs(length)
				return [ 1.0/length ] * length

			elif type(length) in [types.ListType, types.TupleType]:
				list    	= length
				n			= list.count('*') # asterisks count
				float_sum	= 0.0
				for index, item in enumerate(list):
					if type(item) == types.FloatType:
						if 0.0 <= item <= 1.0:
							float_sum += item
						else:
							ValueError('Element %d: float value must lie in range 0..1.' % index)
					elif item != '*':
						TypeError("Element %d: float or string '*' required." % index)

				if float_sum > 1.0:
					raise ValueError('Sum of float values is %f, but must be less or equal 1.0.' % fsum)

				if n > 0: # there are some asterisks
					width	= (1.0 - float_sum)/n
					result	= []
					for item in list:
						if item == '*':
							result.append(width)
						else:
							result.append(item)
					return result

				return list

		self.__rows_def	= preprocess_layout_def(rows)
		self.__cols_def	= preprocess_layout_def(cols)
		self.__map		= [[False for _ in xrange(len(self.__cols_def))]
							for _ in xrange(len(self.__rows_def))]
		self.__children	= []

		self.padx	= abs(int(padx))
		self.pady	= abs(int(pady))

		Container.__init__(self, interface, left, bottom, width, height)
		#self.set_geometry(left, bottom, width, height)

	def __calc_real_geometry(self, pleft, pbottom, pwidth, pheight):
		"""
		Calculate real geometry for given percentage values.

		@param pleft: x coordinate for left-bottom corner
		@type pleft: float (in range 0..1)

		@param pbottom: y coordinate for left-bottom corner
		@type pbottom: float (in range 0..1)

		@param pwidth: width
		@type pwidth: float (in range 0..1)

		@param pheight: height
		@type pheight: float (in range 0..1)
		"""
		width	= pwidth  * self.width
		height	= pheight * self.height

		left	= self.left   + pleft*self.width
		bottom	= self.bottom + (1.0-pbottom)*self.height - height

		return map(int, (left+self.padx, bottom+self.pady, width-self.padx, height-self.pady))

	def set_geometry(self, left, bottom, width, height):
		diff = Container.set_geometry(self, left, bottom, width, height)

		if reduce(lambda a,b: a or b, diff, False): # pos and/or dimensions changed
			for index, (formula, _, widget) in enumerate(self.__children):
				dimensions = self.__calc_real_geometry( *formula )
				self.__children[index] = (formula, dimensions, widget)

		return diff

	def add(self, widget, col, row, colspan=1, rowspan=1):
		"""
		Place C{widget} on the grid.

			- C{col} & C{row} - cell number; cell (0,0) is placed at
				upper-left corner of grid
			- C{colspan} & C{rowspan} - width and height in cells
				(default 1x1)

		ValueError is raised if:
			- coordinates/dimensions points out of the grid,
			- one or more cell are already occupied by other widget.

		@param col: starting column
		@type col: integer

		@param row: starting row
		@type row: integer

		@param colspan: number of columns occupied by widget
		@type colspan: integer

		@param rowspan: number of rows occupied by widget
		@type rowspan: integer
		"""
		if not isinstance(widget, Widget):
			raise TypeError("Widget expeced, you've passed '%s'" % str(type(widget)))

		if row < 0 or row >= len(self.__rows_def):
			raise ValueError("Starting row outside the grid.")

		if col < 0 or col >= len(self.__cols_def):
			raise ValueError("Starting colum outside the grid.")

		if row+rowspan-1 >= len(self.__rows_def):
			raise ValueError("Too much rows.")

		if col+colspan-1 >= len(self.__cols_def):
			raise ValueError("Too much colums.")

		for i in xrange(row, row+rowspan):
			for j in xrange(col, col+colspan):
				if self.__map[i][j]:
					raise ValueError("Some cells of grid are occupied by other widget.")

		for i in xrange(row, row+rowspan):
			for j in xrange(col, col+colspan):
				self.__map[i][j] = True

		pattern = (
			sum(self.__cols_def[:col]),
			sum(self.__rows_def[:row]),
			sum(self.__cols_def[col:col+colspan]),
			sum(self.__rows_def[row:row+rowspan])
		)
		geometry = self.__calc_real_geometry( *pattern )
		self.__children.append( (pattern, geometry, widget) )

		return self

	def draw(self):
		if self.visible():
			for _, geometry, widget in self.__children:
				widget.draw( *geometry )

class Widget(object):
	"""
	Widget (base, abstract class)

	Widget is a base class for all widgets.
	"""
	def __init__(self, interface, autoregister=True, callback=None):
		"""
		@param autoregister: if True, then C{self.event} is automaticly registered
		@type autoregister: boolean

		@param callback: function called when widget emit event; some widgets
			(for example L{Text}) do not emit events
		@type callback: callable
		"""
		self.__visible	= True
		self.callback	= callback
		self.interface	= interface

		if autoregister:
			self.eid = self.interface.bind_button_event(self.event)

	def draw(self, x,y, width,height):
		"""
		Draw widget. This method should be called only by container.

		@param x: x coordinate of left bottom corner
		@type x: integer

		@param y: y coordinate of left bottom corner
		@type y: integer

		@type width: integer

		@type height: integer
		"""
		raise RuntimeError("Widget.draw is an abstract method.")

	def event(self, constant):
		"""
		Method handles widget event(s). By default just call callback if one is present.

		@param constant: additional parameter for callback
		@type constant: any
		"""
		if self.callback: self.callback()

	def visible(self):
		"""
		Return visibility of the widget.
		"""
		return self.__visible

	def show(self, state):
		"""
		Set visibility of the widget.
		"""
		self.__visible = (state==True)

class Button(Widget):
	"""
	Push Button (L{Widget} subclass). C{Callback} is called when user press the button.

	Following attributes are defined:
		- B{name} (read/write) - title of button
		- B{tooltip} (read/write) - tooltip

	Example::

		# file: ex_Button.py
		import Blender
		import gui

		# define callbacks
		def hide_me():
			button1.show(False)
			Blender.Draw.Redraw()

		clicks = 0
		def count_click():
			global clicks
			clicks += 1
			button2.name = "Clicked %d time(s)" % clicks

		# make interface
		interface = gui.Interface()

		button1 = gui.Button(interface, 'Hide me!', callback=hide_me)
		button2 = gui.Button(interface, 'This button has no clicked yet.', callback=count_click)
		row = gui.Rows(interface, 10,10, 250, 20)
		row.addrow( [button1, (button2,0.7)] )

		interface.register_container(row)
		interface.run()
		# eof

	"""
	def __init__(self, interface, name, tooltip="", callback=None):
		"""
		Set initial parameters for push button.

		@type  interface: L{Interface}

		@param name: button's name
		@type  name: string

		@type  tooltip: string

		@type  callback: callable
		"""
		Widget.__init__(self, interface, callback=callback)

		self.__setname(name)
		self.__settooltip(tooltip)

	def draw(self, x,y, width,height):
		if self.visible():
			self.blender_obj = Blender.Draw.Button(self.name, self.eid, x,y, width, height, self.tooltip)

	# properties
	def __getname(self):
		return self.__name

	def __setname(self, name):
		self.__name = str(name)
		Blender.Draw.Redraw()

	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	name	= property(__getname, __setname)
	tooltip = property(__gettooltip, __settooltip)

class Toggle(Widget):
	"""
	Toggle Button (L{Widget} sublcass).

	The toggle button has two static states: on and off.

	Following attributes are defined:
		- B{name} (read/write) - title of button
		- B{tooltip} (read/write)
		- B{state} (read/write) - state of button (on=True, off=False)

	Example::

		# file: ex_Toggle.py
		import Blender
		import gui

		# define callback
		def button1_state(state): switch1.name = state and "On" or "Off"
		def button2_state(state): switch2.name = state and "On" or "Off"

		# make interface
		interface = gui.Interface()

		switch1 = gui.Toggle(interface, 'On', True, callback=button1_state)
		switch2 = gui.Toggle(interface, 'On', True, callback=button2_state)

		row = gui.Rows(interface, 10,10, 250, 20)
		row.addrow( [switch1, switch2] )

		interface.register_container(row)
		interface.run()
		# eof
	"""
	def __init__(self, interface, name, onoff, tooltip="", callback=None):
		"""

		@type interface: L{Interface}

		@param name: name of button
		@type name: string

		@param onoff: initial state of switch
		@type onoff: boolean

		@type tooltip: string

		@param callback: callback is called after state change; callback must
			accept single argument: the state
		@type callback: callable
		"""
		Widget.__init__(self, interface, callback=callback)
		self.__setname(name)
		self.__settooltip(tooltip)
		self.__setstate(onoff)

	def draw(self, x,y, width,height):
		if self.visible():
			self.blender_obj = Blender.Draw.Toggle(self.name, self.eid, x,y, width, height, self.state, self.tooltip)

	def event(self, _):
		self.__state = not self.__state
		if self.callback: self.callback(self.__state)

	# properties
	def __getname(self):
		return self.__name

	def __setname(self, name):
		self.__name = str(name)
		Blender.Draw.Redraw()

	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	def __getstate(self):
		return self.__state

	def __setstate(self, state):
		self.__state = (state == True)
		Blender.Draw.Redraw()

	name	= property(__getname, __setname)
	tooltip = property(__gettooltip, __settooltip)
	state	= property(__getstate, __setstate)

class Number(Widget):
	"""
	Number input base, abstract class (L{Widget} subclass).

	Type of number is integer or floating-point, depending on subclass.
	Callback is called on value change.

	Following attributes are defined:
		- B{name} (read/write) - title of input
		- B{tooltip} (read/write)
		- B{value} (read/write) - current value
		- B{min} (read only) - min allowed value
		- B{max} (read only) - max allowed value
	"""
	def __init__(self, interface, name, value, min, max, tooltip="", callback=None):
		"""
		@param name: name of number
		@type name: string

		@param value: inital value
		@type value: float or integer

		@param min: min allowed value
		@type min: float or integer

		@param max: max allowed value
		@type max: float or integer

		@type tooltip: string

		@param callback: function, that accepts one argument of type int or float
		@type callback: callable
		"""
		Widget.__init__(self, interface, callback=callback)

		self._setname(name)
		self._settooltip(tooltip)

		def numeric(x):
			if type(x) in [types.IntType, types.FloatType]:
				return x
			else:
				raise TypeError("Numeric type required, got %s." % str(type(x)))

		self.__value	= numeric(value)
		min, max		= numeric(min), numeric(max)
		if min <= max:
			self.__min, self.__max = min, max
		else:
			self.__min, self.__max = max, min

	def draw(self, x,y, width, height):
		raise RuntimeError("Abstract method called")

	def event(self, _):
		self.value	= self.blender_obj.val
		if self.callback: self.callback(self.value)

	# properties
	def _getname(self):
		return self.__name

	def _setname(self, name):
		self.__name = str(name)
		Blender.Draw.Redraw()

	def _gettooltip(self):
		return self.__tooltip

	def _settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	def _getvalue(self):
		return self.__value

	def _setvalue(self, value):
		if type(value) == type(self.__value):
			self.__value = max(min(value, self.__max), self.__min)
		else:
			raise TypeError("Incompatible types assignment.")

	def _getmin(self): return self.__min
	def _getmax(self): return self.__max

	name	= property(_getname, _setname)
	tooltip = property(_gettooltip, _settooltip)
	value	= property(_getvalue, _setvalue)
	min		= property(_getmin)
	max		= property(_getmax)

class IntNumber(Number):
	"""
	Integer number input (L{Number} subclass).

	Example::

		# file: ex_IntNumber.py
		import Blender
		import gui

		# callbacks
		def width_callback(val):
			cont.set_geometry(None, None, val, None)
			Blender.Draw.Redraw()

		def height_callback(val):
			cont.set_geometry(None, None, None, val)
			Blender.Draw.Redraw()

		# make interface
		interface = gui.Interface()

		# range of width & height is 50..300, initial value 100
		width  = gui.IntNumber(interface, 'Width',  100, 50, 300, callback=width_callback)
		height = gui.IntNumber(interface, 'Height', 100, 50, 300, callback=height_callback)

		# grid: 1 column, 2 rows
		cont = gui.Grid(interface, 10,10, width.value, height.value, 1,2)
		cont.add( width,  0, 0 )
		cont.add( height, 0, 1 )

		interface.register_container(cont)
		interface.run()
		# eof

		# image:../img/ex_IntNumber.png:

	"""
	def __init__(self, interface, name, value, min, max, tooltip="", callback=None):
		"""
		@type interface: L{Interface}

		@param name: name of number
		@type name: string

		@param value: inital value
		@type value: integer

		@param min: min allowed value
		@type min: integer

		@param max: max allowed value
		@type max: integer

		@type tooltip: string

		@type callback: callable
		"""
		Number.__init__(self, interface, name, int(value), int(min), int(max), tooltip, callback)

	def draw(self, x,y, width, height):
		if self.visible():
			self.blender_obj = Blender.Draw.Number(self.name, self.eid, x,y, width, height, self.value, self.min, self.max, self.tooltip)

class FloatNumber(Number):
	"""
	Floating-point number input (L{Number} subclass).
	"""
	def __init__(self, interface, name, value, min, max, tooltip="", callback=None):
		"""
		@type interface: L{Interface}

		@param name: name of number
		@type name: string

		@param value: initial value
		@type value: float

		@param min: min allowed value
		@type min: float

		@param max: max allowed value
		@type max: float

		@type tooltip: string

		@type callback: callable
		"""
		Number.__init__(self, interface, name, float(value), float(min), float(max), tooltip, callback)

	def draw(self, x,y, width, height):
		if self.visible():
			self.blender_obj = Blender.Draw.Number(self.name, self.eid, x,y, width, height, self.value, self.min, self.max, self.tooltip)

class IntSlider(Number):
	"""
	Integer number input (L{Number} subclass).
	"""
	def __init__(self, interface, name, value, min, max, tooltip="", callback=None):
		"""
		@type interface: L{Interface}

		@param name: name of number
		@type name: string

		@param value: initial value
		@type value: integer

		@param min: min allowed value
		@type min: integer

		@param max: max allowed value
		@type max: integer

		@type tooltip: string

		@type callback: callable
		"""
		Number.__init__(self, interface, name, int(value), int(min), int(max), tooltip, callback)

	def draw(self, x,y, width, height):
		if self.visible():
			self.blender_obj = Blender.Draw.Slider(self.name, self.eid, x,y, width, height, self.value, self.min, self.max, 1, self.tooltip)

class FloatSlider(Number):
	"""
	Floating-point number input (L{Number} subclass)
	"""
	def __init__(self, interface, name, value, min, max, tooltip="", callback=None):
		"""
		@type interface: L{Interface}

		@param name: name of number
		@type name: string

		@param value: inital value
		@type value: float

		@param min: min allowed value
		@type min: float

		@param max: max allowed value
		@type max: float

		@type tooltip: string

		@type callback: callable
		"""
		Number.__init__(self, interface, name, float(value), float(min), float(max), tooltip, callback)

	def draw(self, x,y, width, height):
		if self.visible():
			self.blender_obj = Blender.Draw.Slider(self.name, self.eid, x,y, width, height, self.value, self.min, self.max, 1, self.tooltip)

class String(Widget):
	"""
	String input (L{Widget} subclass).

	Following attributes are defined:
		- B{name} (read/write) - title of string
		- B{tooltip} (read/write)
		- B{string} (read/write)

	Example::

		# file: ex_String.py
		import Blender
		import gui
		import string

		# make interface
		interface = gui.Interface()

		A = gui.String(interface, 'to upper: ',  '', 50, callback=string.upper)
		B = gui.String(interface, 'swap case: ', '', 50, callback=string.swapcase)

		cont = gui.Rows(interface, 10,10, 200, 20)
		cont.addrow(A)
		cont.addrow(B)

		interface.register_container(cont)
		interface.run()
		# eof
	"""
	def __init__(self, interface, name, initial, max_length, tooltip="", callback=None):
		"""
		@type interface: L{Interface}

		@param	name: name of string
		@type	name: string

		@param	initial: initial value of string
		@type	initial: string

		@param	max_length: max length of string
		@type	max_length: integer

		@type	tooltip: string

		@param	callback: Function must accept string and return string that
			is saved back.
		@type	callback: callable
		"""
		Widget.__init__(self, interface, callback=callback)

		self.__setname(name)
		self.__settooltip(tooltip)
		self.__setstring(initial)
		self.__max_length = max(int(abs(max_length)), 1)

	def draw(self, x,y, width, height):
		if self.visible():
			self.blender_obj = Blender.Draw.String(self.name, self.eid, x,y, width, height, self.string, self.__max_length, self.tooltip)

	def event(self, _):
		self.string	= self.blender_obj.val

	# properties
	def __getname(self):
		return self.__name

	def __setname(self, name):
		self.__name = str(name)
		Blender.Draw.Redraw()

	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	def __getstring(self):
		return self.__string

	def __setstring(self, string):
		if self.callback:
			self.__string = self.callback(str(string))
		else:
			self.__string = str(string)
		Blender.Draw.Redraw()

	name	= property(__getname, __setname)
	tooltip = property(__gettooltip, __settooltip)
	string	= property(__getstring, __setstring)

class Text(Widget):
	"""
	Static text (L{Widget} subclass).

	Displays single line of a text. Text widget doesn't emit any events.

	Following attributes are defined:
		- B{text}  - displayed text
		- B{align} - horizontal alignment (string):
			- 'left' (default)
			- 'right'
			- 'center'
		- B{fontsize} - size of font (string):
			- 'large' (starting from Blender 3.37)
			- 'normal'
			- 'small'
			- 'tiny'

	Example::

		# file: ex_Text.py
		import Blender
		import gui

		# make interface
		interface = gui.Interface()

		#
		available_fontsize = ['normal', 'small', 'tiny']
		available_align    = ['left', 'center', 'right']

		# grid 3x3
		cont = gui.Grid(interface, 10,10, 300, 80, 3,3)

		for col, size in enumerate(available_fontsize):
			for row, align in enumerate(available_align):
				cont.add( gui.Text(interface, size, fontsize=size, align=align), col, row )

		interface.register_container(cont)
		interface.run()
		# eof

		# image:../img/ex_Text.png:
	"""
	def __init__(self, interface, text, fontsize="normal", align="left"):
		"""
		@type	interface: L{interface}

		@param	text: displayed text
		@type	text: string

		@param	fontsize: size of font
		@type	fontsize: string

		@param	align: horizontal alignment
		@type	align: string
		"""
		Widget.__init__(self, interface, autoregister=False)

		self.__settext(text)
		self.__setfontsize(fontsize)
		self.__setalign(align)

	def draw(self, x,y,width,height):
		if self.__align == 'center':
			x = x + (width - self.__text_width)/2
		elif self.align == 'right':
			x = x + width - self.__text_width
		#else: align=='left' -- do nothing

		Blender.BGL.glRasterPos2d(x,y)
		self.blender_obj = Blender.Draw.Text(self.__text, self.__fontsize)

	# properties
	def __settext(self, text):
		self.__text			= str(text)
		self.__text_width	= Blender.Draw.GetStringWidth(self.__text)
		Blender.Draw.Redraw()

	def __gettext(self):
		return self.__text

	def __setfontsize(self, fontsize):
		if fontsize in ['large', 'normal', 'small', 'tiny']:
			self.__fontsize = fontsize
		else:
			self.__fontsize = 'normal'

	def __getfontsize(self):
		return self.__fontsize

	def __setalign(self, align):
		if align in [ 'left', 'center', 'right']:
			self.__align = align
		else:
			self.__align = 'left'

	def __getalign(self):
		return self.__align

	text		= property(__gettext, __settext)
	fontsize	= property(__getfontsize, __setfontsize)
	align		= property(__getalign, __setalign)


class MultipleSelect(Widget):
	"""
	Multiple select (abstract class, L{Widget} subclass).

	Widget subclasses allows user to select single value from a set of values;
	each value has a title.

	Following common attributes are defined:
		- B{value} (read/write) - currently selected value
		- B{title} (read only) - title of current value
	"""
	def __init__(self, interface, options, default, callback=None):
		"""
		@type 	interface: L{Interface}

		@param	options:

			Definition of states, i.e. values and titles assigned to them;
			C{options} is a mixed list of:

				1. pair C{(title [I{string}], value [I{integer}])}

				2. C{title [I{string}]} - value for this entry is a previous value
					incremented by one.

			Examples::

				['X', 'Y', 'Z'] =
				    = [('X',0), ('Y',1), ('Z',2)]

				[('A',100), 'A1', 'A2', 'A3', ('B',200), 'B0', 'B1', ('C',300)] =
					= [('A',100), ('A1',101), ('A2',102), ('A3',103),
					   ('B',200), ('B0',201), ('B1',202), ('C',300)]

		@type	options: list of (string, integer)/string

		@param	default: initially selected state; if a value does not match any
			defined, then first value from C{options} list is select
		@type	default: integer

		@param	callback: function must accept one argument, filled with state
			value
		"""
		Widget.__init__(self, interface, autoregister=False, callback=callback)

		# parse options
		self.__available_values = []
		self.__titles = []

		value = -1
		for index, item in enumerate(options):
			if type(item) == types.StringType:
				value += 1
				self.__available_values.append(value)
				self.__titles.append(item)
			elif type(item) == types.TupleType and len(item) == 2:
				if type(item[0]) == types.StringType and type(item[1]) == types.IntType:
					self.__available_values.append(item[1])
					self.__titles.append(item[0])
					value = item[1]
				else:
					raise TypeError("Element %d: string or tuple (string, integer) is required." % index)
			else:
				raise TypeError("Element %d: string or tuple (string, integer) is required." % index)

		if len(self.__available_values) == 0:
			raise ValueError('Empty list of options passed.')

		# select initial value
		self.__selected	= 0
		self.value		= default

	def _getselected(self):
		return self.__selected

	def _setselected(self, idx):
		if 0 <= idx < len(self.__available_values):
			self.__selected = idx
		else:
			self.__selected = 0

	def _iteroveroptions(self):
		for index in xrange(len(self.__available_values)):
			yield index, self.__titles[index], self.__available_values[index]

	def _gettitle(self, idx):
		return self.__titles[idx]

	# properties
	def __getvalue(self):
		return self.__available_values[self.__selected]

	def __setvalue(self, value):
		try:
			idx = self.__available_values.index(value)
		except ValueError:
			idx = 0

		if idx != self.__selected:
			self.__selected	= idx
			Blender.Draw.Redraw()

	def __gettitle(self):
		return self.__titles[self.__selected]

	value	= property(__getvalue, __setvalue)
	title	= property(__gettitle)

class RadioButtons(MultipleSelect):
	"""
	Radio buttons (L{MultipleSelect} subclass). User selects value by switching
	one toggle button from a set.

	Following attributes are defined:
		- B{cols} (read/write) - number of columns
		- B{tooltip} (read/write)

	Example::

		# file: ex_RadioButtons.py
		import Blender
		import gui

		# define callback that sets num of cols in radiobutton
		def change_cols(val):
			radiobuttons.cols = val

		# make interface
		interface = gui.Interface()

		opt 			= map(str, xrange(1,16))
		radiobuttons	= gui.RadioButtons(interface, opt, 0)
		cols			= gui.IntSlider(interface, 'Columns:', len(opt), 1, len(opt), callback=change_cols)

		cont = gui.Rows(interface, 10,10, 300, 20)
		cont.addrow( radiobuttons, 200 )
		cont.addvspace( "quarter" )
		cont.addrow( cols )

		interface.register_container(cont)
		interface.run()
		# eof

		# image:../img/ex_RadioButtons.gif:
	"""
	def __init__(self, interface, options, default, cols=None, tooltip="", callback=None):
		"""
		Initializes the widget.

		See L{MultipleToggle.__init__} for description of other parameters.

		@param	cols:
			Defines how many buttons are in a single row:
				- C{cols==None} - single row of buttons
				- C{cols==len(options)} - single columns of buttons
				- C{1 < cols < len(options)} - other configurations

		@type	cols: integer
		"""
		MultipleSelect.__init__(self, interface, options, default, callback=callback)

		self.__max_cols		= len(options)
		self.__eids			= [None]*len(options)
		self.__blender_objs	= [None]*len(options)
		self.__setcols(cols)
		self.__settooltip(tooltip)

		for index in xrange(self.__max_cols):
			self.__eids[index] = self.interface.bind_button_event(self.event, index)

	def draw(self, x,y,width,height):
		if self.__rows == 1:
			dw = width/self.__cols

			selected = self._getselected()
			for index, title, _ in self._iteroveroptions():
				self.__blender_objs[index] = Blender.Draw.Toggle(title, self.__eids[index], x+index*dw,y, dw, height, selected==index, self.__tooltip)

		else:
			dw	= width/self.__cols
			dh	= height/self.__rows

			Y	= y + (self.__rows-1)*dh
			X	= x
			i	= 0
			selected = self._getselected()
			for index, title, _ in self._iteroveroptions():
				self.__blender_objs[index] = Blender.Draw.Toggle(title, self.__eids[index], X,Y, dw,dh, selected==index, self.__tooltip)
				X += dw
				i += 1
				if i==self.__cols:
					Y -= dh
					X  = x
					i  = 0

	def event(self, index):
		self._setselected(index)
		Blender.Draw.Redraw()
		if self.callback: self.callback(index)

	# properties
	def __setcols(self, cols):
		if cols == None: cols = 0

		cols = int(abs(cols))
		if 0 < cols <= self.__max_cols:
			self.__cols = cols
			self.__rows = (self.__max_cols + self.__cols - 1)/self.__cols
		else:
			self.__cols = self.__max_cols
			self.__rows	= 1
		Blender.Draw.Redraw()

	def __getcols(self):
		return self.__cols

	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	tooltip	= property(__gettooltip, __settooltip)
	cols	= property(__getcols, __setcols)

class MultipleToggle(MultipleSelect):
	"""
	Multiple toggle (L{MultipleSelect} subclass).

	There is single push button, pressing it sets next value.

	Following attributes are defined:
		- B{tooltip} (read/write)

	Example::

		# file: ex_MultipleToggle.py
		import Blender
		import gui

		# define callbacks
		def cb1(value):
			lab1.text = "switch1 state is %d" % value

		def cb2(value):
			lab2.text = "switch2 state is %d" % value

		# make interface
		interface = gui.Interface()

		lab1 = gui.Text(interface, '', align="right")
		lab2 = gui.Text(interface, '', align="right")

		opt1 = ['X', 'Y', 'Z']
		opt2 = [('A',100), 'A1', 'A2', 'A3', ('B',200), 'B0', 'B1', ('C',300)]
		switch1 = gui.MultipleToggle(interface, opt1, 0, callback=cb1)
		switch2 = gui.MultipleToggle(interface, opt2, 0, callback=cb2)

		cont = gui.Rows(interface, 10,10, 300, 20, padx=5)
		cont.addrow( [lab1, switch1] )
		cont.addvspace( "quarter" )
		cont.addrow( [lab2, switch2] )

		interface.register_container(cont)
		interface.run()
		# eof
	"""
	def __init__(self, interface, options, default, tooltip="", callback=None):
		MultipleSelect.__init__(self, interface, options, default, callback=callback)

		self.eid = interface.bind_button_event(self.event)
		self.__settooltip(tooltip)

	def draw(self, x,y, width,height):
		if self.visible():
			self.blender_obj = Blender.Draw.Button(self.title, self.eid, x,y, width, height, self.__tooltip)

	def event(self, _):
		self._setselected( self._getselected()+1 )
		Blender.Draw.Redraw()
		if self.callback: self.callback(self.value)

	# properties
	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	tooltip	= property(__gettooltip, __settooltip)

class Menu(MultipleSelect):
	"""
	Menu (L{MultipleSelect} subclass)

	Allows user to select option from menu. The menu has tilte, and items may
	be grouped i.e, separated by empty row.

	Following attributes are defined:
		- B{menutitle} (read only) - title of menu
		- B{tooltip} (read/write)

	Example::

		# file: ex_Menu.py
		import Blender
		import gui

		# define callback
		def menu_callback(value):
			label.text = "Menu item: %s (value: %d)." % (menu.title, menu.value)

		# make interface
		interface = gui.Interface()

		opt = [
			('A',100), 'A1', 'A2', 'A3',
			'-----', # menu separator is a 3 or more '-'
			('B',200), 'B0', 'B1',
			'------',
			('C',300)
		]

		label = gui.Text(interface, 'Menu example', align="center")
		menu  = gui.Menu(interface, 'ex_Menu.py', opt, 0, callback=menu_callback)

		cont = gui.Rows(interface, 10,10, 300, 20, padx=5)
		cont.addrow( label )
		cont.addvspace( "quarter" )
		cont.addrow( menu )

		interface.register_container(cont)
		interface.run()
		# eof

	"""
	def __init__(self, interface, menutitle, options, default, tooltip="", callback=None):
		MultipleSelect.__init__(self, interface, options, default, callback=callback)
		self.eid = interface.bind_button_event(self.event)

		self.__menutitle = str(menutitle)
		self.__settooltip(tooltip)

		tmp = []
		for index, title, value in self._iteroveroptions():
			if title.startswith('---'):
				tmp.insert(0, "%%l")
			else:
				tmp.insert(0, "%s%%x%d" % (title, value))

		self.__menudef = "%s%%t|%s" % (self.__menutitle, "|".join(tmp))

	def draw(self, x,y, width,height):
		if self.visible():
			self.blender_obj = Blender.Draw.Menu(self.__menudef, self.eid, x,y, width, height, self.value, self.__tooltip)

	def event(self, _):
		self.value = self.blender_obj.val
		if self.callback: self.callback(self.value)

	# properties
	def __getmenutitle(self):
		return self.__menutitle

	def __gettooltip(self):
		return self.__tooltip

	def __settooltip(self, tooltip):
		self.__tooltip = str(tooltip)

	tooltip		= property(__gettooltip, __settooltip)
	menutitle	= property(__getmenutitle)

class Tabs(Container):
	"""
	Container manager (L{Container} subclass)

	The container manages other containers, it display B{single} child container
	at the time. User selects which children is displayed with set of toggle buttons.

	Size of Tabs container is calculated as max dimensions of its children.
	Children widgets are moved to the left-upper corner of the Tabs container.

	Example::

		# file: ex_Tabs.py
		import Blender
		import gui

		# make interface
		interface = gui.Interface()

		# make three grid containers
		grid1 = gui.Grid(interface, 50, 0, 300, 200, 5, 5)
		grid2 = gui.Grid(interface,  0,50, 400, 300, 2, 3)
		grid3 = gui.Grid(interface, 20,50, 300, 150, 4, 6)

		def fill_grid(grid, cols, rows):
			for i in xrange(cols):
				for j in xrange(rows):
					grid.add( gui.Button(interface, "%d,%d" % (i,j)), i, j)

		fill_grid(grid1, 5,5)
		fill_grid(grid2, 2,3)
		fill_grid(grid3, 4,6)

		# pack the container into tab manager
		tabs = gui.Tabs(interface, [(grid1, "5x5"), (grid2, "2x3"), (grid3, "4x6")], 10, 10, 20, 5)

		interface.register_container(tabs)
		interface.run()
		# eof

		# image:../img/ex_Tabs.gif:
	"""
	def __init__(self, interface, containers, x,y, buttons_height, space):

		# preprocess containers list
		self.__containers = []	# list of (container, name)
		width	= 0
		height	= 0
		for index, item in enumerate(containers):
			if isinstance(item, Container):
				interface.unregister_container(item)
				self.__containers.append( (item, "Tab %d" % (index+1)) )
				item.show(False)

				_,_,w,h = item.get_geometry()
				width  = max(w, width)
				height = max(h, height)
				continue
			elif type(item) is types.TupleType and len(item)==2:
				if isinstance(item[0], Container) and type(item[1])==types.StringType:
					interface.unregister_container(item[0])
					self.__containers.append( item )
					item[0].show(False)

					_,_,w,h = item[0].get_geometry()
					width  = max(w, width)
					height = max(h, height)
					continue

			raise TypeError("Element %d: Container or tuple (Container, string) required." % index)

		Container.__init__(self, interface, x,y, width, height)
		self.width  = width
		self.height = height

		self.__buttons_height = max(5, int(abs(buttons_height)))
		self.__space          = max(5, int(abs(space)))
		self.__visible	= 0
		self.__containers[0][0].show(True)
		self.__move_containers()
		self.__switch	= RadioButtons(interface, [c[1] for c in self.__containers], self.__visible, callback=self.event)

	def draw(self):
		if self.visible():
			self.__switch.draw(self.left, self.bottom + self.height + self.__space, self.width, self.__buttons_height)
			self.__containers[self.__visible][0].draw()

	def event(self, index):
		if self.__visible != index:
			self.__containers[self.__visible][0].show(False)
			self.__visible = index
			self.__containers[self.__visible][0].show(True)

	def get_geometry(self):
		return (self.left, self.bottom, self.width, self.height + self.__buttons_height + self.__space)

	def __move_containers(self):
		for container, _ in self.__containers:
			_,_,w,h = container.get_geometry()
			container.set_geometry(self.left, self.bottom + self.height-h, None,None)

	def set_geometry(self, left, bottom, unused1, unused2):
		lc, bc = False, False

		if left != None:
			nl = int(left)
			lc = (nl != self.left)
			self.left = nl

		if bottom != None:
			nb = int(bottom)
			bc = (nb != self.bottom)
			self.bottom = nb

		if lc or bc: self.__move_containers()

		return (lc, bc, False, False)

class Panels(Container):
	"""
	Container manager (L{Container} subclass)

	The container manages other container. It display all container in column,
	and user may hide/show them independently with buttons placed above each
	container.

	Height of Panels depends on children containers. Width depends on blender
	window width, and Paneles forced width of children container to be same.

	If height of Panels container is greater then window's height user may
	scroll down/up the container. Following keyboard binding exists:

		- B{Up arrow}	- scroll up
		- B{Page up}
		- B{Down arrow}	- scroll down
		- B{Page down}

	Additionally B{Ctrl-H} rolls/unrolls all panels.

	Example::

		# file: ex_Panels.py
		import Blender
		import gui

		# define callbacks
		def hleft():
			panels.halign = 'left'

		def hright():
			panels.halign = 'right'

		def vtop():
			panels.valign = 'top'

		def vbottom():
			panels.valign = 'bottom'


		# make interface
		interface = gui.Interface()

		# make 4 grid containers
		ctrl  = gui.Grid(interface,  0, 0, 300, 100, 3, 3)
		grid1 = gui.Grid(interface, 50, 0, 300, 200, 5, 5)
		grid2 = gui.Grid(interface,  0,50, 400, 300, 2, 3)
		grid3 = gui.Grid(interface, 20,50, 300, 150, 4, 6)

		# fill first container with alignment control widgets
		ctrl.add( gui.Button(interface, 'left',   callback=hleft),   0, 1 )
		ctrl.add( gui.Button(interface, 'right',  callback=hright),  2, 1 )
		ctrl.add( gui.Button(interface, 'top',    callback=vtop),    1, 0 )
		ctrl.add( gui.Button(interface, 'bottom', callback=vbottom), 1, 2 )

		# fill rest container with fake buttons
		def fill_grid(grid, cols, rows):
			for i in xrange(cols):
				for j in xrange(rows):
					grid.add( gui.Button(interface, "%d,%d" % (i,j)), i, j)

		fill_grid(grid1, 5,5)
		fill_grid(grid2, 2,3)
		fill_grid(grid3, 4,6)


		# pack the container into tab manager
		panels = gui.Panels(interface, [
			(ctrl, "Panels alignment"),
			(grid1, "5x5"),
			(grid2, "2x3"),
			(grid3, "4x6")],
			"top", "left", 200, 350)

		interface.register_container(panels)
		interface.run()
		# eof
	"""
	def __init__(self, interface, containers, halign, valign, min_width, max_width=None, button_height=20, margin=5):
		"""

		@type	interface: L{Interface}

		@type	containers: list of L{containers<Container>}
			or pair (container, panel name)

		@param	halign: vertical alignment of panels (string):
			- "left"
			- "right"
		@type	halign: string

		@param	valign: vertical alignment of panels (string):
			- "top"
			- "bottom"
		@type	valign: string

		@param	min_width: min width of panels
		@type	min_width: integer

		@param	max_width: max width of panels; if None then C{max_width = min_width}
		@type	max_width: integer

		@param	button_height: height of buttons controlling
			visibility of children containers
		@type	button_height: integer

		@param	margin:
			- vertical space added above and below buttons
			- space beetwen container and blender's window border
		@type	margin: integer
		"""

		# preprocess containers list
		self.__containers = []	# list of (container, name)
		for index, item in enumerate(containers):
			if isinstance(item, Container):
				interface.unregister_container(item)
				self.__containers.append( (item, "Panel %d" % (index+1)) )
				item.show(True)
				continue
			elif type(item) is types.TupleType and len(item)==2:
				if isinstance(item[0], Container) and type(item[1])==types.StringType:
					interface.unregister_container(item[0])
					self.__containers.append( item )
					item[0].show(True)
					continue

			raise TypeError("Element %d: Container or tuple (Container, string) required." % index)

		Container.__init__(self, interface, 0, 0, min_width, 0)

		def scrool_vert(amount):
			def fun(_, val):
				if val:
					self.__adjust_shift(amount)
			return fun

		def hide_show(event, val):
			if val and (self.interface.LeftCtrl or self.interface.RightCtrl):
				any = reduce(lambda a,b: a or b, [s.state for s in self.switches], False)
				if any:
					for s in self.switches:
						s.state = False
				else:
					for s in self.switches:
						s.state = True

				self.__changed(None)

		interface.bind(scrool_vert(+10), Blender.Draw.UPARROWKEY)
		interface.bind(scrool_vert(-10), Blender.Draw.DOWNARROWKEY)

		interface.bind(scrool_vert(+30), Blender.Draw.PAGEUPKEY)
		interface.bind(scrool_vert(-30), Blender.Draw.PAGEDOWNKEY)

		interface.bind(hide_show, Blender.Draw.HKEY)

		self.__margin			= int(abs(margin))
		self.__button_height	= int(abs(button_height))
		self.__winH = 0
		self.__winW = 0
		self.__shift = 0

		self.halign = halign
		self.valign = valign

		self.min_width	= int(abs(min_width))
		if max_width == None:
			self.max_width	= self.min_width
		else:
			self.max_width	= max( self.min_width, int(abs(max_width)) )

		self.switches	= []
		for container, title in self.__containers:
			self.switches.append( Toggle(interface, title, False, callback=self.__changed ) )

		self.__changed(None)

	def __changed(self, _):
		n		= len(self.__containers)
		height	= (2*(n-1))*self.__margin + n*self.__button_height
		for index in xrange(n):
			if self.switches[index].state:
				height += self.__containers[index][0].height

		self.height = height

		Blender.Draw.Redraw()

	def __adjust_shift(self, delta=0):
		if self.__valign == 'top':
			self.top = self.__winH
		else:
			self.top = self.height

		new_shift = self.__shift + delta
		if self.height < self.__winH:
			new_shift = 0
		else:
			if self.__valign == 'top':
				new_shift = min(new_shift, self.height-self.__winH)
				new_shift = max(0, new_shift)
			else: # bottom
				new_shift = max(new_shift, self.__winH-self.height)
				new_shift = min(new_shift, 0)

		if new_shift != self.__shift:
			self.__shift = new_shift
			Blender.Draw.Redraw()

	def __track_window_size(self, recalculate_width=False, recalculate_height=False):
		W, H	= Blender.Window.GetAreaSize()
		width_changed	= recalculate_width
		height_changed	= recalculate_height

		if self.__winH != H:
			self.__winH = H
			height_changed = True

		if self.__winW != W:
			self.__winW = W
			width_changed = True

		if height_changed:
			pass

		if width_changed:
			self.width	= min( self.max_width, min(self.min_width, self.__winW) )
			for container, _ in self.__containers:
				container.set_geometry(None, None, self.width, None)

			if self.__halign == 'left':
				self.left = self.__margin
			else: # right
				self.left = self.__winW - self.width - self.__margin

		return (width_changed, height_changed)

	def draw(self):
		self.__track_window_size()
		self.__adjust_shift()

		curY = self.top + self.__shift - self.__margin

		for index in xrange(len(self.__containers)):

			self.switches[index].draw(self.left, curY - self.__button_height, self.width, self.__button_height)
			curY -= self.__button_height + self.__margin

			if self.switches[index].state:

				container = self.__containers[index][0]
				container.set_geometry(self.left, curY - container.height, None, None)
				container.draw()
				curY -= container.height

	# properties
	def __sethalign(self, halign):
		if halign in ['left', 'right']:
			self.__halign = halign
		else:
			self.__halign = 'left'

		if self.__halign == 'left':
			self.left = self.__margin
		else: # right
			self.left = self.__winW - self.width - self.__margin

		Blender.Draw.Redraw()

	def __gethalign(self):
		return self.__halign

	def __setvalign(self, valign):
		if valign in ['top', 'bottom']:
			self.__valign = valign
		else:
			self.__valign = 'top'
		Blender.Draw.Redraw()

	def __getvalign(self):
		return self.__valign

	halign = property(__gethalign, __sethalign)
	valign = property(__getvalign, __setvalign)

class LargeText(Widget):
	"""
	Display block of text (L{Widget} subclass).

	Text could be aligned left/right/centered and also justify.

	Example::

		# file: ex_LargeText.py
		lorem_ipsum = '''Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
		Curabitur luctus, nulla eget feugiat dapibus, elit justo luctus tellus, ut
		convallis nulla quam ac lectus. Ut pharetra, lectus quis suscipit tristique,
		pede turpis congue pede, vel aliquam urna felis eget quam. Nulla sit amet lacus
		vitae arcu placerat tincidunt. Nam imperdiet nisl id dui. Mauris in quam a
		tortor cursus congue. Integer volutpat. Vestibulum vitae libero nec augue
		sodales dignissim. Ut dui nisl, pulvinar sed, adipiscing ut, adipiscing sit
		amet, eros. Suspendisse gravida mauris id magna. Sed bibendum eros semper diam.
		Fusce semper luctus velit. Cum sociis natoque penatibus et magnis dis
		parturient montes, nascetur ridiculus mus. Aliquam id risus vitae velit viverra
		gravida.'''

		import Blender
		import gui

		# make interface
		interface = gui.Interface()

		def set_width(width):
			textcont.set_geometry(None, None, width, None)

		def set_align(selection):
			align_lookup = {0:'left', 1:'right', 2:'center', 3:'justify'}
			text.align = align_lookup[selection]
			Blender.Draw.Redraw()

		def set_text(selection):
			if selection == 0:
				text.text = lorem_ipsum
			else:
				text.text = lorem_ipsum.replace('\n', ' ')

		text      = gui.LargeText(interface, lorem_ipsum, 16)
		textwidth = gui.IntSlider(interface, 'Width: ', 200, 200, 400, callback=set_width)
		textalign = gui.MultipleToggle(interface, ['left', 'right', 'center', 'justify'], 0, callback=set_align)

		textcont = gui.SingleWidget(interface, text, 10, 40, textwidth.value, 300)
		settings = gui.Rows(interface, 10, 10, 300, 20)
		settings.addrow([(textalign, 0.2), textwidth])
		settings.addrow( gui.RadioButtons(interface, ['raw', 'nl removed'], 0, callback=set_text) )

		interface.register_container( [textcont, settings] )
		interface.run()
		# eof

		# image:../img/ex_LargeText.gif:
	"""
	def __init__(self, interface, text, line_height):
		"""
		@type 	text: string

		@param	line_height: height of line (in pixels)
		@type	line_height: integer
		"""
		Widget.__init__(self, interface, autoregister=False)

		self.__spacelen = Blender.Draw.GetStringWidth(' ')
		self.__lineheight = int(abs(line_height))
		self.width  = -1
		self.text	= text
		self.align	= 'left'

	def __render_left_aligned_line(self, word_list, total_width):
		"""
		@param	word_list: list of pair (words, width of word [pixels])
		@type	word_list: list of (string, integer)

		@param	total_width: total width of all words in the list [pixels]
		@type	total_width: integer
		"""

		tmp = [word for word, width in word_list]
		return [(0, ' '.join(tmp))]

	def __render_right_aligned_line(self, word_list, total_width):
		left_margin = self.width - (total_width + (len(word_list)-1)*self.__spacelen)
		tmp = [word for word, width in word_list]
		return [(left_margin, ' '.join(tmp))]

	def __render_centered_line(self, word_list, total_width):
		left_margin = self.width - (total_width + (len(word_list)-1)*self.__spacelen)
		tmp = [word for word, width in word_list]
		return [(left_margin/2, ' '.join(tmp))]

	def __render_justified_line(self, word_list, total_width):

		def split(n, k):
			assert n >= k
			if k==0:
				return []
			else:
				i = n/k
				return [i] + split(n-i, k-1)

		tmp = []
		x   = 0
		for index, space_width in enumerate( split(self.width-total_width, len(word_list)-1) ):
			tmp.append( (x, word_list[index][0]) )
			x += word_list[index][1] + space_width

		tmp.append( (x, word_list[-1][0]) )
		return tmp

	def __render_line(self, words):
		lines	= []
		tmp		= []
		line_width			= 0
		total_line_width	= 0
		for index, item in enumerate(words):
			word_width = item[1]
			if total_line_width + word_width < self.width:
				tmp.append(item)
				line_width       += word_width
				total_line_width += word_width + self.__spacelen
			else:
				lines.append( self.alignfun(tmp, line_width) )
				line_width = total_line_width = word_width
				tmp = [item]

		if len(tmp):
			lines.append( self.alignfun(tmp, line_width) )

		return lines

	def __render_text(self):
		self.__renderedtext = []
		for line in self.__text:
			self.__renderedtext.extend( self.__render_line(line) )

	def draw(self, x, y, width, height):
		if self.width != width:
			self.width = width
			self.__render_text()

		curY = y + height - self.__lineheight
		for line in self.__renderedtext:
			for left, word in line:
				Blender.BGL.glRasterPos2d(x + left, curY)
				Blender.Draw.Text(word)
			curY -= self.__lineheight
			if curY < y: break

	def __setalign(self, align):
		if align == 'left':
			self.alignfun = self.__render_left_aligned_line
		elif align == 'right':
			self.alignfun = self.__render_right_aligned_line
		elif align == 'center':
			self.alignfun = self.__render_centered_line
		elif align == 'justify':
			self.alignfun = self.__render_justified_line
		else:
			self.alignfun = self.__render_left_aligned_line

		self.width = -1 # force recalculate

	def __settext(self, text):
		self.__text = []	# list of lists of pairs: (word, word width in pixels)
		for line in text.split('\n'):
			self.__text.append([])
			for word in line.split():
				self.__text[-1].append( (word, Blender.Draw.GetStringWidth(word)) )

		self.width = -1 # force recalculate

	align = property(None, __setalign)
	text  = property(None, __settext)

# vim: ts=4 sw=4 nowrap
