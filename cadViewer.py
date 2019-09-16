#!/usr/bin/env python
#
# This file is part of cadViewer, 
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


from __future__ import absolute_import

import sys
import os, os.path
import math
from itertools import islice
import treelib
import workplane
import rpnCalculator
from AnyQt.QtCore import *
from AnyQt.QtGui import *
from AnyQt.QtWidgets import *
from OCC.AIS import AIS_Shape
from OCC.BRep import *
from OCC.BRepAdaptor import *
from OCC.BRepAlgoAPI import *
from OCC.BRepBuilderAPI import *
from OCC.BRepFeat import *
from OCC.BRepFill import *
from OCC.BRepFilletAPI import *
from OCC.BRepLib import *
from OCC.BRepPrimAPI import *
from OCC.BRepOffsetAPI import *
from OCC.gp import *
from OCC.GC import *
from OCC.Geom import *
from OCC.Geom2d import *
from OCC.GeomAPI import *
from OCC.GeomLib import *
from OCC.GCE2d import *
from OCC.TopoDS import *
from OCC.TopExp import *
from OCC.TopAbs import *
from OCC.TopTools import *
from OCC.TopLoc import *
from OCC.Standard import *
from OCC.IntAna2d import *
from OCC.CPnts import *
from OCC.IntAna import IntAna_IntConicQuad
from OCC.Precision import precision_Angular, precision_Confusion
from OCC.Interface import Interface_Static_SetCVal
from OCC.IFSelect import IFSelect_RetDone
from OCCUtils import Construct, Topology
from OCC.IGESControl import *
from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs
#import myStepXcafReader
import OCC.Display.OCCViewer
import OCC.Display.backend
from OCC import VERSION
print "OCC version: %s" % VERSION

# 'used_backend' needs to be defined prior to importing qtViewer3D
if VERSION < "0.16.5":
    used_backend = OCC.Display.backend.get_backend()
elif VERSION == "0.16.5":
    used_backend = OCC.Display.backend.load_backend()
else:
    used_backend = OCC.Display.backend.load_backend()
    print "OCC Version = %s" % OCC.VERSION
from OCC.Display import qtDisplay

TOL = 1e-7 # Linear Tolerance
ATOL = TOL # Angular Tolerance
print 'TOLERANCE = ', TOL

class TreeList(QTreeWidget): # With 'drag & drop' ; context menu
    """ Display assembly structure
    """
    def __init__(self, parent=None):
        QTreeWidget.__init__(self, parent)
        self.header().setHidden(True)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDragDropMode(self.InternalMove)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.contextMenu)
        #self.contextMenu.completed.connect(
        self.popMenu = QMenu(self)

    def contextMenu(self, point):
        self.menu = QMenu()
        action = self.popMenu.exec_(self.mapToGlobal(point))

    def dropEvent(self, event):
        if event.source() == self:
            QAbstractItemView.dropEvent(self, event)

    def dropMimeData(self, parent, row, data, action):
        if action == Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def moveSelection(self, parent, position):
    # save the selected items
        selection = [QPersistentModelIndex(i)
                      for i in self.selectedIndexes()]
        parent_index = self.indexFromItem(parent)
        if parent_index in selection:
            return False
        # save the drop location in case it gets moved
        target = self.model().index(position, 0, parent_index).row()
        if target < 0:
            target = position
        # remove the selected items
        taken = []
        for index in reversed(selection):
            item = self.itemFromIndex(QModelIndex(index))
            if item is None or item.parent() is None:
                taken.append(self.takeTopLevelItem(index.row()))
            else:
                taken.append(item.parent().takeChild(index.row()))
        # insert the selected items at their new positions
        while taken:
            if position == -1:
                # append the items if position not specified
                if parent_index.isValid():
                    parent.insertChild(
                        parent.childCount(), taken.pop(0))
                else:
                    self.insertTopLevelItem(
                        self.topLevelItemCount(), taken.pop(0))
            else:
                # insert the items at the specified position
                if parent_index.isValid():
                    parent.insertChild(min(target,
                        parent.childCount()), taken.pop(0))
                else:
                    self.insertTopLevelItem(min(target,
                        self.topLevelItemCount()), taken.pop(0))
        return True

class MainWindow(QMainWindow):
    def __init__(self, *args):
        apply(QMainWindow.__init__,(self,)+args)
        self.canva = qtDisplay.qtViewer3d(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.contextMenu)
        #self.completed.connect(self.contextMenu)
        self.popMenu = QMenu(self)
        self.setWindowTitle("Simple CAD App using pythonOCC-%s ('qt' backend)"%VERSION)
        self.resize(960,720)
        self.setCentralWidget(self.canva)
        self.treeDockWidget = QDockWidget("Assy/Part Structure", self)
        self.treeDockWidget.setObjectName("treeDockWidget")
        self.treeDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea| Qt.RightDockWidgetArea)
        self.asyPrtTree = TreeList()   # Assy/Part structure (display)
        self.asyPrtTree.itemClicked.connect(self.asyPrtTreeItemClicked)
        #self.asyPrtTree.itemChanged.connect(self.asyPrtTreeItemChanged)
        self.treeDockWidget.setWidget(self.asyPrtTree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.treeDockWidget)
        self.wpToolBar = QToolBar("2D")
        self.addToolBar(Qt.RightToolBarArea, self.wpToolBar)
        self.wpToolBar.setMovable(True)
        if sys.platform == 'darwin':
            QtGui.qt_mac_set_native_menubar(False)
        self.menu_bar = self.menuBar()
        self._menus = {}
        self._menu_methods = {}
        self.centerOnScreen()
        # Internally, everything is always in mm
        # scale user input and output values
        # (user input values) * unitscale = value in mm
        # (output values) / unitscale = value in user's units
        self._unitDict = {'mm': 1.0, 'in': 25.4, 'ft': 304.8}
        self.units = 'mm'
        self.unitscale = self._unitDict[self.units]
        self.unitsLabel = QLabel()
        self.unitsLabel.setText("Units: %s " % self.units)
        #self.unitsLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.endOpButton = QToolButton()
        self.endOpButton.setText('End Operation')
        self.endOpButton.clicked.connect(self.clearCallback)
        self.currOpLabel = QLabel()
        self.registeredCallback = None
        self.currOpLabel.setText("Current Operation: %s " % self.registeredCallback)
        self.lineEdit = QLineEdit()
        self.lineEditStack = [] # list of user inputs
        #self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.appendToStack)
        #self.lineEdit.completed.connect(self.appendToStack)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.lineEdit)
        status.addPermanentWidget(self.currOpLabel)
        status.addPermanentWidget(self.endOpButton)
        status.addPermanentWidget(self.unitsLabel)
        status.showMessage("Ready", 5000)
        self.activePart = None # OCCpartObject
        self.activePartUID = 0
        self.activeWp = None # WorkPlane object
        self.activeWpUID = 0
        self._assyDict = {} # k = uid, v = Loc
        self._partDict = {} # k = uid, v = OCCpartObject
        self._wpDict = {} # k = uid, v = wpObject
        self._nameDict = {} # k = uid, v = partName
        self._colorDict = {}    # k = uid, v = part display color
        self._transparencyDict = {}    # k = uid, v = part display transparency
        self._ancestorDict = {} # k = uid, v = ancestorUID
        self._currentUID = 0
        self._wpNmbr = 1
        self.drawList = [] # list of part uid's to be displayed
        self.tree = treelib.Tree()  # Assy/Part Structure (model)
        self.tree.create_node('/', 0, None, {'a':True, 'l':None, 'c':None, 's':None})   # Root Node in TreeModel
        itemName = QStringList(['/', str(0)])
        self.asyPrtTreeRoot = QTreeWidgetItem(self.asyPrtTree, itemName)    # Root Item in TreeView
        self.asyPrtTree.expandItem(self.asyPrtTreeRoot)
        self.itemClicked = None   # TreeView item that has been mouse clicked
        self.floatStack = []  # storage stack for floating point values
        self.ptStack = []  # storage stack for point picks
        self.edgeStack = []  # storage stack for edge picks
        self.faceStack = []  # storage stack for face picks
        self.shapeStack = []  # storage stack for shape picks
        self.context = None
        self.calculator = None
        
    ####  PyQt menuBar & general methods:

    def centerOnScreen (self):
        '''Centers the window on the screen.'''
        resolution = QDesktopWidget().screenGeometry()
        self.move(
                    (resolution.width() / 2) - (self.frameSize().width() / 2),
                    (resolution.height() / 2) - (self.frameSize().height() / 2)
        )

    def add_menu(self, menu_name):
        _menu = self.menu_bar.addMenu("&"+menu_name)
        self._menus[menu_name]=_menu
        
    def add_function_to_menu(self, menu_name, text, _callable):
        assert callable(_callable), 'the function supplied is not callable'
        try:
            _action = QAction(text, self)
            # if not, the "exit" action is now shown...
            # Qt is trying so hard to be native cocoa'ish that its a nuisance
            _action.setMenuRole(QAction.NoRole)
            self.connect(_action, SIGNAL("triggered()"), _callable)
            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError('the menu item %s does not exist' % (menu_name))

    def closeEvent(self, event):    # things that need to happen on exit
        try:
            self.calculator.close()
        except:
            pass
        event.accept()

    #### 'treeView' related methods:

    def contextMenu(self, point):
        self.menu = QMenu()
        action = self.popMenu.exec_(self.mapToGlobal(point))

    def getPartsInAssy(self, uid):
        if uid not in self._assyDict.keys():
            print "This node is not an assembly"
        else:
            asyPrtTree = []
            leafNodes = self.tree.leaves(uid)
            for node in leafNodes:
                pid = node.identifier
                if pid in self._partDict.keys():
                    asyPrtTree.append(pid)
            return asyPrtTree

    def asyPrtTreeItemClicked(self, item):  # called whenever treeView item is clicked
        self.itemClicked = item # store item
        if not self.inSync():   # click may have been on checkmark. Update drawList (if needed)
            self.syncDrawListToChecked()
            self.redraw()

    def checkedToList(self):
        """
        Returns list of checked (part) items in treeView
        """
        dl = []
        for item in self.asyPrtTree.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            if item.checkState(0) == 2:
                uid = int(item.text(1))
                if (uid in self._partDict.keys()) or (uid in self._wpDict.keys()):
                    dl.append(uid)
        return dl
        
    def inSync(self):
        """
        Returns True if checked items are in sync with drawList
        """
        if self.checkedToList() == self.drawList:
            return True
        else:
            return False
        
    def syncDrawListToChecked(self):
        self.drawList = self.checkedToList()

    def syncCheckedToDrawList(self):
        for item in self.asyPrtTree.findItems("", Qt.MatchContains | Qt.MatchRecursive):
            itemUid = int(item.text(1))
            if (itemUid in self._partDict) or (itemUid in self._wpDict):
                if itemUid in self.drawList:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

    def setActive(self):    # Set item clicked in treeView Active
        item = self.itemClicked
        if item:
            name = item.text(0)
            uid = int(item.text(1))
            if uid in self._partDict:
                self.activePart = self._partDict[uid]
                self.activePartUID = uid
                sbText = "%s [uid=%i] is now the active part" % (name, uid)
                self.redraw()
            elif uid in self._wpDict:
                self.activeWp = self._wpDict[uid]
                self.activeWpUID = uid
                sbText = "%s [uid=%i] is now the active workplane" % (name, uid)
                self.redraw()
            else:
                sbText = "This is an assembly. Click on a part."
            self.asyPrtTree.clearSelection()
            self.itemClicked = None
            self.statusBar().showMessage(sbText, 5000)

    def setTransparent(self):
        item = self.itemClicked
        if item:
            uid = int(item.text(1))
            if uid in self._partDict:
                self._transparencyDict[uid] = 0.6
                self.redraw()
            self.itemClicked = None

    def setOpaque(self):
        item = self.itemClicked
        if item:
            uid = int(item.text(1))
            if uid in self._partDict:
                self._transparencyDict.pop(uid)
                self.redraw()
            self.itemClicked = None
               
    def editName(self): # Edit name of item clicked in treeView
        item = self.itemClicked
        sbText = '' # status bar text
        if item:
            name = item.text(0)
            uid = int(item.text(1))
            prompt = 'Enter new name for part %s' % name
            newName, OK = QInputDialog.getText(self, 'Input Dialog',
                                               prompt, text=name)
            if OK:
                item.setText(0, newName)
                sbText = "Part name changed to %s" % newName
                self._nameDict[uid] = newName
        self.asyPrtTree.clearSelection()
        self.itemClicked = None
        # Todo: update name in treeModel
        self.statusBar().showMessage(sbText, 5000)

    ####  Relay functions: (give calculator access to module functions)

    def distPtPt(self):
        distPtPt()

    def edgeLen(self):
        edgeLen()

    ####  Administrative and data mangaement methods:

    def launchCalc(self):
        if not self.calculator:
            self.calculator = rpnCalculator.Calculator(self)
            self.calculator.show()

    def setUnits(self, units):
        if units in self._unitDict.keys():
            self.units = units
            self.unitscale = self._unitDict[self.units]
            self.unitsLabel.setText("Units: %s " % self.units)
    
    def printCurrUID(self):
        print self._currentUID

    def getNewPartUID(self, objct, name="", ancestor=0,
                      typ='p', color=None):
        """
        Method for assigning a unique ID (serial number) to a new part
        (typ='p'), assembly (typ='a') or workplane (typ='w') generated
        within the application. Using that uid as a key, record the
        information in the various dictionaries. The process of modifying
        an existing part generally involves doing an operation on an
        existing 'ancestor' part, which is not thrown away, but merely
        removed from the drawlist.
        """
        uid = self._currentUID + 1
        self._currentUID = uid               
        if ancestor:
            if ancestor in self._colorDict.keys():
                color = self._colorDict[ancestor]
            if ancestor in self._transparencyDict.keys():
                transp = self._transparencyDict[ancestor]
                self._transparencyDict[uid] = transp
            if not name:
                name = self._nameDict[ancestor] # Keep ancestor name
            if ancestor in self.drawList:
                self.drawList.remove(ancestor)  # Remove ancestor from draw list
        if not name:
            name = 'Part'   # Default name
        # Update appropriate dictionaries and add node to treeModel
        if typ == 'p':
            self._partDict[uid] = objct # OCC...
            if color:   # OCC.Quantity.Quantity_Color()
                c = OCC.Display.OCCViewer.color(color.Red(), color.Green(), color.Blue())
            else:
                c = OCC.Display.OCCViewer.color(.2,.1,.1)   # default color
            self._colorDict[uid] = c
            if ancestor:
                self._ancestorDict[uid] = ancestor
            self.tree.create_node(name,
                                  uid,
                                  0,
                                  {'a': False, 'l': None, 'c': c, 's': objct})
            # Make new part active
            self.activePartUID = uid
            self.activePart = objct
        elif typ == 'a':
            self._assyDict[uid] = objct  # TopLoc_Location
            self.tree.create_node(name,
                                  uid,
                                  0,
                                  {'a': True, 'l': None, 'c': None, 's': None})
        elif typ == 'w':
            name = "wp%i" % self._wpNmbr
            self._wpNmbr += 1
            self._wpDict[uid] = objct # wpObject
            self.tree.create_node(name,
                                  uid,
                                  0,
                                  {'a': False, 'l': None, 'c': None, 's': None})
            self.activeWp = objct
            self.activeWpUID = uid
        self._nameDict[uid] = name
        # add item to treeView
        itemName = QStringList([name, str(uid)])
        item = QTreeWidgetItem(self.asyPrtTreeRoot, itemName)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked)
        # Add new uid to draw list and sync w/ treeView
        self.drawList.append(uid)
        self.syncCheckedToDrawList()
        return uid

    def appendToStack(self):    # called when <ret> is pressed on line edit
        self.lineEditStack.append(unicode(self.lineEdit.text()))
        self.lineEdit.clear()
        cb = self.registeredCallback
        if cb:
            cb([])  # call self.registeredCallback with arg=empty_list
        else:
            self.lineEditStack.pop()

    def valueFromCalc(self, value):
        """Receive value from calculator."""
        cb = self.registeredCallback
        if cb:
            self.lineEditStack.append(str(value))
            cb([])  # call self.registeredCallback with arg=empty_list
        else:
            print value

    def clearStack(self):
        self.lineEditStack = []

    def clearAllStacks(self):
        self.lineEditStack = []
        self.floatStack = []
        self.ptStack = []
        self.edgeStack = []
        self.faceStack = []
        
    def registerCallback(self, callback):
        currCallback = self.registeredCallback
        if currCallback:    # Make sure a callback isn't already registered
            self.clearCallback()
        display.register_select_callback(callback)
        self.registeredCallback = callback
        self.currOpLabel.setText("Current Operation: %s " % callback.func_name[:-1])
            
    def clearCallback(self):
        if self.registeredCallback:
            display.unregister_callback(self.registeredCallback)
            self.registeredCallback = None
            self.clearAllStacks()
            self.currOpLabel.setText("Current Operation: None ")
            win.statusBar().showMessage('')
            display.SetSelectionModeNeutral()
            self.redraw()
        
    ####  3D Display (Draw / Hide) methods:

    def fitAll(self):
        self.canva._display.FitAll()

    def eraseAll(self):
        context = self.canva._display.Context
        context.RemoveAll()
        self.drawList = []
        self.syncCheckedToDrawList()
    
    def redraw(self):
        if not self.context:
            context = self.canva._display.Context
            self.context = context
            print 'initialized self.context'
        context = self.context
        if not self.registeredCallback:
            display.SetSelectionModeNeutral()
            context.SetAutoActivateSelection(False)
        context.RemoveAll()
        for uid in self.drawList:
            if uid in self._partDict.keys():
                if uid in self._transparencyDict.keys():
                    transp = self._transparencyDict[uid]
                else:
                    transp = 0
                color = self._colorDict[uid]
                aisShape = AIS_Shape(self._partDict[uid])
                h_aisShape = aisShape.GetHandle()
                context.Display(h_aisShape)
                context.SetColor(h_aisShape, color)
                context.SetTransparency(h_aisShape, transp)
                if uid == self.activePartUID:
                    edgeColor = OCC.Quantity.Quantity_NOC_RED
                else:
                    edgeColor = OCC.Quantity.Quantity_NOC_BLACK
                context.HilightWithColor(h_aisShape, edgeColor)
            elif uid in self._wpDict.keys():
                wp = self._wpDict[uid]
                border = wp.border
                aisShape = AIS_Shape(border)
                h_aisShape = aisShape.GetHandle()
                context.Display(h_aisShape)
                if uid == self.activeWpUID:
                    borderColor = OCC.Quantity.Quantity_NOC_DARKGREEN
                else:
                    borderColor = OCC.Quantity.Quantity_NOC_GRAY
                context.SetColor(h_aisShape, borderColor)
                context.SetTransparency(h_aisShape, 0.8)
                clClr = OCC.Display.OCCViewer.color(1,0,1)
                for cline in wp.clineList:
                    self.canva._display.DisplayShape(cline, color=clClr)
                for point in wp.intersectPts():
                    self.canva._display.DisplayShape(point)
                for ccirc in wp.ccircList:
                    self.canva._display.DisplayShape(ccirc, color=clClr)
                for wire in wp.wireList:
                    self.canva._display.DisplayShape(wire, color="WHITE")
                display.Repaint()

    def drawAll(self):
        self.drawList = []
        for k in self._partDict.keys():
            self.drawList.append(k)
        for k in self._wpDict.keys():
            self.drawList.append(k)
        self.syncCheckedToDrawList()
        self.redraw()

    def drawOnlyActivePart(self):
        self.eraseAll()
        uid = self.activePartUID
        self.drawList.append(uid)
        self.canva._display.DisplayShape(self._partDict[uid])
        self.syncCheckedToDrawList()
        self.redraw()

    def drawOnlyPart(self, key):
        self.eraseAll()
        self.drawList.append(key)
        self.syncCheckedToDrawList()
        self.redraw()

    def drawAddPart(self, key): # Add part to drawList
        self.drawList.append(key)
        self.syncCheckedToDrawList()
        self.redraw()

    def drawHidePart(self, key): # Remove part from drawList
        if key in self.drawList:
            self.drawList.remove(key)
            self.syncCheckedToDrawList()
            self.redraw()

    ####  Step Load / Save methods:

    def loadStep(self):
        """
        Load a step file and bring it in as a treelib.Tree() structure
        Unpack this structure to:
        1. Populate the various dictionaries: assy, part, name, color and
        2. Build the Part/Assy structure (treeView), and
        3. Paste the loaded tree onto win.tree (treeModel)
        """
        prompt = 'Select STEP file to import'
        fname = QFileDialog.getOpenFileName(None, prompt, './', "STEP files (*.stp *.STP *.step)")
        if not fname:
            print "Load step cancelled"
            return
        fname = str(fname)
        name = os.path.basename(fname).split('.')[0]
        nextUID = self._currentUID
        stepImporter = myStepXcafReader.StepXcafImporter(fname, nextUID)
        tree = stepImporter.tree
        tempTreeDict = {}   # uid:asyPrtTreeItem (used temporarily during unpack)
        for uid in tree.expand_tree(mode=self.tree.DEPTH):
            node = tree.get_node(uid)
            name = node.tag
            itemName = QStringList([name, str(uid)])
            parentUid = node.bpointer
            if node.data['a']:  # Assembly
                if not parentUid: # This is the top level item
                    parentItem = self.asyPrtTreeRoot
                else:
                    parentItem = tempTreeDict[parentUid]
                item = QTreeWidgetItem(parentItem, itemName)
                item.setFlags(item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self.asyPrtTree.expandItem(item)
                tempTreeDict[uid] = item
                Loc = node.data['l'] # Location object
                self._assyDict[uid] = Loc
            else:   # Part
                # add item to asyPrtTree treeView
                if not parentUid: # This is the top level item
                    parentItem = self.asyPrtTreeRoot
                else:
                    parentItem = tempTreeDict[parentUid]
                item = QTreeWidgetItem(parentItem, itemName)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked)
                tempTreeDict[uid] = item
                color = node.data['c']
                shape = node.data['s']
                # Update dictionaries
                self._partDict[uid] = shape
                self._nameDict[uid] = name
                if color:
                    c = OCC.Display.OCCViewer.color(color.Red(), color.Green(), color.Blue())
                else:
                    c = OCC.Display.OCCViewer.color(.2,.1,.1)   # default color
                self._colorDict[uid] = c
                self.activePartUID = uid           # Set as active part
                self.activePart = shape
                self.drawList.append(uid)   # Add to draw list
        self.tree.paste(0, tree) # Paste tree onto win.tree root
        
        keyList = tempTreeDict.keys()
        keyList.sort()
        maxUID = keyList[-1]
        self._currentUID = maxUID
        
        self.redraw()

    def saveStepActPrt(self):
        prompt = 'Choose filename for step file.'
        fname = QFileDialog.getSaveFileName(None, prompt, './', "STEP files (*.stp *.STP *.step)")
        if not fname:
            print "Save step cancelled."
            return
        fname = str(fname)
        
        # initialize the STEP exporter
        step_writer = STEPControl_Writer()
        Interface_Static_SetCVal("write.step.schema", "AP203")

        # transfer shapes and write file
        step_writer.Transfer(self.activePart, STEPControl_AsIs)
        status = step_writer.Write(fname)
        assert(status == IFSelect_RetDone)
        
#############################################
#
# Workplane creation functions...
#
#############################################

def wpBy3Pts(initial=True):
    """
    Pick 3 points (vertices).
    Direction from pt1 to pt2 sets wDir, pt2 is wpOrigin.
    Direction from pt2 to pt3 sets uDir
    """
    if initial:
        win.registerCallback(wpBy3PtsC)
        display.selected_shape = None
        display.SetSelectionModeVertex()
        win.ptStack = []
        statusText = "Pick 3 points. Dir from pt1-pt2 sets wDir, pt2 is origin."
        win.statusBar().showMessage(statusText)
        return
    if win.ptStack:
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
        
def wpBy3PtsC(shapeList, *kwargs):  # callback (collector) for wpBy3Pts
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
        wpBy3Pts(initial=False)

def wpOnFace(initial=True):
    """
    Pick 2 faces. First face defines plane of wp. Second face defines uDir.
    """
    if initial:
        win.registerCallback(wpOnFaceC)
        display.selected_shape = None
        display.SetSelectionModeFace()
        win.faceStack = []
        statusText = "Select face for workplane. (WP origin in cntr of face.)"
        win.statusBar().showMessage(statusText)
        return
    if win.faceStack:
        faceU = win.faceStack.pop()
        faceW = win.faceStack.pop()
        wp = workplane.WorkPlane(100, face=faceW, faceU=faceU)
        win.getNewPartUID(wp, typ='w')
        win.clearCallback()
        statusText = "Workplane created."
        win.statusBar().showMessage(statusText)
        
def wpOnFaceC(shapeList, *kwargs):  # callback (collector) for wpOnFace
    print shapeList
    print kwargs
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (len(win.faceStack) == 1):
        statusText = "Select face for workplane U direction."
        win.statusBar().showMessage(statusText)
    elif (len(win.faceStack) == 2):
        wpOnFace(initial=False)

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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
# 3D Measure functons...
#
#############################################

def distPtPt(initial=True):
    if initial:
        win.registerCallback(distPtPtC)
        # Next 2 lines enable selecting intersection points on WP
        display.SetSelectionModeVertex()
        display.SetSelectionModeShape()
        # User needs to switch to "Select Mode: Vertex" to pick vertices on parts
        statusText = "Dist between 2 pts on WP. (Select Mode: Vertex for parts)"
        win.statusBar().showMessage(statusText)
    elif len(win.ptStack) == 2:
        p2 = win.ptStack.pop()
        p1 = win.ptStack.pop()
        vec = gp_Vec(p1, p2)
        dist = vec.Magnitude()
        dist = dist / win.unitscale
        win.calculator.putx(dist)
        
def distPtPtC(shapeList, *kwargs):  # callback (collector) for distPtPt
    print shapeList
    print kwargs
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if len(win.ptStack) == 2:
        distPtPt(initial=False)
    
def edgeLen(initial=True):
    if initial:
        win.registerCallback(edgeLenC)
        display.SetSelectionModeEdge()
        statusText = "pick 2 points."
        win.statusBar().showMessage(statusText)
    elif win.edgeStack:
        edge = win.edgeStack.pop()
        edgelen = CPnts_AbscissaPoint_Length(BRepAdaptor_Curve(edge))
        edgelen = edgelen / win.unitscale
        win.calculator.putx(edgelen)
        win.redraw()
        
def edgeLenC(shapeList, *kwargs):  # callback (collector) for edgeLen
    print shapeList
    print kwargs
    for shape in shapeList:
        edge = topods_Edge(shape)
        win.edgeStack.append(edge)
    if win.edgeStack:
        edgeLen(initial=False)

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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
        print 'Not yet implemented for faces with holes.'
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
    print 'Number of edges on mFace = ', nrEdges

    # make an ordered list of faces adjacent to mFace
    faces = topo.faces_from_solids(workPart) # all faces
    adjFacesDict = {} # key=seq : value=face
    for face in faces:
        edges = topo.edges_from_face(face)
        if face.IsSame(mFace):
            print 'Found mFace'
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
                print 'found adjacent face at sequence %i' % seq
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
        
        print 'Length of mF_vrtxList= ', len(mF_vrtxList)
        print 'Length of newPointList= ', len(newPntList)
        
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
                    print 'Unable to find intersection with target plane'
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
    print 'Number of New Edges = ', nrEdges
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

    print 'number of new points = ', len(newPntList)
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
    
    print 'Number of other faces: ', len(otherFaces)
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
    print shapeList
    print kwargs
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
        print 'Number of faces to begin: ', topo.number_of_faces_from_solids(workPart)
        print 'Number of faces after removal: ', len(faceList)
        for f in faceList:
            sew.Add(f)
        sew.Perform()
        res = sew.SewedShape()
        win.getNewPartUID(res)
        win.statusBar().showMessage('Face Removal operation complete')
        win.clearCallback()
        
def remFaceC(shapeList, *kwargs):  # callback (collector) for remFace
    print shapeList
    print kwargs
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
        print 'Number of faces to repair: ', len(planarFaceRepairList)
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
#  Info & Utility functions:
#
#############################################

def topoDumpAP():
    Topology.dumpTopology(win.activePart)
        
def printActPart():
    uid = win.activePartUID
    if uid:
        name = win._nameDict[uid]
        print "Active Part: %s [uid=%i]" % (name, int(uid))
    else:
        print None

def clearPntStack():
    win.ptStack = []

def printDrawList():
    print "Draw List:", win.drawList

def printInSync():
    print win.inSync()
        
def setUnits_in():
    win.setUnits('in')
        
def setUnits_mm():
    win.setUnits('mm')
        
app = QApplication(sys.argv)
win = MainWindow()
win.add_menu('File')
win.add_function_to_menu('File', "Load STEP", win.loadStep)
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
win.add_menu('Utility')
win.add_function_to_menu('Utility', "Topology of Act Prt", topoDumpAP)    
win.add_function_to_menu('Utility', "print current UID", win.printCurrUID)    
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

win.asyPrtTree.popMenu.addAction('Set Active', win.setActive)
win.asyPrtTree.popMenu.addAction('Make Transparent', win.setTransparent)
win.asyPrtTree.popMenu.addAction('Make Opaque', win.setOpaque)
win.asyPrtTree.popMenu.addAction('Edit Name', win.editName)

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

