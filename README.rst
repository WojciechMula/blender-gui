========================================================================
                      Blender GUI
========================================================================

Last update: 2006-10-11 (the module is not maintained any longer)


Introduction
------------------------------------------------------------------------


The built-in module Blender_.Draw gives access to basic GUI
elements like buttons, sliders etc, it also manages user
input. But programming interface is function-orientated and
thus slightly primitive. Programmer have to write a lot of
code, mostly redundant; the code is large, entangled, hard
to read, extend, and maintain.

I've decided to write an object orientated programming
interface, that works at higher level of abstraction and
makes almost all common actions.  It is easy to use and
understand, even for non-programmers.

I hope that module will be useful for Blender_ users.


Contents
------------------------------------------------------------------------

* `gui.py <gui.py>`_ --- main program
* `extract_examples.py <extract_examples.py>`_ --- utility
  to extract samples from ``gui.py``
* `epydoc_img.py <epydoc_img.py>`_ --- simple utility that
  adds images to epydoc output
* documentation of the module in html format


Sample extensions that use ``blender-gui``
------------------------------------------------------------------------

Cylinder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_cylinder.py <plugins/mesh_cylinder.py>`_
* .. image:: plugins/mesh_cylinder.png


Disc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_disc.py <plugins/mesh_disc.py>`_
* .. image:: plugins/mesh_disc.png


Cylinder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_sphere.py <plugins/mesh_sphere.py>`_
* .. image:: plugins/mesh_sphere.png


Torus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_torus.py <plugins/mesh_torus.py>`_
* .. image:: plugins/mesh_torus.png


Tube
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_tube.py <plugins/mesh_tube.py>`_
* .. image:: plugins/mesh_tube.png


Twist mesh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `mesh_twist.py <plugins/mesh_twist.py>`_
* .. image:: plugins/mesh_twist.png


.. _Blender: http://www.blender.org
.. _Epydoc:  http://epydoc.sourceforge.net

