#!BPY
"""
Name: 'Mesh disc'
Blender: 236
Group: 'Add'
Tooltip: 'Create mesh disc'
"""

import Blender
import gui

from Blender import NMesh
from math import pi, sin, cos

XZ = 1
XY = 2
YZ = 4

CENTER = 0x100
CURSOR = 0x200

def create():
	obj = Disc(
		InnerRadius.value,
		OuterRadius.value,
		Segments.value,
		Subdivisions.value,
	)

	if Center.value == CURSOR:
		obj.setLocation( *Blender.Window.GetCursorPos() )
	
	if   Orientation.value == XZ:
		pass
	elif Orientation.value == XY:
		obj.RotY = pi/2.0
	elif Orientation.value == YZ:
		obj.RotX = pi/2.0

interface	= gui.Interface()

grid		= gui.Grid(interface, 10, 10, 300, 200, [0.4, 0.6], 7)
InnerRadius	= gui.FloatNumber(interface, 'Inner radius: ', 0.5, 0.00001, 1.0e8)
OuterRadius	= gui.FloatNumber(interface, 'Outer radius: ', 1.0, 0.00001, 1.0e8)
Segments	= gui.IntSlider(interface, 'Segments: ', 32, 3, 1024)
Subdivisions	= gui.IntSlider(interface, 'Subdivisions: ', 1, 1, 256)

Center		= gui.MultipleToggle(interface, [ ('World center',CENTER), ('3D cursor',CURSOR) ], 0, tooltip="Origin")
Orientation	= gui.RadioButtons(interface,  [('xz',XZ), ('xy',XY), ('yz',YZ)], XZ, tooltip="Orientation")

Create		= gui.Button(interface, 'Create', callback=create)

grid.add( InnerRadius,  0, 0, colspan=2 )
grid.add( OuterRadius,  0, 1, colspan=2 )
grid.add( Segments,     0, 2, colspan=2 )
grid.add( Subdivisions, 0, 3, colspan=2 )
grid.add( Center, 0, 4 )
grid.add( Orientation, 1, 4 )
grid.add( Create, 0, 6, colspan=2)

interface.register_container(grid)

def Disc(
	InnerRadius,
	OuterRadius,
	Segments,
	Subdivisions
	):

	poly = NMesh.GetRaw()


	#### Make vertices
	dr = (OuterRadius - InnerRadius)/Subdivisions
	r  = InnerRadius
	da = pi*2/Segments
	for _ in xrange(Subdivisions+1):
		alpha = 0.0
		for i in range(0,Segments):
			x = r * cos(alpha)
			y = r * sin(alpha)
			alpha += da
			poly.verts.append( NMesh.Vert(x,y,0.0) )

		r += dr

	#### Make faces
	for i in xrange(Subdivisions):
		ring0 = Segments * i
		ring1 = Segments * (i+1)
		for j in xrange(Segments):
			f = NMesh.Face()

			j0 = j
			j1 = (j+1) % Segments
			f.v.append(poly.verts[ring0 + j0])
			f.v.append(poly.verts[ring0 + j1])
			f.v.append(poly.verts[ring1 + j1])
			f.v.append(poly.verts[ring1 + j0])
			poly.faces.append(f)

	######### Creates a new Object with the new Mesh
	polyObj = NMesh.PutRaw(poly)
	return polyObj

interface.run()
Blender.Redraw()

# vim: ts=4 sw=4
