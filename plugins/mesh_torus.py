#!BPY
"""
Name: 'Mesh tours'
Blender: 236
Group: 'Add'
Tooltip: 'Create mesh torus'
"""

import Blender
from Blender import NMesh
from Blender import Mathutils
from math import sin,cos,pi
import gui

XZ = 1
XY = 2
YZ = 4

CENTER = 0x100
CURSOR = 0x200

def create():
	if Cut.state:
		obj = Torus2(
			MajorRadius.value,
			MinorRadius.value,
			MajorDivisions.value,
			MinorDivisions.value,
			StartMajorAngle.value,
			CapStart.state,
			EndMajorAngle.value,
			CapEnd.state,
			StartMinorAngle.value,
			Smooth.state
		)
	else:
		obj = Torus(
			MajorRadius.value,
			MinorRadius.value,
			MajorDivisions.value,
			MinorDivisions.value,
			StartMinorAngle.value,
			Smooth.state
		)
	
	if Origin.value == CURSOR:
		obj.setLocation( *Blender.Window.GetCursorPos() )
	
	if   Orientation.value == XZ:
		pass
	elif Orientation.value == XY:
		obj.RotY = pi/2.0
	elif Orientation.value == YZ:
		obj.RotX = pi/2.0

# GUI

interface	= gui.Interface()

Create	= gui.Button(interface, 'Create', callback=create)
Smooth	= gui.Toggle(interface, 'Smooth', True)
		
# basic settings
MajorRadius	= gui.FloatNumber(interface, '', 1.0, 0.00001, 1.0e8)
MinorRadius	= gui.FloatNumber(interface, '', 0.25, 0.00001, 1.0e8)
MajorDivisions	= gui.IntNumber(interface, '', 32, 3, 1024)
MinorDivisions	= gui.IntNumber(interface, '', 16, 3, 1024)
StartMinorAngle	= gui.FloatSlider(interface, '', 0, 0, 360)

# extended
StartMajorAngle	= gui.FloatSlider(interface, '', 0, 0, 360)
EndMajorAngle	= gui.FloatSlider(interface, '', 0, 0, 360)
CapStart	= gui.Toggle(interface, 'cap', True, tooltip="Cap start")
CapEnd		= gui.Toggle(interface, 'cap', True, tooltip="Cap end")
Cut		= gui.Toggle(interface, 'Cut torus', False)

# origin & orientation
Origin		= gui.MultipleToggle(interface, [ ('World center',CENTER), ('3D cursor',CURSOR) ], 0, tooltip="Origin")
Orientation	= gui.RadioButtons(interface,  [('xz',XZ), ('xy',XY), ('yz',YZ)], XZ, tooltip="Orientation")

# rows container
rows		= gui.Rows(interface, 10, 10, 300, padx=4)

def _(text): return gui.Text(interface, text, align="right")

rows.addrow( [ (_("Major radius:"),0.4) , MajorRadius] ).addvspace("quarter")
rows.addrow( [ (_("Minor radius:"),0.4) , MinorRadius] ).addvspace()

rows.addrow( [ (_("Major divisions:"),0.4) , MajorDivisions] ).addvspace("quarter")
rows.addrow( [ (_("Minor divisions:"),0.4) , MinorDivisions] ).addvspace("quarter")
rows.addrow( [ (_("Minor angle start:"),0.4) , StartMinorAngle] ).addvspace()

rows.addrow( [(Origin, 0.3), Orientation] ).addvspace()

rows.addrow( Cut ).addvspace("quarter")
rows.addrow( [ (_("Start angle: "), 0.35), StartMajorAngle, (CapStart, 0.1) ] ).addvspace("quarter")
rows.addrow( [ (_("End angle: "),   0.35), EndMajorAngle,   (CapEnd,   0.1) ] ).addvspace()

rows.addrow( [Create, Smooth] )

rows.addrow( [] )

interface.register_container(rows)
interface.run()

# Simple torus
def Torus(
		MajorRadius,
		MinorRadius,
		MajorDivisions,
		MinorDivisions,
		StartMinorAngle,
		Smooth):

	# deg 2 rad
	StartMinorAngle = (StartMinorAngle * 2*pi)/180

	def MakeVertexRing(vertex_list, angle):
		m = Mathutils.RotationMatrix(angle, 3, "z")
		for i in xrange(MinorDivisions):
			phi = (pi*2 * i/MinorDivisions) + StartMinorAngle
			x = MajorRadius + MinorRadius * cos(phi)
			y = 0.0
			z = MinorRadius * sin(phi)

			v = Mathutils.Vector( [x,y,z] )
			v = Mathutils.VecMultMat(v, m)

			vertex_list.append( NMesh.Vert( v.x, v.y, v.z ) )
	
	######### Creates a new mesh
	poly = NMesh.GetRaw()

	angle	= 0
	da		= 360.0/MajorDivisions
	for _ in xrange(MajorDivisions):
		MakeVertexRing(poly.verts, angle)
		angle += da

	######## Make faces
	for i in xrange(MajorDivisions):
		ring1_num = MinorDivisions * i
		ring2_num = MinorDivisions * ((i+1) % MajorDivisions)
		for j in xrange(MinorDivisions):
			f = NMesh.Face()
			f.smooth = Smooth

			f.v.append(poly.verts[ring1_num + j])
			f.v.append(poly.verts[ring1_num + (j+1) % MinorDivisions])
			f.v.append(poly.verts[ring2_num + (j+1) % MinorDivisions])
			f.v.append(poly.verts[ring2_num + j])
			poly.faces.append(f)

	polyObj = NMesh.PutRaw(poly)
	return polyObj

# Piece of torus
def Torus2(
		MajorRadius,
		MinorRadius,
		MajorDivisions,
		MinorDivisions,
		StartMajorAngle,
		CapStart,
		EndMajorAngle,
		CapEnd,
		StartMinorAngle,
		Smooth):

	# deg 2 rad
	StartMinorAngle = (StartMinorAngle * 2*pi)/180

	StartMajorAngle, EndMajorAngle = min(StartMajorAngle, EndMajorAngle), max(StartMajorAngle, EndMajorAngle)

	def MakeVertexRing(vertex_list, angle):
		m = Mathutils.RotationMatrix(angle, 3, "z")
		for i in xrange(MinorDivisions):
			phi = (pi*2 * i/MinorDivisions) + StartMinorAngle
			x = MajorRadius + MinorRadius * cos(phi)
			y = 0.0
			z = MinorRadius * sin(phi)

			v = Mathutils.Vector( [x,y,z] )
			v = Mathutils.VecMultMat(v, m)

			vertex_list.append( NMesh.Vert( v.x, v.y, v.z ) )
	
	######### Creates a new mesh
	poly = NMesh.GetRaw()

	angle	= StartMajorAngle
	da		= (EndMajorAngle-StartMajorAngle)/MajorDivisions
	for _ in xrange(MajorDivisions+1):
		MakeVertexRing(poly.verts, angle)
		angle += da

	######## Make faces
	for i in xrange(MajorDivisions):
		ring1_num = MinorDivisions * i
		ring2_num = MinorDivisions * (i+1)
		for j in xrange(MinorDivisions):
			f = NMesh.Face()
			f.smooth = Smooth

			f.v.append(poly.verts[ring1_num + j])
			f.v.append(poly.verts[ring1_num + (j+1) % MinorDivisions])
			f.v.append(poly.verts[ring2_num + (j+1) % MinorDivisions])
			f.v.append(poly.verts[ring2_num + j])
			poly.faces.append(f)
	
	####
	if CapStart:
		for i in xrange(MinorDivisions-1):
			f = NMesh.Face()
			f.smooth = Smooth
			
			f.v.append(poly.verts[0])
			f.v.append(poly.verts[i])
			f.v.append(poly.verts[i+1])
			poly.faces.append(f)
	
	####
	if CapEnd:
		for i in xrange(MinorDivisions-1):
			f = NMesh.Face()
			f.smooth = Smooth
			
			f.v.append(poly.verts[-1])
			f.v.append(poly.verts[-(i+1)])
			f.v.append(poly.verts[-(i+2)])
			poly.faces.append(f)

	polyObj = NMesh.PutRaw(poly)
	return polyObj

Blender.Redraw()

# vim: ts=4 sw=4
# $Id: mesh_torus.py,v 1.1.1.1 2006-04-03 18:20:34 wojtek Exp $
