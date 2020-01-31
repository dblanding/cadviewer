#!/usr/bin/env python
#
# Copyright 2020 Doug Blanding (dblanding@gmail.com)
#
# This file is part of cadViewer.
# The latest  version of this file can be found at:
# //https://github.com/dblanding/cadviewer
#
# cadViewer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# cadViewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# if not, write to the Free Software Foundation, Inc.
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import sys
from math import pi

from OCC.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.AIS import *
from OCC.Quantity import *
from OCC.Display.SimpleGui import init_display
from OCC.TopoDS import *
from OCC.gp import *
from OCC.TopLoc import *
from OCC.Geom import *
from OCC.BRep import BRep_Tool_Surface
from OCC.GCE2d import *
from OCC.BRepBuilderAPI import *
from OCC.GC import *
import aocutils.brep.solid_make

display, start_display, add_menu, add_function_to_menu = init_display()


def geom_plane_from_face(aFace):
    """
    Returns the geometric plane entity from a planar surface
    """
    return Handle_Geom_Plane.DownCast(OCC.BRep.BRep_Tool_Surface(aFace)).GetObject()

def redraw(shape, event=None):
    # display with crisp edges and transpaarency
    context = display.Context
    context.RemoveAll()
    context.SetAutoActivateSelection(False)
    aisShape = AIS_Shape(shape)
    h_aisShape = aisShape.GetHandle()
    context.Display(h_aisShape)
    context.SetTransparency(h_aisShape, .1)
    context.HilightWithColor(h_aisShape, OCC.Quantity.Quantity_NOC_BLACK)
    display.FitAll()
    
def makeBox(event=None):
    # Make a box
    Box = BRepPrimAPI_MakeBox(60, 60, 50).Shape()
    redraw()
    
def rotateBox():
    aisShape = AIS_Shape(Box)
    ax1 = gp_Ax1(gp_Pnt(0., 0., 0.), gp_Dir(1., 0., 0.))
    aRotTrsf = gp_Trsf()
    angle = pi/6
    aRotTrsf.SetRotation(ax1, angle)
    aTopLoc = TopLoc_Location(aRotTrsf)
    Box.Move(aTopLoc)
    redraw()

def enableFaceSelect(event=None):
    display.selected_shape = None
    display.SetSelectionModeFace()

def makeSqProfile(size, surface):
    # points and segments need to be in CW sequence to get W pointing along Z
    aPnt1 = gp_Pnt2d(-size, size)
    aPnt2 = gp_Pnt2d(size, size)
    aPnt3 = gp_Pnt2d(size, -size)
    aPnt4 = gp_Pnt2d(-size, -size)
    aSegment1 = GCE2d_MakeSegment(aPnt1, aPnt2)
    aSegment2 = GCE2d_MakeSegment(aPnt2, aPnt3)
    aSegment3 = GCE2d_MakeSegment(aPnt3, aPnt4)
    aSegment4 = GCE2d_MakeSegment(aPnt4, aPnt1)
    print 'Next is where something crashes'
    aEdge1 = BRepBuilderAPI_MakeEdge(aSegment1.Value(),
                                     Handle_Geom_Surface(surface))
    aEdge2 = BRepBuilderAPI_MakeEdge(aSegment2.Value(),
                                     Handle_Geom_Surface(surface))
    aEdge3 = BRepBuilderAPI_MakeEdge(aSegment3.Value(),
                                     Handle_Geom_Surface(surface))
    aEdge4 = BRepBuilderAPI_MakeEdge(aSegment4.Value(),
                                     Handle_Geom_Surface(surface))
    print "Doesn't get here (with rotated box)"
    aWire = BRepBuilderAPI_MakeWire(aEdge1.Edge(),
                                    aEdge2.Edge(),
                                    aEdge3.Edge(),
                                    aEdge4.Edge())

    myWireProfile = aWire.Wire()
    return myWireProfile # TopoDS_Wire

def wireProfileOnFace(event=None):
    aShape = display.GetSelectedShape()
    shapes = display.GetSelectedShapes()
    face = None
    if aShape:
        face = topods_Face(aShape)
        print "A shape found:"
    elif shapes:
        aShape = shapes[0]
        face = topods_Face(aShape)
        print len(shapes), "Shapes found"
    if face:
        surface = geom_plane_from_face(face)
        wireProfile = makeSqProfile(50, surface)
        display.DisplayShape(wireProfile)
    else:
        print 'no face'

def translatePnt(p1, vec):
    p2 = gp_Pnt()
    p2 = p1.Translated(vec)
    return p2

def pointsToWire(p1, p2, p3, p4):
    seg1 = GC_MakeSegment(p1, p2)
    seg2 = GC_MakeSegment(p2, p3)
    seg3 = GC_MakeSegment(p3, p4)
    seg4 = GC_MakeSegment(p4, p1)
    edge1 = BRepBuilderAPI_MakeEdge(seg1.Value())
    edge2 = BRepBuilderAPI_MakeEdge(seg2.Value())
    edge3 = BRepBuilderAPI_MakeEdge(seg3.Value())
    edge4 = BRepBuilderAPI_MakeEdge(seg4.Value())
    wire = BRepBuilderAPI_MakeWire(edge1.Edge(), edge2.Edge(),
                                   edge3.Edge(), edge4.Edge())
    return wire.Wire()
    
def sewBox():
    # Length of shape (spine)
    Vec = gp_Vec(0, 0, 10)
    # starting with bot vertices, make bot wire & face
    p1 = gp_Pnt(0, 0, 0)
    p2 = gp_Pnt(20, 0, 0)
    p3 = gp_Pnt(20, 20, 0)
    p4 = gp_Pnt(0, 20, 0)
    botWire = pointsToWire(p1, p2, p3, p4)
    botFace = BRepBuilderAPI_MakeFace(botWire).Face()
    # starting with topvertices, make top face
    p5 = translatePnt(p1, Vec)
    p6 = translatePnt(p2, Vec)
    p7 = translatePnt(p3, Vec)
    p8 = translatePnt(p4, Vec)
    topWire = pointsToWire(p5, p6, p7, p8)
    topFace = BRepBuilderAPI_MakeFace(topWire).Face()
    # Make spine (wire) to make 'pipe'
    spineSeg = GC_MakeSegment(p1, p5)
    spineEdge = BRepBuilderAPI_MakeEdge(spineSeg.Value())
    spineWire = BRepBuilderAPI_MakeWire(spineEdge.Edge()).Wire()
    pipe = OCC.BRepOffsetAPI.BRepOffsetAPI_MakePipe(botWire, spineWire).Shape()
    # Sew together botFace, pipe, and topFace to get solid
    tolerance = 1e-6
    sew = OCC.BRepBuilderAPI.BRepBuilderAPI_Sewing(tolerance)
    sew.Add(botFace)
    sew.Add(pipe)
    sew.Add(topFace)
    sew.Perform()
    res = sew.SewedShape()
    print type(res)
    redraw(res)
    
def exit(event=None):
    sys.exit()

if __name__ == '__main__':
    add_menu('operations')
    add_function_to_menu('operations', makeBox)
    add_function_to_menu('operations', rotateBox)
    add_function_to_menu('operations', enableFaceSelect)
    add_function_to_menu('operations', wireProfileOnFace)
    add_function_to_menu('operations', exit)
    add_menu('Experimental')
    add_function_to_menu('Experimental', sewBox)
    
    start_display()
