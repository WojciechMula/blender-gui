#!BPY
"""
Name: 'Mesh tube'
Blender: 236
Group: 'Add'
Tooltip: 'Create mesh tube'
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
	obj = Tube(
		InnerRadius.value,
		OuterRadius.value,
		Height.value,
		InnerDivisions.value,
		OuterDivisions.value,
		CapDivisions.value,
		Segments.value,
		Smooth.state,
		StartAngle.value,
		EndAngle.value,
		UseAngles.state
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

interface = gui.Interface('Mesh tube $Revision: 1.1.1.1 $')

### Make widgets

# dimensions
InnerRadius	= gui.FloatNumber(interface, '', 1.0, 0.0001, 1.0e8, tooltip='Inner radius')
OuterRadius	= gui.FloatNumber(interface, '', 2.0, 0.0001, 1.0e8, tooltip='Outer radius')
Height		= gui.FloatNumber(interface, '', 5.0, 0.0001, 1.0e8, tooltip='Height')

# accuracy
InnerDivisions	= gui.IntNumber(interface, '', 1, 1, 512, tooltip="Inner divisions")
OuterDivisions	= gui.IntNumber(interface, '', 1, 1, 512, tooltip="Outer divisions")
CapDivisions	= gui.IntNumber(interface, '', 1, 1, 256, tooltip="Cap divisions")
Segments		= gui.IntNumber(interface, '', 32, 3, 1024, tooltip="Segments")

# cut 
UseAngles	= gui.Toggle(interface, 'Cut tube', False)
StartAngle	= gui.FloatSlider(interface, '', 0, 0, 360)
EndAngle	= gui.FloatSlider(interface, '', 0, 0, 360)

# origin & orientation
Origin		= gui.MultipleToggle(interface, [ ('World center',CENTER), ('3D cursor',CURSOR) ], 0, tooltip="Origin")
Orientation	= gui.RadioButtons(interface,  [('xz',XZ), ('xy',XY), ('yz',YZ)], XZ, tooltip="Orientation")

# 
Create		= gui.Button(interface, 'Create', callback=create)
Smooth		= gui.Toggle(interface, 'Smooth', True, 'Smooth mesh')

# place widgets at container
rows = gui.Rows(interface, 10, 10, 300, padx=4)

def _(text): return gui.Text(interface, text, align="right")

rows.addrow( [ (_("Inner radius: "), 0.4), InnerRadius ] ).addvspace("quarter")
rows.addrow( [ (_("Outer radius: "), 0.4), OuterRadius ] ).addvspace("quarter")
rows.addrow( [ (_("Height: "), 0.4), Height ] ).addvspace()

rows.addrow( [ (_("Segments: "), 0.4), Segments ] ).addvspace("quarter")
rows.addrow( [ (_("Inner divisions: "), 0.4), InnerDivisions ] ).addvspace("quarter")
rows.addrow( [ (_("Outer divisions: "), 0.4), OuterDivisions ] ).addvspace("quarter")
rows.addrow( [ (_("Cap divisions: "), 0.4), CapDivisions ] ).addvspace()

rows.addrow( UseAngles ).addvspace("quarter")
rows.addrow( [ (_("Start angle: "), 0.4), StartAngle ] ).addvspace("quarter")
rows.addrow( [ (_("End angle: "), 0.4), EndAngle ] ).addvspace()

rows.addrow( [(Origin, 0.3), Orientation] ).addvspace()

rows.addrow( [Create, Smooth] )

interface.register_container(rows)
interface.run()

def Tube(InnerRadius, OuterRadius, Height, InnerDivisions, OuterDivisions, CapDivisions, Segments, Smooth, StartAngle, EndAngle, UseAngles):

	def MakeVertexRectange():
		# makes one side of a tube's section
		
		vertex_list = []

		# inner vertexes (except top one)
		x	= InnerRadius
		y	= 0.0
		z	= 0.0
		dz	= Height/InnerDivisions
		for i in xrange(InnerDivisions):
			vertex_list.append( (x,y,z) )
			z += dz

		# top vertexes (except outer one)
		x	= InnerRadius
		z	= Height
		dx	= (OuterRadius-InnerRadius)/CapDivisions
		for i in xrange(CapDivisions):
			vertex_list.append( (x,y,z) )
			x += dx

		# outer vertexes (except bottom one)
		x	= OuterRadius
		z	= Height
		dz	= Height/OuterDivisions
		for i in xrange(OuterDivisions):
			vertex_list.append( (x,y,z) )
			z -= dz

		# outer vertexes (except inner one)
		x	= OuterRadius
		z	= 0
		for i in xrange(CapDivisions):
			vertex_list.append( (x,y,z) )
			x -= dx

		return vertex_list
	
	def RotateZvert( (x,y,z), angle ):
		c = cos(angle)
		s = sin(angle)
		
		X = c*x - s*y
		Y = s*x + c*y

		return (X,Y,z)
	
	def AddYRotatedVertexes(polygon_vertex_list, vertex_list, angle):
		c = cos(angle)
		s = sin(angle)

		for (x,y,z) in vertex_list:
			X = c*x - s*y
			Y = s*x + c*y
			Z = z

			polygon_vertex_list.append( NMesh.Vert(X,Y,Z) )
	
	def deg2rad(angle):
		return pi*angle/180.0
	def rad2deg(angle):
		return 180*angle/pi
	
	######### Creates a new mesh
	poly = NMesh.GetRaw()

	#### make vertexes
	vert = MakeVertexRectange()
	if UseAngles:
		da			= float(EndAngle-StartAngle)/Segments
		angle		= StartAngle
		segments	= Segments+1
	else:
		da			= 360.0/Segments
		angle		= 0.0
		segments	= Segments

	angle	= deg2rad(angle)
	da		= deg2rad(da)

	for _ in xrange(segments):
		AddYRotatedVertexes(poly.verts, vert, angle)
		angle += da

	#### Make faces
	vps = 2*CapDivisions + InnerDivisions + OuterDivisions

	## skin
	for i in xrange(Segments):
		section0 = vps * i
		section1 = vps * ((i+1) % segments)
		for j in xrange(vps):
			f			= NMesh.Face()
			f.smooth	= Smooth

			j0 = j
			j1 = (j+1) % vps

			f.v.append(poly.verts[section0+j0])
			f.v.append(poly.verts[section0+j1])
			f.v.append(poly.verts[section1+j1])
			f.v.append(poly.verts[section1+j0])

			poly.faces.append(f)
			
	## caps
	if UseAngles:
	
		# add vertex at center of caps
		X = (InnerRadius + OuterRadius)/2.0
		Y = 0
		Z = Height/2.0

		poly.verts.append( NMesh.Vert( *RotateZvert( (X,Y,Z), deg2rad(StartAngle) ) ) )
		poly.verts.append( NMesh.Vert( *RotateZvert( (X,Y,Z), deg2rad(EndAngle) ) ) )

		# and make faces
		for i in xrange(vps):
			f0			= NMesh.Face()
			f1			= NMesh.Face()
			f0.smooth	= Smooth
			f1.smooth	= Smooth

			i0 = i
			i1 = (i+1) % vps

			f0.v.append(poly.verts[-2])
			f0.v.append(poly.verts[i0])
			f0.v.append(poly.verts[i1])

			f1.v.append(poly.verts[-1])
			f1.v.append(poly.verts[-(i0+3)])
			f1.v.append(poly.verts[-(i1+3)])
			
			poly.faces.append(f0)
			poly.faces.append(f1)

	polyObj = NMesh.PutRaw(poly)
	return polyObj

Blender.Redraw()

# vim: ts=4 sw=4

