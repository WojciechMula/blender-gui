#!BPY
"""
Name: 'Twist'
Blender: 236
Group: 'Mesh'
Tooltip: 'Twist a mesh'
"""

import Blender
import sys
import gui
from math import sin,cos,acos,pi

# define callbacks

vertex_list = []
mesh		= None
min_x, max_x	= None, None
min_y, max_y	= None, None
min_z, max_z	= None, None

def get_selected():
	global vertex_list, mesh, min_x, max_x, min_y, max_y, min_z, max_z

	if not mesh:
		for object in Blender.Object.GetSelected():
			if object.getType() == 'Mesh':
				Info.text = '%s selected' % object.getName()
				mesh = object.getData()
				vertex_list = [(v.co[0], v.co[1], v.co[2]) for v in mesh.verts]

				min_x = min([x for x,_,_ in object.getBoundBox()])
				max_x = max([x for x,_,_ in object.getBoundBox()])
				min_y = min([y for _,y,_ in object.getBoundBox()])
				max_y = max([y for _,y,_ in object.getBoundBox()])
				min_z = min([z for _,_,z in object.getBoundBox()])
				max_z = max([z for _,_,z in object.getBoundBox()])
				return
	
		Info.text = 'No mesh selected'

def cancel():
	global vertex_list, mesh

	if mesh:
		for index, v in enumerate(mesh.verts):
			v.co[0], v.co[1], v.co[2] = vertex_list[index]
		mesh.update()
	
	vertex_list = []
	mesh		= None
	Info.text	= 'No mesh selected'

AXIS_X = 1
AXIS_Y = 2
AXIS_Z = 3

def update():
	global vertex_list, mesh
	if mesh:
		axis = {AXIS_X: 'x', AXIS_Y: 'y', AXIS_Z: 'z'}
		twist_mesh(
			vertex_list,
			mesh,
			axis[Axis.value],
			Angle.value,
			StartFrom.value,
			EndAt.value
		)

def live_update(_):
	if LiveUpdate.state:
		update()

def apply():
	global vertex_list, mesh
	if mesh:
		update()

		vertex_list	= []
		mesh		= []
		Info.text	= 'No mesh selected'

# make interface
interface	= gui.Interface('mesh twist $Revision: 1.1.1.1 $')

StartFrom	= gui.FloatSlider(interface, 'Start: ',   0.0, 0.0, 100.0, callback=live_update)
EndAt		= gui.FloatSlider(interface, 'End: ' , 100.0, 0.0, 100.0, callback=live_update)
Axis		= gui.RadioButtons(interface, [('X', AXIS_X), ('Y', AXIS_Y), ('Z', AXIS_Z)], AXIS_Y, callback=live_update)
Angle		= gui.FloatSlider(interface, 'Angle: ',   0.0, 0.0, 360.0*100, callback=live_update)
LiveUpdate	= gui.Toggle(interface, 'Live update', False)

Info		= gui.Text(interface, 'No mesh selected', align='center')
GetMesh		= gui.Button(interface, 'Get mesh', callback=get_selected)

Cancel		= gui.Button(interface, 'Cancel', callback=cancel)
Apply		= gui.Button(interface, 'Apply', callback=apply)
Update		= gui.Button(interface, 'Update', callback=update)

rows = gui.Rows(interface, 10, 10, 250, 20)

rows.addrow( Info ).addvspace('half')

rows.addrow( StartFrom )
rows.addrow( EndAt ).addvspace('half')
rows.addrow( Axis )
rows.addrow( Angle ).addvspace('half')

rows.addrow( [GetMesh, LiveUpdate] )
rows.addrow( [Cancel, Update, Apply] )

interface.register_container( rows )
interface.run()

# common functions
def twist_mesh(vertex_list, mesh, Axis, Angle, StartFrom, EndAt):

	StartFrom, EndAt = min(StartFrom, EndAt)/100.0, max(StartFrom, EndAt)/100.0
	Angle = pi*Angle/180.0

	def rot_x( (x,y,z) , angle):
		c = cos(angle)
		s = sin(angle)
		return (x, y*c-z*s, y*s+z*c)

	def rot_y( (x,y,z) , angle):
		c = cos(angle)
		s = sin(angle)
		return (x*c-z*s, y, x*s+z*c)
	
	def rot_z( (x,y,z) , angle):
		c = cos(angle)
		s = sin(angle)
		return (x*c-y*s, x*s+y*s, z)

	if Axis == 'x':
		d  = max_x - min_x
		rd = EndAt-StartFrom
		for index, v in enumerate(mesh.verts):
			t = (vertex_list[index][0]-min_x)/d
			if StartFrom <= t <= EndAt: 
				ang = Angle*(t-StartFrom)/rd
				v.co[0], v.co[1], v.co[2] = rot_x( vertex_list[index], ang)
			else:
				v.co[0], v.co[1], v.co[2] = vertex_list[index]

		mesh.update()
		return True
	elif Axis == 'y':
		d  = max_y - min_y
		rd = EndAt-StartFrom
		for index, v in enumerate(mesh.verts):
			t = (vertex_list[index][1]-min_y)/d
			if StartFrom <= t <= EndAt: 
				ang = Angle*(t-StartFrom)/rd
				v.co[0], v.co[1], v.co[2] = rot_y( vertex_list[index], ang)
			else:
				v.co[0], v.co[1], v.co[2] = vertex_list[index]

		mesh.update()
		return True
	elif Axis == 'z':
		d  = max_z - min_z
		rd = EndAt-StartFrom
		for index, v in enumerate(mesh.verts):
			t = (vertex_list[index][2]-min_z)/d
			if StartFrom <= t <= EndAt:
				ang = Angle*(t-StartFrom)/rd
				v.co[0], v.co[1], v.co[2] = rot_z( vertex_list[index], ang)
			else:
				v.co[0], v.co[1], v.co[2] = vertex_list[index]

		mesh.update()
		return True
	else:
		return False
	
# vim: ts=4 sw=4
# $Id: mesh_twist.py,v 1.1.1.1 2006-04-03 18:20:34 wojtek Exp $
