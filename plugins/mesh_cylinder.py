#!BPY
"""
Name: 'Mesh cylinder'
Blender: 236
Group: 'Add'
Tooltip: 'Create mesh cylider'
"""

import Blender
from Blender import NMesh
from Blender.BGL import *
from Blender.Draw import *

import math
from math import *

XZ = 1
XY = 2
YZ = 4

CENTER = 0x100
CURSOR = 0x200

def create():
	obj = Cylinder(
		Radius.value,
		Height.value,
		Segments.value,
		OuterDivisions.value,
		CapDivisions.value,
		Smooth.state,
	)

	if Origin.value == CURSOR:
		obj.setLocation( *Blender.Window.GetCursorPos() )

	if   Orientation.value == XZ:
		pass
	elif Orientation.value == XY:
		obj.RotY = pi/2.0
	elif Orientation.value == YZ:
		obj.RotX = pi/2.0


###### Make GUI
import gui

interface = gui.Interface('Mesh cylinder $Revision: 1.1.1.1 $')

### Make widgets

# dimensions
Radius	= gui.FloatNumber(interface, '', 1.0, 0.0001, 1.0e8, tooltip='Radius')
Height	= gui.FloatNumber(interface, '', 3.0, 0.0001, 1.0e8, tooltip='Height')

# accuracy
CapDivisions	= gui.IntNumber(interface, '', 1, 1, 256, tooltip="Cap divisions")
OuterDivisions	= gui.IntNumber(interface, '', 1, 1, 256, tooltip="Outer divisions")
Segments		= gui.IntNumber(interface, '', 32, 3, 1024, tooltip="Segments")

# cut
#UseAngles	= gui.Toggle(interface, 'Cut tube', False)
#StartAngle	= gui.FloatSlider(interface, '', 0, 0, 360)
#EndAngle	= gui.FloatSlider(interface, '', 0, 0, 360)

# origin & orientation
Origin		= gui.MultipleToggle(interface, [ ('World center',CENTER), ('3D cursor',CURSOR) ], 0, tooltip="Origin")
Orientation	= gui.RadioButtons(interface,  [('xz',XZ), ('xy',XY), ('yz',YZ)], XZ, tooltip="Orientation")

#
Create		= gui.Button(interface, 'Create', callback=create)
Smooth		= gui.Toggle(interface, 'Smooth', True, 'Smooth mesh')

# place widgets at container
rows = gui.Rows(interface, 10, 10, 300, padx=4)

def _(text): return gui.Text(interface, text, align="right")

rows.addrow( [ (_("Radius: "), 0.4), Radius ] ).addvspace("quarter")
rows.addrow( [ (_("Height: "), 0.4), Height ] ).addvspace()

rows.addrow( [ (_("Segments: "), 0.4), Segments ] ).addvspace("quarter")
rows.addrow( [ (_("Outer divisions: "), 0.4), OuterDivisions ] ).addvspace("quarter")
rows.addrow( [ (_("Cap divisions: "), 0.4), CapDivisions ] ).addvspace()

#rows.addrow( UseAngles ).addvspace("quarter")
#rows.addrow( [ (_("Start angle: "), 0.4), StartAngle ] ).addvspace("quarter")
#rows.addrow( [ (_("End angle: "), 0.4), EndAngle ] ).addvspace()

rows.addrow( [(Origin, 0.3), Orientation] ).addvspace()

rows.addrow( [Create, Smooth] )

interface.register_container(rows)
interface.run()

def Cylinder(
	Radius,
	Height,
	Segments,
	Divisions,
	CapDivisions,
	Smooth):

	def MakeVertexRing(vertex_list, r, z):
		for i in xrange(Segments):
			phi = (pi*2 * i/Segments)
			x = r * cos(phi)
			y = r * sin(phi)

			vertex_list.append( Blender.NMesh.Vert(x,y,z) )

	######### Creates a new mesh
	poly = NMesh.GetRaw()

	#### make vertexes
	dr = Radius/CapDivisions
	r  = dr
	for _ in xrange(CapDivisions):
		MakeVertexRing(poly.verts, r, 0.0)
		r += dr

	r  = Radius
	dz = Height/Divisions
	z  = 0.0
	for _ in xrange(Divisions):
		MakeVertexRing(poly.verts, r, z)
		z += dz

	dr = Radius/CapDivisions
	r  = Radius
	for _ in xrange(CapDivisions):
		MakeVertexRing(poly.verts, r, Height)
		r -= dr

	#### Make faces
	tvc = 2*(CapDivisions-1) + Divisions + 1
	for i in xrange(tvc):
		ring1_num = Segments * i
		ring2_num = Segments * (i+1)
		for j in xrange(Segments):
			j0 = j
			j1 = (j+1) % Segments

			f = Blender.NMesh.Face()
			f.smooth = Smooth

			f.v.append(poly.verts[ring1_num + j0])
			f.v.append(poly.verts[ring1_num + j1])
			f.v.append(poly.verts[ring2_num + j1])
			f.v.append(poly.verts[ring2_num + j0])
			poly.faces.append(f)

	#### Cap caps
	poly.verts.append( Blender.NMesh.Vert(0,0,0) )
	poly.verts.append( Blender.NMesh.Vert(0,0,Height) )
	for j in xrange(Segments):
		j0 = j
		j1 = (j+1) % Segments

		f = Blender.NMesh.Face()
		f.smooth = Smooth
		f.v.append(poly.verts[-2])
		f.v.append(poly.verts[j0])
		f.v.append(poly.verts[j1])
		poly.faces.append(f)

		f = Blender.NMesh.Face()
		f.smooth = Smooth
		f.v.append(poly.verts[-1])
		f.v.append(poly.verts[-(j0+3)])
		f.v.append(poly.verts[-(j1+3)])
		poly.faces.append(f)

	polyObj = NMesh.PutRaw(poly)
	return polyObj

Blender.Redraw()

# vim: ts=4 sw=4

