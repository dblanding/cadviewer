#!/usr/bin/env python
#
# cadViewer.py
# An embryonic python 3D CAD application with very little functionality.
# Perhaps it could be a starting point for a more elaborate program.
# It may be only useful to facilitate the exploration of pythonOCC syntax.
# The latest  version of this file can be found at:
# https://sites.google.com/site/pythonocc/
#
# Author: Doug Blanding   <dblanding at gmail dot com>
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

from OCC.Core.gp import (gp_Pnt, gp_OX, gp_Vec, gp_Trsf, gp_DZ, gp_Ax2, gp_Ax3,
                         gp_Pnt2d, gp_Dir2d, gp_Ax2d)
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment
from OCC.Core.GCE2d import GCE2d_MakeSegment
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.Geom2d import Geom2d_Ellipse, Geom2d_TrimmedCurve
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge,
                                     BRepBuilderAPI_MakeWire,
                                     BRepBuilderAPI_MakeFace,
                                     BRepBuilderAPI_Transform,
                                     BRepBuilderAPI_MakeVertex)
from OCC.Core.BRepPrimAPI import (BRepPrimAPI_MakePrism,
                                  BRepPrimAPI_MakeCylinder)
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepOffsetAPI import (BRepOffsetAPI_MakeThickSolid,
                                    BRepOffsetAPI_ThruSections)
from OCC.Core.BRepLib import breplib
from OCC.Core.BRep import BRep_Builder
from OCC.Core.GeomAbs import GeomAbs_Plane
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.TopoDS import topods, topods_Wire, TopoDS_Compound
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCC.Core.TopTools import TopTools_ListOfShape

#############################################
#
#  Bottle Demo:
#
#############################################

def face_is_plane(face):
    """
    Returns True if the TopoDS_Shape is a plane, False otherwise
    """
    surf = BRepAdaptor_Surface(face, True)
    surf_type = surf.GetType()
    return surf_type == GeomAbs_Plane


def geom_plane_from_face(aFace):
    """
    Returns the geometric plane entity from a planar surface
    """
    return BRepAdaptor_Surface(aFace, True).Plane()

# Bottle Dimensions...
width = 50
height = 70
thickness = 30

def makeBottle(): # complete bottle
    startBottle(startOnly=False)

def startBottle(startOnly=True): # minus the neck fillet, shelling & threads
    partName = "Bottle-start"
    # The points we'll use to create the profile of the bottle's body
    aPnt1 = gp_Pnt(-width / 2.0, 0, 0)
    aPnt2 = gp_Pnt(-width / 2.0, -thickness / 4.0, 0)
    aPnt3 = gp_Pnt(0, -thickness / 2.0, 0)
    aPnt4 = gp_Pnt(width / 2.0, -thickness / 4.0, 0)
    aPnt5 = gp_Pnt(width / 2.0, 0, 0)

    aArcOfCircle = GC_MakeArcOfCircle(aPnt2, aPnt3, aPnt4)
    aSegment1 = GC_MakeSegment(aPnt1, aPnt2)
    aSegment2 = GC_MakeSegment(aPnt4, aPnt5)

    # Could also construct the line edges directly using the points
    # instead of the resulting line.
    aEdge1 = BRepBuilderAPI_MakeEdge(aSegment1.Value())
    aEdge2 = BRepBuilderAPI_MakeEdge(aArcOfCircle.Value())
    aEdge3 = BRepBuilderAPI_MakeEdge(aSegment2.Value())

    # Create a wire out of the edges
    aWire = BRepBuilderAPI_MakeWire(aEdge1.Edge(), aEdge2.Edge(), aEdge3.Edge())

    # Quick way to specify the X axis
    xAxis = gp_OX()

    # Set up the mirror
    aTrsf = gp_Trsf()
    aTrsf.SetMirror(xAxis)

    # Apply the mirror transformation
    aBRespTrsf = BRepBuilderAPI_Transform(aWire.Wire(), aTrsf)

    # Get the mirrored shape back out of the transformation
    # and convert back to a wire
    aMirroredShape = aBRespTrsf.Shape()

    # A wire instead of a generic shape now
    aMirroredWire = topods.Wire(aMirroredShape)

    # Combine the two constituent wires
    mkWire = BRepBuilderAPI_MakeWire()
    mkWire.Add(aWire.Wire())
    mkWire.Add(aMirroredWire)
    myWireProfile = mkWire.Wire()

    # The face that we'll sweep to make the prism
    myFaceProfile = BRepBuilderAPI_MakeFace(myWireProfile)

    # We want to sweep the face along the Z axis to the height
    aPrismVec = gp_Vec(0, 0, height)
    myBody = BRepPrimAPI_MakePrism(myFaceProfile.Face(), aPrismVec)

    # Add fillets to all edges through the explorer
    mkFillet = BRepFilletAPI_MakeFillet(myBody.Shape())
    anEdgeExplorer = TopExp_Explorer(myBody.Shape(), TopAbs_EDGE)

    while anEdgeExplorer.More():
        anEdge = topods.Edge(anEdgeExplorer.Current())
        mkFillet.Add(thickness / 12.0, anEdge)

        anEdgeExplorer.Next()

    myBody = mkFillet.Shape()
    
    
    # Create the neck of the bottle
    neckLocation = gp_Pnt(0, 0, height)
    neckAxis = gp_DZ()
    neckAx2 = gp_Ax2(neckLocation, neckAxis)

    myNeckRadius = thickness / 4.0
    myNeckHeight = height / 10.0

    mkCylinder = BRepPrimAPI_MakeCylinder(neckAx2, myNeckRadius, myNeckHeight)
    myBody = BRepAlgoAPI_Fuse(myBody , mkCylinder.Shape())
    if startOnly: # quit here
        uid = win.getNewPartUID(myBody.Shape(), name=partName)
        win.redraw()
        return
    
    partName = "Bottle-complete"
    # Our goal is to find the highest Z face and remove it
    faceToRemove = None
    zMax = -1

    # We have to work our way through all the faces to find the highest Z face
    aFaceExplorer = TopExp_Explorer(myBody.Shape(), TopAbs_FACE)
    while aFaceExplorer.More():
        aFace = topods.Face(aFaceExplorer.Current())

        if face_is_plane(aFace):
            aPlane = geom_plane_from_face(aFace)

            # We want the highest Z face, so compare this to the previous faces
            aPnt = aPlane.Location()
            aZ = aPnt.Z()
            if aZ > zMax:
                zMax = aZ
                faceToRemove = aFace

        aFaceExplorer.Next()

    facesToRemove = TopTools_ListOfShape()
    facesToRemove.Append(faceToRemove)

    myBody = BRepOffsetAPI_MakeThickSolid(myBody.Shape(), facesToRemove,
                                          -thickness / 50.0, 0.001)

    # Set up our surfaces for the threading on the neck
    neckAx2_Ax3 = gp_Ax3(neckLocation, gp_DZ())
    aCyl1 = Geom_CylindricalSurface(neckAx2_Ax3, myNeckRadius * 0.99)
    aCyl2 = Geom_CylindricalSurface(neckAx2_Ax3, myNeckRadius * 1.05)

    # Set up the curves for the threads on the bottle's neck
    aPnt = gp_Pnt2d(2.0 * math.pi, myNeckHeight / 2.0)
    aDir = gp_Dir2d(2.0 * math.pi, myNeckHeight / 4.0)
    anAx2d = gp_Ax2d(aPnt, aDir)

    aMajor = 2.0 * math.pi
    aMinor = myNeckHeight / 10.0

    anEllipse1 = Geom2d_Ellipse(anAx2d, aMajor, aMinor)
    anEllipse2 = Geom2d_Ellipse(anAx2d, aMajor, aMinor / 4.0)

    anArc1 = Geom2d_TrimmedCurve(anEllipse1, 0, math.pi)
    anArc2 = Geom2d_TrimmedCurve(anEllipse2, 0, math.pi)
    
    anEllipsePnt1 = anEllipse1.Value(0)
    anEllipsePnt2 = anEllipse1.Value(math.pi)

    aSegment = GCE2d_MakeSegment(anEllipsePnt1, anEllipsePnt2)

    # Build edges and wires for threading
    anEdge1OnSurf1 = BRepBuilderAPI_MakeEdge(anArc1, aCyl1)
    anEdge2OnSurf1 = BRepBuilderAPI_MakeEdge(aSegment.Value(), aCyl1)
    anEdge1OnSurf2 = BRepBuilderAPI_MakeEdge(anArc2, aCyl2)
    anEdge2OnSurf2 = BRepBuilderAPI_MakeEdge(aSegment.Value(), aCyl2)

    threadingWire1 = BRepBuilderAPI_MakeWire(anEdge1OnSurf1.Edge(),
                                             anEdge2OnSurf1.Edge())
    threadingWire2 = BRepBuilderAPI_MakeWire(anEdge1OnSurf2.Edge(),
                                             anEdge2OnSurf2.Edge())

    # Compute the 3D representations of the edges/wires
    breplib.BuildCurves3d(threadingWire1.Shape())
    breplib.BuildCurves3d(threadingWire2.Shape())

    # Create the surfaces of the threading
    aTool = BRepOffsetAPI_ThruSections(True)
    aTool.AddWire(threadingWire1.Wire())
    aTool.AddWire(threadingWire2.Wire())
    aTool.CheckCompatibility(False)
    myThreading = aTool.Shape()

    # Build the resulting compound
    aRes = TopoDS_Compound()
    aBuilder = BRep_Builder()
    aBuilder.MakeCompound(aRes)
    aBuilder.Add(aRes, myBody.Shape())
    aBuilder.Add(aRes, myThreading)
    uid = win.getNewPartUID(aRes, name=partName)
    win.redraw()

# Make Bottle step by step...   
def makePoints(event=None):
    global aPnt1, aPnt2, aPnt3, aPnt4, aPnt5
    aPnt1 = gp_Pnt(-width / 2. , 0 , 0)
    aPnt2 = gp_Pnt(-width / 2. , -thickness / 4. , 0)
    aPnt3 = gp_Pnt(0 , -thickness / 2. , 0)
    aPnt4 = gp_Pnt(width / 2. , -thickness / 4. , 0)
    aPnt5 = gp_Pnt(width / 2. , 0 , 0)
    V1 = BRepBuilderAPI_MakeVertex(aPnt1)
    V2 = BRepBuilderAPI_MakeVertex(aPnt2)
    V3 = BRepBuilderAPI_MakeVertex(aPnt3)
    V4 = BRepBuilderAPI_MakeVertex(aPnt4)
    V5 = BRepBuilderAPI_MakeVertex(aPnt5)
    # add dummy point above bottle just to set view size
    V6 = BRepBuilderAPI_MakeVertex(gp_Pnt(0,0,height*1.1))
    display.DisplayShape(V1.Vertex())
    display.DisplayShape(V2.Vertex())
    display.DisplayShape(V3.Vertex())
    display.DisplayShape(V4.Vertex())
    display.DisplayShape(V5.Vertex())
    display.DisplayShape(V6.Vertex())
    display.FitAll()
    display.EraseAll()
    display.DisplayShape(V1.Vertex())
    display.DisplayShape(V2.Vertex())
    display.DisplayShape(V3.Vertex())
    display.DisplayShape(V4.Vertex())
    display.DisplayShape(V5.Vertex())
    display.Repaint()
    win.statusBar().showMessage('Make Points complete')

def makeLines(event=None):
    global aEdge1, aEdge2, aEdge3
    aArcOfCircle = GC_MakeArcOfCircle(aPnt2,aPnt3 ,aPnt4)
    aSegment1 = GC_MakeSegment(aPnt1 , aPnt2)
    aSegment2 = GC_MakeSegment(aPnt4 , aPnt5)
    # Display lines
    aEdge1 = BRepBuilderAPI_MakeEdge(aSegment1.Value())
    aEdge2 = BRepBuilderAPI_MakeEdge(aArcOfCircle.Value())
    aEdge3 = BRepBuilderAPI_MakeEdge(aSegment2.Value())
    display.DisplayColoredShape(aEdge1.Edge(),'RED')
    display.DisplayColoredShape(aEdge2.Edge(),'RED')
    display.DisplayColoredShape(aEdge3.Edge(),'RED')
    display.Repaint()
    win.statusBar().showMessage('Make lines complete')

def makeHalfWire(event=None):
    global aWire
    aWire  = BRepBuilderAPI_MakeWire(aEdge1.Edge(),
                                     aEdge2.Edge(),
                                     aEdge3.Edge()).Wire()
    display.EraseAll()
    display.DisplayColoredShape(aWire, 'BLUE')
    display.Repaint()
    win.statusBar().showMessage('Make Half Wire complete')

def makeWholeWire(event=None):
    global myWireProfile
    xAxis = gp_OX()
    # Set up the mirror
    aTrsf = gp_Trsf()
    aTrsf.SetMirror(xAxis)
    # Apply the mirror transform
    aBRepTrsf = BRepBuilderAPI_Transform(aWire, aTrsf)
    # Convert mirrored shape to a wire
    aMirroredShape = aBRepTrsf.Shape()
    aMirroredWire = topods_Wire(aMirroredShape)
    # Combine the two wires
    mkWire = BRepBuilderAPI_MakeWire()
    mkWire.Add(aWire)
    mkWire.Add(aMirroredWire)
    myWireProfile = mkWire.Wire()
    display.DisplayColoredShape(myWireProfile, 'BLUE')
    display.Repaint()
    win.statusBar().showMessage('Make whole wire complete')

def makeFace(event=None):
    global myFaceProfile
    myFaceProfile = BRepBuilderAPI_MakeFace(myWireProfile)
    if myFaceProfile.IsDone():
        bottomFace = myFaceProfile.Face()
    display.DisplayShape(bottomFace, color='YELLOW', transparency=0.6)
    display.Repaint()
    win.statusBar().showMessage('Make face complete')

def makeBody(event=None):
    partName = 'body'
    aPrismVec = gp_Vec(0 , 0 , height)
    myBody = BRepPrimAPI_MakePrism(myFaceProfile.Shape(),
                                   aPrismVec).Shape()
    win.getNewPartUID(myBody, name=partName)
    win.statusBar().showMessage('Bottle body complete')
    win.redraw()
    
def makeFillets(event=None):
    newPrtName = 'bodyWithFillets'
    workPart = win.activePart
    wrkPrtUID = win.activePartUID
    mkFillet = BRepFilletAPI_MakeFillet(workPart)
    aEdgeExplorer = TopExp_Explorer(workPart,
                                    TopAbs_EDGE)
    while aEdgeExplorer.More():
        aEdge = topods_Edge(aEdgeExplorer.Current())
        mkFillet.Add(thickness / 12. , aEdge)
        aEdgeExplorer.Next()
    myBody = mkFillet.Shape()
    win.getNewPartUID(myBody, name=newPrtName, ancestor=wrkPrtUID)
    win.statusBar().showMessage('Bottle with fillets complete')
    win.redraw()
    
def addNeck(event=None):
    newPrtName = 'bodyWithNeck'
    workPart = win.activePart
    wrkPrtUID = win.activePartUID
    neckLocation = gp_Pnt(0 , 0 , height)
    neckNormal = gp_DZ()
    neckAx2 = gp_Ax2(neckLocation , neckNormal)
    myNeckRadius = thickness / 4.
    myNeckHeight = height / 10.
    MKCylinder = BRepPrimAPI_MakeCylinder(neckAx2,
                                          myNeckRadius,
                                          myNeckHeight)
    myNeck = MKCylinder.Shape()
    myBody = BRepAlgoAPI_Fuse(workPart, myNeck).Shape()
    win.getNewPartUID(myBody, name=newPrtName, ancestor=wrkPrtUID)
    win.statusBar().showMessage('Add neck complete')
    win.redraw()
