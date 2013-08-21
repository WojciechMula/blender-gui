#!BPY
"""
Name: 'Mesh sphere'
Blender: 236
Group: 'Add'
Tooltip: 'Create UV mesh sphere'
"""

import Blender
import gui
from math import sin,cos,acos,pi

XZ = 1
XY = 2
YZ = 4

CENTER = 0x100
CURSOR = 0x200

def create():
	if Hemisphere.state:
		obj = Sphere2(
			Radius.value,
			UDivisions.value,
			VDivisions.value,
			Percent.value,
			Cap.state,
			CapMethod.value,
			Smooth.state
		)
	else:
		obj = Sphere(
			Radius.value,
			UDivisions.value,
			VDivisions.value,
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


interface = gui.Interface('Mesh Sphere $Revision: 1.1.1.1 $')

Radius 		= gui.FloatNumber(interface, '', 1, 0.001, 1.0e8)
UDivisions	= gui.IntNumber(interface, 'U: ', 16, 3, 1024)
VDivisions	= gui.IntNumber(interface, 'V: ', 16, 3, 1024)
Smooth		= gui.Toggle(interface, 'Smooth', True)

Create		= gui.Button(interface, 'Create', callback=create)

Hemisphere	= gui.Toggle(interface, 'Hemisphere', False)
Cap			= gui.Toggle(interface, 'Cap', True)
CapMethod	= gui.MultipleToggle(interface,  ['simple', 'symmetrical'], 0)
Percent		= gui.FloatSlider(interface, '', 50, 0, 100)

Origin		= gui.MultipleToggle(interface, [ ('World center',CENTER), ('3D cursor',CURSOR) ], 0, tooltip="Origin")
Orientation	= gui.RadioButtons(interface,  [('xz',XZ), ('xy',XY), ('yz',YZ)], XZ, tooltip="Orientation")

rows = gui.Rows(interface, 10, 10, 300, 20, padx=4)
rows.addrow( gui.Text(interface, 'Sphere radius') )
rows.addvspace("quarter")
rows.addrow( Radius )
rows.addvspace()

rows.addrow( gui.Text(interface, 'Divisions:') )
rows.addvspace("quarter")
rows.addrow( UDivisions )
rows.addvspace("quarter")
rows.addrow( VDivisions )

rows.addvspace()

rows.addrow( [Hemisphere, Cap, CapMethod] )
rows.addvspace("quarter")
rows.addrow( Percent )

rows.addvspace()

rows.addrow( [(Origin, 0.3), Orientation] )
rows.addvspace()

rows.addrow( [Create, Smooth] )

interface.register_container(rows)
interface.run()

def Sphere(
		Radius,
		UDivisions,
		VDivisions,
		Smooth):

	def MakeVertexRing(vertex_list, r, z):
		for i in xrange(UDivisions):
			phi = (pi*2 * i/UDivisions)
			x = r * cos(phi)
			y = r * sin(phi)

			vertex_list.append( Blender.NMesh.Vert(x,y,z) )

	######### Creates a new mesh
	poly = Blender.NMesh.GetRaw()

	da		= 180.0/VDivisions
	angle	= da
	for _ in xrange(VDivisions-1):
		r = Radius * sin(angle/180 * pi)
		z = Radius * cos(angle/180 * pi)
		MakeVertexRing(poly.verts, r, z)
		angle += da

	poly.verts.append( Blender.NMesh.Vert(0.0, 0.0, +Radius) )
	poly.verts.append( Blender.NMesh.Vert(0.0, 0.0, -Radius) )

	######## Make faces
	for i in xrange(VDivisions-2):
		ring1_num = UDivisions * i
		ring2_num = UDivisions * (i+1)
		for j in xrange(UDivisions):
			f = Blender.NMesh.Face()
			f.smooth = Smooth

			f.v.append(poly.verts[ring1_num + j])
			f.v.append(poly.verts[ring1_num + (j+1) % UDivisions])
			f.v.append(poly.verts[ring2_num + (j+1) % UDivisions])
			f.v.append(poly.verts[ring2_num + j])
			poly.faces.append(f)

	for k in xrange(UDivisions):
			i = k
			j = (k+1) % UDivisions

			f = Blender.NMesh.Face()
			f.smooth = Smooth
			f.v.append(poly.verts[-1])
			f.v.append(poly.verts[-(i+3)])
			f.v.append(poly.verts[-(j+3)])
			poly.faces.append(f)

			f = Blender.NMesh.Face()
			f.smooth = Smooth
			f.v.append(poly.verts[-2])
			f.v.append(poly.verts[i])
			f.v.append(poly.verts[j])
			poly.faces.append(f)

	polyObj = Blender.NMesh.PutRaw(poly)
	return polyObj

def Sphere2(
		Radius,
		UDivisions,
		VDivisions,
		Clip,
		CapBottom,
		CapSymmetrical,
		Smooth):

	def MakeVertexRing(vertex_list, r, z):
		for i in xrange(UDivisions):
			phi = (pi*2 * i/UDivisions)
			x = r * cos(phi)
			y = r * sin(phi)

			vertex_list.append( Blender.NMesh.Vert(x,y,z) )

	######### Creates a new mesh
	poly = Blender.NMesh.GetRaw()

	norm_z	= 1.0-(Clip/50.0) # -1..+1
	rang	= 180*acos(norm_z)/pi
	min_z	= Radius * cos(rang/180 * pi)

	da		= rang/VDivisions
	angle	= rang
	for _ in xrange(VDivisions-1):
		r = Radius * sin(angle/180 * pi)
		z = Radius * cos(angle/180 * pi)
		MakeVertexRing(poly.verts, r, z)
		angle -= da

	poly.verts.append( Blender.NMesh.Vert(0.0, 0.0, +Radius) )

	######## Make faces

	#### Make "inner" sphere skin
	for i in xrange(VDivisions-2):
		ring1_num = UDivisions * i
		ring2_num = UDivisions * (i+1)
		for j in xrange(UDivisions):
			f = Blender.NMesh.Face()
			f.smooth = Smooth

			f.v.append(poly.verts[ring1_num + j])
			f.v.append(poly.verts[ring1_num + (j+1) % UDivisions])
			f.v.append(poly.verts[ring2_num + (j+1) % UDivisions])
			f.v.append(poly.verts[ring2_num + j])
			poly.faces.append(f)

	#### make faces around top (single) vertex
	for k in xrange(UDivisions):
			i = k
			j = (k+1) % UDivisions

			f = Blender.NMesh.Face()
			f.smooth = Smooth
			f.v.append(poly.verts[-1])
			f.v.append(poly.verts[-(i+2)])
			f.v.append(poly.verts[-(j+2)])
			poly.faces.append(f)

	#### cap the hole
	if CapBottom:
		if CapSymmetrical:
			poly.verts.append( Blender.NMesh.Vert(0.0, 0.0, min_z) )
			for i in xrange(UDivisions):
				f = Blender.NMesh.Face()
				f.smooth = Smooth
				f.v.append(poly.verts[-1])
				f.v.append(poly.verts[i])
				f.v.append(poly.verts[(i+1) % UDivisions])
				poly.faces.append(f)
		else:
			for i in xrange(UDivisions-2):
				f = Blender.NMesh.Face()
				f.smooth = Smooth
				f.v.append(poly.verts[0])
				f.v.append(poly.verts[i+1])
				f.v.append(poly.verts[i+2])
				poly.faces.append(f)

	polyObj = Blender.NMesh.PutRaw(poly)
	return polyObj

Blender.Redraw()

# vim: ts=4 sw=4
# $Id: mesh_sphere.py,v 1.1.1.1 2006-04-03 18:20:34 wojtek Exp $
