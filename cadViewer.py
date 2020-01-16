#!/usr/bin/env python
#
# This file is part of cadViewer, 
# An embryonic python 3D CAD application with very little functionality.
# Perhaps it could be a starting point for a more elaborate program.
# It may be only useful to facilitate the exploration of pythonOCC syntax.
# The latest  version of this file can be found at:
# https://github.com/dblanding/cadviewer
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


from itertools import islice
import logging
import math
import os, os.path
import sys
import rpnCalculator
import stepXD
import treelib
import workplane
from mainwindow import MainWindow, TreeView
"""
from PyQt5.QtCore import Qt, QPersistentModelIndex, QModelIndex
from PyQt5.QtGui import QIcon, QPixmap, QBrush, QColor
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QTreeWidget,
                             QMenu, QDockWidget, QDesktopWidget, QToolButton,
                             QLineEdit, QTreeWidgetItem, QAction, QDockWidget,
                             QToolBar, QFileDialog, QAbstractItemView,
                             QInputDialog, QTreeWidgetItemIterator)
"""
from PyQt5.QtWidgets import QApplication, QMenu
from PyQt5.QtGui import QIcon, QPixmap, QBrush, QColor
#imports for bottle demo
from OCC.Core.gp import (gp_Pnt, gp_OX, gp_Vec, gp_Trsf, gp_DZ, gp_Ax2, gp_Ax3,
                         gp_Pnt2d, gp_Dir2d, gp_Ax2d)
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment
from OCC.Core.GCE2d import GCE2d_MakeSegment
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.Geom2d import Geom2d_Ellipse, Geom2d_TrimmedCurve
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire,
                                     BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform,
                                     BRepBuilderAPI_MakeVertex)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder
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

from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge,
                                     BRepBuilderAPI_MakeFace,
                                     BRepBuilderAPI_MakeSolid,
                                     BRepBuilderAPI_MakeWire,
                                     BRepBuilderAPI_Sewing,
                                     BRepBuilderAPI_Transform)
from OCC.Core.BRepFill import brepfill
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.BRepPrimAPI import (BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism,
                                  BRepPrimAPI_MakeCylinder) 
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCC.Core.CPnts import CPnts_AbscissaPoint_Length
from OCC.Core.gp import (gp_Ax1, gp_Ax3, gp_Dir, gp_Lin, gp_Pln,
                         gp_Pnt, gp_Trsf, gp_Vec)
from OCC.Core.GC import GC_MakeSegment
from OCC.Core.GeomAPI import GeomAPI_IntSS
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.IntAna import IntAna_IntConicQuad
from OCC.Core.Interface import Interface_Static_SetCVal
from OCC.Core.Precision import precision_Angular, precision_Confusion
from OCC.Core.Prs3d import Prs3d_Drawer
from OCC.Core.STEPCAFControl import STEPCAFControl_Writer
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.TCollection import (TCollection_ExtendedString,
                                  TCollection_AsciiString)
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
from OCC.Core.TopoDS import (topods_Edge, topods_Face, topods_Shell,
                             topods_Vertex)
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.TopTools import TopTools_ListOfShape
from OCC.Core.Quantity import (Quantity_Color, Quantity_NOC_RED,
                               Quantity_NOC_GRAY, Quantity_NOC_BLACK,
                               Quantity_NOC_DARKGREEN)
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool,
                              XCAFDoc_DocumentTool_LayerTool,
                              XCAFDoc_DocumentTool_MaterialTool,
                              XCAFDoc_ColorSurf)
from OCCUtils import Construct, Topology
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # set to DEBUG | INFO | ERROR

TOL = 1e-7 # Linear Tolerance
ATOL = TOL # Angular Tolerance
print('TOLERANCE = ', TOL)


#############################################
#
# Workplane creation functions...
#
#############################################

        
def wpBy3Pts(*args):
    """
    Direction from pt1 to pt2 sets wDir, pt2 is wpOrigin.
    direction from pt2 to pt3 sets uDir
    """
    print(f'args = {args}')
    if win.ptStack:
        # Finish
        p3 = win.ptStack.pop()
        p2 = win.ptStack.pop()
        p1 = win.ptStack.pop()
        wVec = gp_Vec(p1, p2)
        wDir = gp_Dir(wVec)
        origin = p2
        uVec = gp_Vec(p2, p3)
        uDir = gp_Dir(uVec)
        axis3 = gp_Ax3(origin, wDir, uDir)
        wp = workplane.WorkPlane(100, ax3=axis3)
        win.getNewPartUID(wp, typ='w')
        win.clearCallback()
        statusText = "Workplane created."
        win.statusBar().showMessage(statusText)
    else:
        # Initial setup
        win.registerCallback(wpBy3PtsC)
        display.selected_shape = None
        display.SetSelectionModeVertex()
        statusText = "Pick 3 points. Dir from pt1-pt2 sets wDir, pt2 is origin."
        win.statusBar().showMessage(statusText)
        return
        
def wpBy3PtsC(shapeList, *args):  # callback (collector) for wpBy3Pts
    print(f'args = {args}')
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (len(win.ptStack) == 1):
        statusText = "Now select point 2 (wp origin)."
        win.statusBar().showMessage(statusText)
    elif (len(win.ptStack) == 2):
        statusText = "Now select point 3 to set uDir."
        win.statusBar().showMessage(statusText)
    elif (len(win.ptStack) == 3):
        wpBy3Pts()

def wpOnFace(*args):
    """ First face defines plane of wp. Second face defines uDir.
    """
    if not win.faceStack:
        win.registerCallback(wpOnFaceC)
        display.selected_shape = None
        display.SetSelectionModeFace()
        statusText = "Select face for workplane."
        win.statusBar().showMessage(statusText)
        return
    else:
        faceU = win.faceStack.pop()
        faceW = win.faceStack.pop()
        wp = workplane.WorkPlane(100, face=faceW, faceU=faceU)
        win.getNewPartUID(wp, typ='w')
        win.clearCallback()
        statusText = "Workplane created."
        win.statusBar().showMessage(statusText)
        
def wpOnFaceC(shapeList=None, *args):  # callback (collector) for wpOnFace
    if not shapeList:
        shapeList = []
    print(shapeList)
    print(args)
    for shape in shapeList:
        print(type(shape))
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (len(win.faceStack) == 1):
        statusText = "Select face for workplane U direction."
        win.statusBar().showMessage(statusText)
    elif (len(win.faceStack) == 2):
        wpOnFace()

def makeWP():   # Default workplane located in X-Y plane at 0,0,0
    wp = workplane.WorkPlane(100)
    win.getNewPartUID(wp, typ='w')
    win.redraw()

#############################################
#
# 2d Construction Line functions...
# With these methods, SetSelectionModeVertex enables selection of vertexes
# on parts, automatically projecting those onto the active Workplane.
# To select intersection points on the wp, user should change to
# SetSelectionModeShape.
#
#############################################

def clineH(initial=True):   # Horizontal construction line
    if initial:
        win.registerCallback(clineHC)
        display.SetSelectionModeVertex()
        win.ptStack = []
        win.lineEditStack = []
        win.lineEdit.setFocus()
        statusText = "Select point or enter Y-value for horizontal cline."
        win.statusBar().showMessage(statusText)
    if (win.lineEditStack or win.ptStack):
        wp = win.activeWp
        if win.ptStack:
            pnt = win.ptStack.pop()
            trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
            pnt.Transform(trsf)
            # 2d point
            p = (pnt.X(), pnt.Y())
        else:
            text = win.lineEditStack.pop()
            x = 0
            y = float(text) * win.unitscale
            p = (x,y)
        wp.hcl(p)
        win.ptStack = []
        win.redraw()
        
def clineHC(shapeList, *kwargs):  # callback (collector) for clineH
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (win.ptStack or win.lineEditStack):
        clineH(initial=False)

def clineV(initial=True):   # Vertical construction line
    if initial:
        win.registerCallback(clineVC)
        display.SetSelectionModeVertex()
        win.ptStack = []
        win.lineEditStack = []
        win.lineEdit.setFocus()
        statusText = "Select point or enter X-value for vertcal cline."
        win.statusBar().showMessage(statusText)
    if (win.lineEditStack or win.ptStack):
        wp = win.activeWp
        if win.ptStack:
            pnt = win.ptStack.pop()
            trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
            pnt.Transform(trsf)
            # 2d point
            p = (pnt.X(), pnt.Y())
        else:
            text = win.lineEditStack.pop()
            x = float(text) * win.unitscale
            y = 0
            p = (x,y)
        wp.vcl(p)
        win.ptStack = []
        win.redraw()
        
def clineVC(shapeList, *kwargs):  # callback (collector) for clineV
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (win.ptStack or win.lineEditStack):
        clineV(initial=False)

def clineHV(initial=True):   # Horizontal + Vertical construction lines
    if initial:
        win.registerCallback(clineHVC)
        display.SetSelectionModeVertex()
        win.ptStack = []
        win.lineEditStack = []
        win.lineEdit.setFocus()
        statusText = "Select point or enter x,y coords for H+V cline."
        win.statusBar().showMessage(statusText)
    if (win.lineEditStack or win.ptStack):
        wp = win.activeWp
        if win.ptStack:
            pnt = win.ptStack.pop()
            trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
            pnt.Transform(trsf)
            # 2d point
            p = (pnt.X(), pnt.Y())
        else:
            strx, stry = win.lineEditStack.pop().split(',')
            x = float(strx) * win.unitscale
            y = float(stry) * win.unitscale
            p = (x,y)
        wp.hvcl(p)
        win.ptStack = []
        win.redraw()
        
def clineHVC(shapeList, *kwargs):  # callback (collector) for clineHV
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (win.ptStack or win.lineEditStack):
        clineHV(initial=False)

def cline2Pts(initial=True):
    if initial:
        win.registerCallback(cline2PtsC)
        display.SetSelectionModeVertex()
        win.ptStack = []
        statusText = "Select 2 points for Construction Line."
        win.statusBar().showMessage(statusText)
    if len(win.ptStack) == 2:
        wp = win.activeWp
        p2 = win.ptStack.pop()
        p1 = win.ptStack.pop()
        trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
        p1.Transform(trsf)
        p2.Transform(trsf)
        # 2d points
        pnt1 = (p1.X(), p1.Y())
        pnt2 = (p2.X(), p2.Y())
        wp.acl(pnt1, pnt2)
        win.ptStack = []
        win.redraw()
        
def cline2PtsC(shapeList, *kwargs):  # callback (collector) for cline2Pts
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if len(win.ptStack) == 2:
        cline2Pts(initial=False)

def clineAng(initial=True):
    if initial:
        win.registerCallback(clineAngC)
        display.SetSelectionModeVertex()
        display.SetSelectionModeShape()
        win.ptStack = []
        win.floatStack = []
        win.lineEditStack = []
        win.lineEdit.setFocus()
        statusText = "Select point on WP (or enter x,y coords) then enter angle."
        win.statusBar().showMessage(statusText)
    if (win.ptStack and win.lineEditStack):
        wp = win.activeWp
        text = win.lineEditStack.pop()
        angle = float(text)
        p = win.ptStack.pop()
        trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
        p.Transform(trsf)
        pnt = (p.X(), p.Y()) # 2D point
        wp.acl(pnt, ang=angle)
        win.ptStack = []
        win.redraw()
    elif len(win.lineEditStack) == 2:
        wp = win.activeWp
        angtext = win.lineEditStack.pop()
        angle = float(angtext)
        pnttext = win.lineEditStack.pop()
        if ',' in pnttext:
            strx, stry = pnttext.split(',')
            x = float(strx) * win.unitscale
            y = float(stry) * win.unitscale
            pnt = (x,y)
            wp.acl(pnt, ang=angle)
            win.ptStack = []
            win.redraw()

def clineAngC(shapeList, *kwargs):  # callback (collector) for clineAng
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (win.ptStack and win.lineEditStack):
        clineAng(initial=False)
    if len(win.lineEditStack) == 2:
        clineAng(initial=False)
    
def clineRefAng():
    pass

def clineAngBisec(initial=True):
    pass

def clineLinBisec(initial=True):
    if initial:
        win.registerCallback(clineLinBisecC)
        display.SetSelectionModeVertex()
    if len(win.ptStack) == 2:
        wp = win.activeWp
        p2 = win.ptStack.pop()
        p1 = win.ptStack.pop()
        trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
        p1.Transform(trsf)
        p2.Transform(trsf)
        # 2d points
        pnt1 = (p1.X(), p1.Y())
        pnt2 = (p2.X(), p2.Y())
        wp.lbcl(pnt1, pnt2)
        win.ptStack = []
        win.redraw()
        
def clineLinBisecC(shapeList, *kwargs):  # callback (collector) for clineLinBisec
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if len(win.ptStack) == 2:
        clineLinBisec(initial=False)

def clinePara():
    pass

def clinePerp():
    pass

def clineTan1():
    pass

def clineTan2():
    pass

def ccirc():
    pass

#############################################
#
# 2d Geometry Line functions...
#
#############################################

def makeWireCircle(initial=True):
    if initial:
        win.registerCallback(makeWireCircleC)
        display.SetSelectionModeVertex()
        display.SetSelectionModeShape() #This allows selection of intersection points
    if win.ptStack:
        wp = win.activeWp
        p1 = win.ptStack.pop()
        trsf = wp.Trsf.Inverted()  # New transform. Don't invert wp.Trsf
        p1.Transform(trsf)
        pnt = (p1.X(), p1.Y())  # 2d point
        win.activeWp.circ(pnt, 10)
        win.ptStack = []
        win.clearCallback()
        
def makeWireCircleC(shapeList, *kwargs):  # callback (collector) for makeWireCircle
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if win.ptStack:
        makeWireCircle(initial=False)

def geom():
    pass

#############################################
#
# 3D Geometry creation functions...
#
#############################################

def makeBox():
    name = 'Box'
    myBody = BRepPrimAPI_MakeBox(60,60,50).Shape()
    uid = win.getNewPartUID(myBody, name=name)
    win.redraw()
    
def makeCyl():
    name = 'Cylinder'
    myBody = BRepPrimAPI_MakeCylinder(40,80).Shape()
    uid = win.getNewPartUID(myBody, name=name)
    win.redraw()
    
#############################################
#
# 3D Geometry positioning functons...
#
#############################################

def rotateAP():
    aisShape = AIS_Shape(win.activePart)
    ax1 = gp_Ax1(gp_Pnt(0., 0., 0.), gp_Dir(1., 0., 0.))
    aRotTrsf = gp_Trsf()
    angle = math.pi/18 # 10 degrees
    aRotTrsf.SetRotation(ax1, angle)
    aTopLoc = TopLoc_Location(aRotTrsf)
    win.activePart.Move(aTopLoc)
    win.redraw()
    return

#############################################
#
# 3D Geometry modification functons...
#
#############################################

def hole(initial=True):
    if initial:
        win.registerCallback(holeC)
        display.SetSelectionModeVertex()
        display.SetSelectionModeShape()
        statusText = "Select location of hole then specify hole radius."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.ptStack):
        text = win.lineEditStack.pop()
        holeR = float(text)
        pnt = win.ptStack.pop()
        holeCyl = BRepPrimAPI_MakeCylinder(holeR, 100).Shape()
        # Transform to put holeCyl in -Z direction
        origin = gp_Pnt(0,0,0)
        wDir = gp_Dir(0,0,-1)   # -Z direction
        uDir = gp_Dir(1,0,0)
        ax3 = gp_Ax3(origin, wDir, uDir)          
        mTrsf = gp_Trsf()
        mTrsf.SetTransformation(ax3)
        topLoc = TopLoc_Location(mTrsf)
        holeCyl.Move(topLoc)
        # Move holeCyl from global origin to wp origin
        wp = win.activeWp
        aTopLoc = TopLoc_Location(wp.Trsf)
        holeCyl.Move(aTopLoc)
        # Move holeCyl from wp origin to selected pnt
        aVec = gp_Vec(wp.origin, pnt)
        aTrsf = gp_Trsf()
        aTrsf.SetTranslation(aVec)
        bTopLoc = TopLoc_Location(aTrsf)
        holeCyl.Move(bTopLoc)
        # Subtract holeCyl from win.activePart
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        newPart = BRepAlgoAPI_Cut(workPart, holeCyl).Shape()
        uid = win.getNewPartUID(newPart, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Hole operation complete')
        win.clearCallback()
        win.redraw()

def holeC(shapeList, *kwargs):  # callback (collector) for hole
    print(shapeList)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (win.ptStack and win.lineEditStack):
        hole(initial=False)

def fillet(initial=True):
    if initial:
        win.registerCallback(filletC)
        display.SetSelectionModeEdge()
        statusText = "Select edge(s) to fillet then specify fillet radius."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.edgeStack):
        text = win.lineEditStack.pop()
        filletR = float(text)
        edges = []
        for edge in win.edgeStack:
            edges.append(edge)
        win.edgeStack = []
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        mkFillet = BRepFilletAPI_MakeFillet(workPart)
        for edge in edges:
            mkFillet.Add(filletR , edge)
        newPart = mkFillet.Shape()
        win.getNewPartUID(newPart, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Fillet operation complete')
        win.clearCallback()
        
def filletC(shapeList, *kwargs):  # callback (collector) for fillet
    print(shapeList)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        edge = topods_Edge(shape)
        win.edgeStack.append(edge)
    if (win.edgeStack and win.lineEditStack):
        fillet(initial=False)

def shell(initial=True):
    if initial:
        win.registerCallback(shellC)
        display.SetSelectionModeFace()
        statusText = "Select face(s) to remove then specify shell thickness."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.faceStack):
        text = win.lineEditStack.pop()
        faces = TopTools_ListOfShape()
        for face in win.faceStack:
            faces.Append(face)
        win.faceStack = []
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        shellT = float(text)
        newPart = BRepOffsetAPI_MakeThickSolid(workPart, faces, -shellT, 1.e-3).Shape()
        win.getNewPartUID(newPart, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Shell operation complete')
        win.clearCallback()

def shellC(shapeList, *kwargs):  # callback (collector) for shell
    print(shapeList)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        shell(initial=False)

def lift(initial=True):
    if initial:
        win.registerCallback(liftC)
        display.SetSelectionModeFace()
        statusText = "Select face to offset and specify (+)offset distance."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.faceStack):
        text = win.lineEditStack.pop()
        dist = float(text)
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        face = win.faceStack.pop()
        norm = Construct.face_normal(face)
        liftVec = Construct.dir_to_vec(norm).Scaled(dist)
        toolBody = BRepPrimAPI_MakePrism(face, liftVec).Shape()
        join = BRepAlgoAPI_Fuse(workPart, toolBody)
        if join.IsDone():
            fused = join.Shape()
            join.Destroy()
        merged = mergePart(fused)
        win.getNewPartUID(merged, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Lift operation complete')
        win.clearCallback()

def liftC(shapeList, *kwargs):  # callback (collector) for lift
    print(shapeList)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        lift(initial=False)

#############################################
#
# 3D Dynamic Geometry Modification functons...
#
#############################################

def pointsToWire(orderedPointList): # returns wire from an ordered list of pts
    OPL = orderedPointList
    segList = []
    for i in range(len(OPL)-1):
        segList.append(GC_MakeSegment(OPL[i], OPL[i+1]))
    segList.append(GC_MakeSegment(OPL[-1], OPL[0]))
    EL = [] # Ordered List of edges
    for seg in segList:
        EL.append(BRepBuilderAPI_MakeEdge(seg.Value()).Edge())
    if len(EL)<5:
        wire = BRepBuilderAPI_MakeWire(*EL) # Only accepts up to 4 edges
    else:
        wire = BRepBuilderAPI_MakeWire(*EL[:4])
        for edge in EL[4:]:
            wire.Add(edge)
    return wire.Wire()

def face_is_plane(face):
    """
    Returns True if the TopoDS_Shape is a plane, False otherwise
    """
    hs = BRep_Tool_Surface(face)
    downcast_result = Handle_Geom_Plane.DownCast(hs)
    # The handle is null if face is not planar
    if downcast_result.IsNull():
        return False
    else:
        return True

def planeOfFace(face): # return plane of face
    surface = BRep_Tool_Surface(face) # type: Handle_Geom_Surface
    plane = Handle_Geom_Plane.DownCast(surface).GetObject() # type: Geom_Plane
    pln = plane.Pln() # type: gp_Pln
    return pln

def intersectPnt(line, pln): # return intersection pt of line with plane
    inters = IntAna_IntConicQuad(line, pln, precision_Angular(), precision_Confusion())
    if inters.IsDone:
        if inters.NbPoints() > 0: # expect value = 1
            return inters.Point(1) # only want 1 point anyway

def edgeOnFaceP(edge, face): # edge matches one of the edges of face (predicate)
    # edge and face are not neccesarily on same solid
    GeomCurve, first, last = BRep_Tool.Curve(edge)
    P1 = GeomCurve.GetObject().Value(first) # type: gp_Pnt
    P2 = GeomCurve.GetObject().Value(last) # type: gp_Pnt
    gpVec = gp_Vec(P1, P2)
    gpDir = gp_Dir(gpVec)
    line = gp_Lin(P1, gpDir)
    topo = Topology.Topo(face)
    edges = topo.edges_from_face(face)
    match = False
    for e in edges:
        vertices = topo.vertices_from_edge(e)
        p1 = BRep_Tool().Pnt(next(vertices))
        p2 = BRep_Tool().Pnt(next(vertices))
        if ((line.Distance(p1) < TOL) and (line.Distance(p2) < TOL)):
            match = True
            break
    return match

def makeToolBody(mFace, workPart, tSurf):
    # Make toolBody on mFace (of active part) to target surface.
    # Construct side faces directly by extending adjacent faces of workPart
    # Construct target face. Sew all faces together.
    
    # type(tSurf) = Handle_Geom_Surface
    tPlane = Handle_Geom_Plane.DownCast(tSurf).GetObject() # type: Geom_Plane
    tPln = tPlane.Pln() # type: gp_Pln
    
    topo = Topology.Topo(workPart)
    mF_wires = topo.wires_from_face(mFace)
    if topo.number_of_wires_from_face(mFace) > 1:
        print('Not yet implemented for faces with holes.')
        return
    else: # Only one wire in mFace
        pass
    mF_wire = next(mF_wires)
    mF_vrtxList = [] # ordered list of vertices of mFace
    for vrtx in topo.ordered_vertices_from_wire(mF_wire):
        mF_vrtxList.append(vrtx)
        
    mF_edgeList = [] # ordered list of edges of mFace
    nrEdges = 0
    for edge in topo.ordered_edges_from_wire(mF_wire):
        mF_edgeList.append(edge)
        nrEdges += 1
    print('Number of edges on mFace = ', nrEdges)

    # make an ordered list of faces adjacent to mFace
    faces = topo.faces_from_solids(workPart) # all faces
    adjFacesDict = {} # key=seq : value=face
    for face in faces:
        edges = topo.edges_from_face(face)
        if face.IsSame(mFace):
            print('Found mFace')
        else:
            adjacentFace = False # assume face is not adjacent...
            for e in edges:
                seq = 0 # keep track of which edge in ordered list is matched
                for f in mF_edgeList:
                    seq += 1
                    if e.IsSame(f): # common edge
                        adjacentFace = True # until it is discovered
                        break
                if adjacentFace:
                    break
            if adjacentFace:
                print('found adjacent face at sequence %i' % seq)
                adjFacesDict[seq] = face
    mF_adjFaceList = []
    for key in sorted(adjFacesDict):
        mF_adjFaceList.append(adjFacesDict[key]) # ordered list of adjacent faces

    newFaceList = []

    # CASE 1: ToolBody has one (closed loop) side face
    if len(mF_adjFaceList) == 1: # Only one face adjacent to mface (must be closed)
        loopEdges = []
        conicalSurf = BRep_Tool_Surface(mF_adjFaceList[0])
        baseSurf = BRep_Tool_Surface(mFace)
        for surf in (baseSurf, tSurf):
            inters = GeomAPI_IntSS()
            inters.Perform(conicalSurf, surf, 1.0e-7)
            if inters.IsDone():
                nbLines = inters.NbLines()
                curve = inters.Line(nbLines) # type: Handle_Geom_curve
                edge = BRepBuilderAPI_MakeEdge(curve).Edge()
                loopEdges.append(edge)
        sideFace = brepfill.Face(loopEdges[0], loopEdges[1])
        newFaceList.append(sideFace)
        newEdgeList = [loopEdges[1]]

    # CASE 2: ToolBody has several planar side faces
    else:
        # Make an ordered list of corner points where toolBody intersects tPlane
        newPntList = []
        for vrtx in mF_vrtxList: # for each vertex of mFace
            edgs = topo.edges_from_vertex(vrtx)
            for edg in edgs: # for each edge connected to vertex
                edgeInFace = False # assume edge is not in face
                for e in mF_edgeList:
                    if edg.IsSame(e): # until discovered that it is
                        edgeInFace = True
                if not edgeInFace: # edge is between 2 adjacent faces
                    pList = [] # end points of edge
                    for vrtx in topo.vertices_from_edge(edg):
                        pList.append(BRep_Tool().Pnt(vrtx))
                    gpvec = gp_Vec(pList[0], pList[1])
                    gpdir = gp_Dir(gpvec)
                    line = gp_Lin(pList[0], gpdir)
                    Pnt = intersectPnt(line, tPln)
                    # For some reason, I'm getting 6 edges at each vertex
                    # Throw out duplicate points
                    try:
                        prevPnt = newPntList[-1]
                        if (Pnt.Distance(prevPnt) > TOL):
                            newPntList.append(Pnt)
                    except:
                        newPntList.append(Pnt)
        
        print('Length of mF_vrtxList= ', len(mF_vrtxList))
        print('Length of newPointList= ', len(newPntList))
        
        # make new side faces of toolBody
        newEdgeList = []
        for i in range(nrEdges):
            face = mF_adjFaceList[i]
            surf = BRep_Tool_Surface(face)
            # find curve at intersection of surf with tSurf
            inters = GeomAPI_IntSS()
            inters.Perform(surf, tSurf, 1.0e-7)
            if inters.IsDone():
                nbLines = inters.NbLines()
                if not nbLines:
                    print('Unable to find intersection with target plane')
                    # Get this when trying to align a face on a 'toolBody' part
                curve = inters.Line(nbLines) # type: Handle_Geom_curve
                if nrEdges == 1: # Closed cylindrical face. Done!
                    newEdge = BRepBuilderAPI_MakeEdge(curve).Edge()
                else:
                    # more than one edge needed to enclose face
                    if face_is_plane(face):
                        if (i < (nrEdges-1)):
                            newSegment = GC_MakeSegment(newPntList[i], newPntList[i+1])
                        else:
                            newSegment = GC_MakeSegment(newPntList[i], newPntList[0])
                    newEdge = BRepBuilderAPI_MakeEdge(newSegment.Value()).Edge()
                newEdgeList.append(newEdge)
            newFace = brepfill.Face(mF_edgeList[i], newEdge)
            newFaceList.append(newFace)

    # make a new base face on mFace
    baseFace = mFace.Reversed()
                
    # make new face on tPlane
    nrEdges = len(newEdgeList)
    print('Number of New Edges = ', nrEdges)
    if (nrEdges == 1):
        newWire = BRepBuilderAPI_MakeWire(newEdgeList[0]).Wire()
    else:
        newWire = pointsToWire(newPntList)
    newFace = BRepBuilderAPI_MakeFace(newWire).Face()
    
    # sew all the faces together
    sew = BRepBuilderAPI_Sewing(TOL)
    sew.Add(baseFace)
    for sideFace in newFaceList:
        sew.Add(sideFace)
    sew.Add(newFace)
    sew.Perform()
    shape = sew.SewedShape()
    shell = topods_Shell(shape)
    makeSolid = BRepBuilderAPI_MakeSolid()
    makeSolid.Add(shell)
    solid = makeSolid.Solid()
    return solid
                
def tweak(mFace, tFace):
    # Align move face (on active part) to target face
    # All other faces remain in their original planes.
    # Only works if all adjacent faces are planar.
    """
    The algorithm is to first find the four vertices of mFace (to be moved) then
    at each vertex, identify the edge that is *not* contained in mFace. The
    intersection of each of these edges with the plane of tFace is a new vertex.
    The mFace is replaced by a new face defined by the four new vertices.
    The adjacent faces are stretched to the new vertices, remaining in their
    initial planes. The part is then sewn back together.
    """
    tSurf = BRep_Tool_Surface(tFace) # Handle_Geom_Surface
    tPlane = Handle_Geom_Plane.DownCast(tSurf).GetObject() # type: Geom_Plane
    tPln = tPlane.Pln() # type: gp_Pln
    workPart = win.activePart
    topo = Topology.Topo(workPart)
    edgeList = [] # edges of face to be moved
    for edge in topo.edges_from_face(mFace):
        edgeList.append(edge)
    wires = topo.wires_from_face(mFace)
    for wire in wires: # assuming there is only one wire
        oldVertices = topo.ordered_vertices_from_wire(wire)
    oldVrtxList = [] # ordered list of vertices of mFace
    for vrtx in oldVertices:
        oldVrtxList.append(vrtx)
    
    # Find new points (which will become the vertices of moved mFace)
    newPntList = [] # also ordered to corespond with oldVrtxList
    for vrtx in oldVrtxList: # for each vertex of mFace
        edgs = topo.edges_from_vertex(vrtx)
        for edg in edgs: # for each edge connected to vertex
            edgeInFace = False # assume edge is not in face
            for e in edgeList:
                if (hash(edg) == hash(e)): # until discovered that it is
                    edgeInFace = True
            if not edgeInFace: # edge between 2 adjacent faces
                pList = [] # end points of edge
                for vrtx in topo.vertices_from_edge(edg):
                    pList.append(BRep_Tool().Pnt(vrtx))
                gpvec = gp_Vec(pList[0], pList[1])
                gpdir = gp_Dir(gpvec)
                line = gp_Lin(pList[0], gpdir)
                newPntList.append(intersectPnt(line, tPln))
                break

    print('number of new points = ', len(newPntList))
    '''
    for i in range(len(newPntList)):
        P = newPntList[i]
        display.DisplayShape(P)
        pstring = "P%i" % i
        display.DisplayMessage(P, pstring)
    '''
    # sort through all the part's faces and stretch the adjacent ones        
    faces = topo.faces_from_solids(workPart) # all faces
    adjFaces = [] # Adjacent faces (stretched)
    otherFaces = [] # Other faces (to be reused unchanged)
    for face in faces:
        edges = topo.edges_from_face(face)
        if face == mFace:
            pass # This is the face to be moved
        else:
            adjacentFace = False # assume face is not adjacent...
            for e in edges:
                for f in edgeList:
                    if (hash(e) == hash(f)): # common edge
                        adjacentFace = True # until discovered that it is
            if adjacentFace:
                wires = topo.wires_from_face(face)
                wireList = []
                for wire in wires:
                    wireList.append(wire)
                outerWire = wireList.pop(0)
                orderedVertices = topo.ordered_vertices_from_wire(outerWire)
                orderedPtList = []
                for vrtx in orderedVertices:
                    pnt = BRep_Tool().Pnt(vrtx)
                    for i in range(len(oldVrtxList)):
                        if (hash(vrtx) == hash(oldVrtxList[i])): # common vertex
                            pnt = newPntList[i]
                    orderedPtList.append(pnt)
                orderedPtList.reverse() # need to do this for faces with holes
                stretchedWire = pointsToWire(orderedPtList)
                makeFace = BRepBuilderAPI_MakeFace(stretchedWire)
                for wire in wireList:
                    makeFace.Add(wire)
                if makeFace.IsDone():
                    stretchedFace = makeFace.Face()
                    adjFaces.append(stretchedFace)
            else:
                otherFaces.append(face)

    # make newFace to replace mFace
    newWire = pointsToWire(newPntList)
    makeFace = BRepBuilderAPI_MakeFace(newWire)
    if makeFace.IsDone():
        newFace = makeFace.Face()
    
    # sew all the faces together
    sew = BRepBuilderAPI_Sewing(TOL)
    
    print('Number of other faces: ', len(otherFaces))
    for f in otherFaces:
        sew.Add(f)
    
    for f in adjFaces:
        sew.Add(f)
    sew.Add(newFace)
    sew.Perform()
    shape = sew.SewedShape()
    shell = topods_Shell(shape)
    makeSolid = BRepBuilderAPI_MakeSolid()
    makeSolid.Add(shell)
    solid = makeSolid.Solid()
    return solid

def offsetFace(initial=True):
    """
    Offset a selected face on the active part in its normal direction.
    This method builds a toolbody on the selected face, then fuses
    it to the workpart. 
    """
    
    if initial:
        win.registerCallback(offsetFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move and enter offset distance."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.faceStack):
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        text = win.lineEditStack.pop()
        value = float(text) * win.unitscale
        mFace = win.faceStack.pop() # face to be moved
        # build and position target face
        tFace = BRepBuilderAPI_MakeFace(mFace).Face()
        faceNormal = Construct.face_normal(mFace)
        vctr = gp_Vec(faceNormal).Multiplied(value)
        trsf = gp_Trsf()
        trsf.SetTranslation(vctr)
        '''
        tFace.Move(TopLoc_Location(trsf))
        '''
        brep_trns = BRepBuilderAPI_Transform(tFace, trsf)
        shape = brep_trns.Shape()
        tFace = topods.Face(shape)
        tSurf = BRep_Tool_Surface(tFace) # Handle_Geom_Surface
        toolBody = makeToolBody(mFace, workPart, tSurf)
        fused = BRepAlgoAPI_Fuse(workPart, toolBody).Shape()
        merged = mergePart(fused)
        win.getNewPartUID(merged, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Offset Face operation complete')
        win.clearCallback()

def offsetFaceC(shapeList, *kwargs):  # callback (collector) for offsetFace
    print(shapeList)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        offsetFace(initial=False)

def alignFace(initial=True):
    """
    Align a selected face on the active part to some other face.
    This method builds a toolbody on the selected face, then fuses
    it to the workpart. 
    """
    
    if initial:
        win.registerCallback(alignFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        tFace = win.faceStack.pop() # target face (to be aligned to)
        tSurf = BRep_Tool_Surface(tFace) # Handle_Geom_Surface
        mFace = win.faceStack.pop() # face to be moved
        toolBody = makeToolBody(mFace, workPart, tSurf)
        fused = BRepAlgoAPI_Fuse(workPart, toolBody).Shape()
        merged = mergePart(fused)
        win.getNewPartUID(merged, ancestor=wrkPrtUID)

        win.statusBar().showMessage('Align Face operation complete')
        win.clearCallback()
        
def alignFaceC(shapeList, *kwargs):  # callback (collector) for alignFace
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if len(win.faceStack) == 1:
        statusText = "Select face to align to."
        win.statusBar().showMessage(statusText)
    if len(win.faceStack) == 2:
        alignFace(initial=False)

def tweakFace(initial=True):
    """
    Align a selected face on the active part to some other face.
    This method modifies the workPart directly, rather than building a
    toolbody and fusing it to the workPart. 
    """
    
    if initial:
        win.registerCallback(tweakFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        tFace = win.faceStack.pop() # target face (to be aligned to)
        mFace = win.faceStack.pop() # face to be moved
        tb = tweak(mFace, tFace)
        win.getNewPartUID(tb)
        win.statusBar().showMessage('Align Face operation complete')
        win.clearCallback()
        
def tweakFaceC(shapeList, *kwargs):  # callback (collector) for tweakFace
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if len(win.faceStack) == 1:
        statusText = "Select face to align to."
        win.statusBar().showMessage(statusText)
    if len(win.faceStack) == 2:
        tweakFace(initial=False)

def fuse(initial=True): # Fuse two parts
    if initial:
        win.registerCallback(fuseC)
        display.SetSelectionModeFace()
        display.SetSelectionModeShape()
        statusText = "Select first shape to fuse."
        win.statusBar().showMessage(statusText)
    elif len(win.shapeStack) == 2:
        shape2 = win.shapeStack.pop()
        shape1 = win.shapeStack.pop()
        fused = BRepAlgoAPI_Fuse(shape1, shape2).Shape()
        res = mergePart(fused)
        win.getNewPartUID(res)
        win.statusBar().showMessage('Fuse operation complete')
        win.clearCallback()
        
def fuseC(shapeList, *kwargs):  # callback (collector) for fuse
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        win.shapeStack.append(shape)
    if len(win.shapeStack) == 1:
        statusText = "Select second part to fuse."
        win.statusBar().showMessage(statusText)
    if len(win.shapeStack) == 2:
        fuse(initial=False)

def remFace(initial=True): # remove face (of active part)
    if initial:
        win.registerCallback(remFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to remove."
        win.statusBar().showMessage(statusText)
    elif win.faceStack:
        rface = win.faceStack.pop() # face to remove
        workPart = win.activePart
        topo = Topology.Topo(workPart)
        faceList = []
        for face in topo.faces_from_solids(workPart): # all faces
            if not face == rface:
                faceList.append(face)
        
        # sew all the faces together
        sew = BRepBuilderAPI_Sewing(TOL)
        print('Number of faces to begin: ', topo.number_of_faces_from_solids(workPart))
        print('Number of faces after removal: ', len(faceList))
        for f in faceList:
            sew.Add(f)
        sew.Perform()
        res = sew.SewedShape()
        win.getNewPartUID(res)
        win.statusBar().showMessage('Face Removal operation complete')
        win.clearCallback()
        
def remFaceC(shapeList, *kwargs):  # callback (collector) for remFace
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if win.faceStack:
        remFace(initial=False)

def mergePlanarFaces(rEdge, face1, face2, solid):
    """
    This operation combines 2 adjacent coplanar faces (face1 & face2) of
    solid into one new face and returns that face.
    Shared edge (rEdge) is removed and any short colinear edges around
    the perimeter of the new face are merged.
    """
    topo = Topology.Topo(solid)
    # find ordered points going ccw around face1 loop
    f1wires = topo.wires_from_face(face1)
    f1wire =next(f1wires)
    f1vertcs = topo.ordered_vertices_from_wire(f1wire)
    f1pnts = [BRep_Tool().Pnt(vrtx) for vrtx in f1vertcs]
    # find ordered points going ccw around face2 loop
    f2wires = topo.wires_from_face(face2)
    f2wire =next(f2wires)
    f2vertcs = topo.ordered_vertices_from_wire(f2wire)
    f2pnts = [BRep_Tool().Pnt(vrtx) for vrtx in f2vertcs]
    # find indices of pts common to both loops (where loops join)
    L1i = []
    L2i = []
    for i in range(len(f1pnts)):
        for j in range(len(f2pnts)):
            if f1pnts[i] == f2pnts[j]:
                #print '%i <==> %i' % (j,i)
                L1i.append(i)
                L2i.append(j)
    # Combine the 2 loops into one big loop, minus the removed edge.
    # Concatanate ordered pnts around face1, then face 2, going ccw.
    # Start a new list at one of the joining points on loop 1.
    # The next point in the list will be the next point in loop 1.
    # If the next point is the other joining point of loop 1,
    # Start with the other joining point instead.
    indx = L1i[0]
    strt = f1pnts[indx]
    try:
        nxti = indx + 1
        nxt = f1pnts[nxti]
    except IndexError:
        nxti = 0
    if (nxti == L1i[1]):
        L1StartIndex = L1i[1]
        L2StartIndex = L2i[0]
    else:
        L1StartIndex = L1i[0]
        L2StartIndex = L2i[1]
    L1StopIndex = L1StartIndex + (len(f1pnts) - 1)
    L2StopIndex = L2StartIndex + (len(f2pnts) - 1)
    # To allow wrapping around the end of the list, double the pnt list
    PL = list(islice((f1pnts * 2), L1StartIndex, L1StopIndex))
    PL = PL + list(islice((f2pnts * 2), L2StartIndex, L2StopIndex))
    #print 'Initial length of point list of new face = ', len(PL)
    # Remove 'extra' points (not needed) to define wire
    PLE = PL + PL[:2] # Pnt List (Extended) to allow indexing to i+2
    extraPnts = []
    for i in range(len(PL)):
        # line defined by straddling points
        gpVec = gp_Vec(PLE[i], PLE[i+2])
        gpDir = gp_Dir(gpVec)
        line = gp_Lin(PLE[i], gpDir)
        # does PLE[i+1] lie on line?
        if (line.Distance(PLE[i+1]) < TOL):
            extraPnts.append(PLE[i+1])
    for pnt in extraPnts:
        PL.remove(pnt)
    #print 'Reduced length of point list of new face = ', len(PL)
    
    newWire = pointsToWire(PL)
    makeFace = BRepBuilderAPI_MakeFace(newWire)
    if makeFace.IsDone():
        mergedFace = makeFace.Face()
    return mergedFace        
        
def mergePart(workPart=None):
    """
    After a Boolean fuse operation, the faces of the resulting part still
    contain the edges of the original parts prior to being fused.
    This operation explores the workPart to find any adjacent faces with
    the same underlying surface (planar or conic).
    Those faces are combined into a larger face with the formerly shared
    edge removed. Also, short colinear edges of the new faces are merged.
    If the found faces are not planar, they are assumed to be conical and
    the conical face is reconstructed without the shared edge.
    """
    if not workPart:
        workPart = win.activePart
    topo = Topology.Topo(workPart)
    faceList = []
    planarFaceRepairList = []
    conicFaceRepairList = []
    for face in topo.faces_from_solids(workPart):
        faceList.append(face)
    
    for i, f1 in enumerate(faceList):
        norm1 = Construct.face_normal(f1)
        for f2 in faceList[i+1:]:
            norm2 = Construct.face_normal(f2)
            if norm1.IsEqual(norm2, ATOL):
                f1eList = []
                f2eList = []
                for edge in topo.edges_from_face(f1):
                    f1eList.append(edge)
                for edge in topo.edges_from_face(f2):
                    f2eList.append(edge)
                for e1 in f1eList:
                    for e2 in f2eList:
                        if e1.IsSame(e2):
                            if face_is_plane(f1):
                                planarFaceRepairList.append([[f1, f2], e1])
                                break
                            else: # face is conical
                                conicFaceRepairList.append([[f1, f2], e1])
                                
    # Replace coplanar face pairs with merged faces
    if planarFaceRepairList:
        print('Number of faces to repair: ', len(planarFaceRepairList))
        for facePair, edge in planarFaceRepairList:
            for face in facePair:
                faceList.remove(face)
            mergedFace = mergePlanarFaces(edge, facePair[0], facePair[1], workPart)
            faceList.append(mergedFace)

    # Replace conical face pair with merged face
    if conicFaceRepairList:
        for facePair, edge in conicFaceRepairList:
            curveList = []
            for face in facePair:
                faceList.remove(face)
                edges = topo.edges_from_face(face)
                for e in edges:
                    hCurve, umin, umax = BRep_Tool.Curve(e)
                    curve = hCurve.GetObject()
                    vectr = curve.DN(0.0, 2)
                    # collect only curved edges (but not shared edge)
                    if vectr.Magnitude(): # is curved
                        if not edge.IsSame(e): # not shared edge
                            curveList.append(hCurve)
            
            # construct a face between the two curves in curveList
            newEdgeList = [BRepBuilderAPI_MakeEdge(c).Edge() for c in curveList]
            newConicFace = brepfill.Face(newEdgeList[0], newEdgeList[1])
            faceList.append(newConicFace)
        
    # sew all the faces together
    sew = BRepBuilderAPI_Sewing(TOL)
    for f in faceList:
        sew.Add(f)
    sew.Perform()
    res = sew.SewedShape()
    shell = topods_Shell(res)
    makeSolid = BRepBuilderAPI_MakeSolid()
    makeSolid.Add(shell)
    solid = makeSolid.Solid()
    return solid

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
    startBottle(complete=True)

def startBottle(complete=False): # minus the neck fillet, shelling & threads
    complete = complete
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

    # Could also construct the line edges directly using the points instead of the resulting line
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

    # Get the mirrored shape back out of the transformation and convert back to a wire
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
    if not complete: # quit here
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

    myBody = BRepOffsetAPI_MakeThickSolid(myBody.Shape(), facesToRemove, -thickness / 50.0, 0.001)

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

    threadingWire1 = BRepBuilderAPI_MakeWire(anEdge1OnSurf1.Edge(), anEdge2OnSurf1.Edge())
    threadingWire2 = BRepBuilderAPI_MakeWire(anEdge1OnSurf2.Edge(), anEdge2OnSurf2.Edge())

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
    
#############################################
#
#  Info & Utility functions:
#
#############################################

def topoDumpAP():
    Topology.dumpTopology(win.activePart)
        
def printCurrUID():
    print(win._currentUID)

def printActiveAsyInfo():
    print(f"Name: {win.activeAsy}")
    print(f"UID: {win.activeAsyUID}")

def printActiveWpInfo():
    print(f"Name: {win.activeWp}")
    print(f"UID: {win.activeWpUID}")

def printActivePartInfo():
    print(f"Name: {win.activePart}")
    print(f"UID: {win.activePartUID}")

def printPartsInActiveAssy():
    asyPrtTree = []
    leafNodes = win.treeModel.leaves(self.activeAsyUID)
    for node in leafNodes:
        pid = node.identifier
        if pid in win._partDict:
            asyPrtTree.append(pid)
    print(asyPrtTree)

def printActPart():
    uid = win.activePartUID
    if uid:
        name = win._nameDict[uid]
        print("Active Part: %s [uid=%i]" % (name, int(uid)))
    else:
        print(None)

def printTreeView():
    """Print 'uid'; 'name'; 'parent' for all items in treeView."""
    iterator = QTreeWidgetItemIterator(win.treeView)
    while iterator.value():
        item = iterator.value()
        name = item.text(0)
        strUID = item.text(1)
        uid = int(strUID)
        pname = None
        parent = item.parent()
        if parent:
            puid = parent.text(1)
            pname = parent.text(0)
        print(f"UID: {uid}; Name: {name}; Parent: {pname}")
        iterator += 1

def clearPntStack():
    win.ptStack = []

def printDrawList():
    print("Draw List:", win.drawList)

def printInSync():
    print(win.inSync())
        
def setUnits_in():
    win.setUnits('in')
        
def setUnits_mm():
    win.setUnits('mm')

if __name__ == '__main__':        
    app = QApplication(sys.argv)
    win = MainWindow()
    win.add_menu('File')
    win.add_function_to_menu('File', "Load STEP", win.loadStep)
    win.add_function_to_menu('File', "Save STEP", win.saveStep)
    win.add_function_to_menu('File', "Save STEP (Act Prt)", win.saveStepActPrt)
    win.add_menu('Workplane')
    win.add_function_to_menu('Workplane', "Workplane on face", wpOnFace)
    win.add_function_to_menu('Workplane', "Workplane by 3 points", wpBy3Pts)
    win.add_function_to_menu('Workplane', "(Def) Workplane @Z=0", makeWP)
    win.add_menu('2D Geometry')
    win.add_function_to_menu('2D Geometry', "Make Wire Circle", makeWireCircle)
    win.add_menu('Create 3D')
    win.add_function_to_menu('Create 3D', "Box", makeBox)
    win.add_function_to_menu('Create 3D', "Cylinder", makeCyl)
    win.add_menu('Modify Active Part')
    win.add_function_to_menu('Modify Active Part', "Rotate Act Part", rotateAP)
    win.add_function_to_menu('Modify Active Part', "Make Hole", hole)
    win.add_function_to_menu('Modify Active Part', "Fillet", fillet)
    win.add_function_to_menu('Modify Active Part', "Shell", shell)
    win.add_function_to_menu('Modify Active Part', "Lift Face", lift)
    win.add_function_to_menu('Modify Active Part', "Offset Face", offsetFace)
    win.add_function_to_menu('Modify Active Part', "Align Face", alignFace)
    win.add_function_to_menu('Modify Active Part', "Tweak Face", tweakFace)
    win.add_function_to_menu('Modify Active Part', "Fuse", fuse)
    win.add_function_to_menu('Modify Active Part', "Remove Face", remFace)
    win.add_menu('Bottle')
    win.add_function_to_menu('Bottle', "Step 1: points", makePoints)
    win.add_function_to_menu('Bottle', "Step 2: lines", makeLines)
    win.add_function_to_menu('Bottle', "Step 3: half wire", makeHalfWire)
    win.add_function_to_menu('Bottle', "Step 4: whole wire", makeWholeWire)
    win.add_function_to_menu('Bottle', "Step 5: face", makeFace)
    win.add_function_to_menu('Bottle', "Step 6: body", makeBody)
    win.add_function_to_menu('Bottle', "Step 7: fillets", makeFillets)
    win.add_function_to_menu('Bottle', "Step 8: neck", addNeck)
    win.add_function_to_menu('Bottle', "start bottle", startBottle)
    win.add_function_to_menu('Bottle', "complete bottle", makeBottle)
    win.add_menu('Utility')
    win.add_function_to_menu('Utility', "Topology of Act Prt", topoDumpAP)
    win.add_function_to_menu('Utility', "print(current UID)", printCurrUID)
    win.add_function_to_menu('Utility', "print(TreeViewData)", printTreeView)
    win.add_function_to_menu('Utility', "print(Active Wp Info)", printActiveWpInfo)
    win.add_function_to_menu('Utility', "print(Active Asy Info)", printActiveAsyInfo)
    win.add_function_to_menu('Utility', "print(Active Prt Info)", printActivePartInfo)
    win.add_function_to_menu('Utility', "Clear Line Edit Stack", win.clearStack)
    win.add_function_to_menu('Utility', "Calculator", win.launchCalc)
    win.add_function_to_menu('Utility', "set Units ->in", setUnits_in)
    win.add_function_to_menu('Utility', "set Units ->mm", setUnits_mm)

    drawSubMenu = QMenu('Draw')
    win.popMenu.addMenu(drawSubMenu)    
    drawSubMenu.addAction('Fit All', win.fitAll)    
    drawSubMenu.addAction('Redraw', win.redraw)    
    drawSubMenu.addAction('Hide All', win.eraseAll)    
    drawSubMenu.addAction('Draw All', win.drawAll)    
    drawSubMenu.addAction('Draw Only Active Part', win.drawOnlyActivePart)

    win.treeView.popMenu.addAction('Set Active', win.setClickedActive)
    win.treeView.popMenu.addAction('Make Transparent', win.setTransparent)
    win.treeView.popMenu.addAction('Make Opaque', win.setOpaque)
    win.treeView.popMenu.addAction('Edit Name', win.editName)

    win.show()
    win.canva.InitDriver()
    display = win.canva._display

    selectSubMenu = QMenu('Select Mode')
    win.popMenu.addMenu(selectSubMenu)    
    selectSubMenu.addAction('Vertex', display.SetSelectionModeVertex)    
    selectSubMenu.addAction('Edge', display.SetSelectionModeEdge)    
    selectSubMenu.addAction('Face', display.SetSelectionModeFace)    
    selectSubMenu.addAction('Shape', display.SetSelectionModeShape)    
    selectSubMenu.addAction('Neutral', display.SetSelectionModeNeutral)    
    win.popMenu.addAction('Clear Callback', win.clearCallback)

    win.wpToolBar.addAction(QIcon(QPixmap('icons/hcl.gif')), 'Horizontal', clineH)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/vcl.gif')), 'Vertical', clineV)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/hvcl.gif')), 'H + V', clineHV)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/tpcl.gif')), 'By 2 Pnts', cline2Pts)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/acl.gif')), 'Angle', clineAng)
    #win.wpToolBar.addAction(QIcon(QPixmap('icons/refangcl.gif')), 'Ref-Ang', clineRefAng)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/abcl.gif')), 'Angular Bisector', clineAngBisec)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/lbcl.gif')), 'Linear Bisector', clineLinBisec)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/parcl.gif')), 'Parallel', clinePara)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/perpcl.gif')), 'Perpendicular', clinePerp)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cltan1.gif')), 'Tangent to circle', clineTan1)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cltan2.gif')), 'Tangent 2 circles', clineTan2)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/ccirc.gif')), 'Circle', ccirc)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cc3p.gif')), 'Circle by 3Pts', ccirc)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cccirc.gif')), 'Concentric Circle', ccirc)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cctan2.gif')), 'Circ Tangent x2', ccirc)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/cctan3.gif')), 'Circ Tangent x3', ccirc)
    win.wpToolBar.addSeparator()
    win.wpToolBar.addAction(QIcon(QPixmap('icons/line.gif')), 'Line', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/rect.gif')), 'Rectangle', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/poly.gif')), 'Polygon', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/slot.gif')), 'Slot', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/circ.gif')), 'Circle', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/arcc2p.gif')), 'Arc Cntr-2Pts', geom)
    win.wpToolBar.addAction(QIcon(QPixmap('icons/arc3p.gif')), 'Arc by 3Pts', geom)

    win.raise_() # bring the app to the top
    app.exec_()
