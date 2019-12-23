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
import workplane
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QTreeWidget
from PyQt5.QtWidgets import QMenu, QDockWidget, QDesktopWidget, QToolButton
from PyQt5.QtWidgets import QLineEdit, QTreeWidgetItem, QAction
import PyQt5.QtWidgets
#import rpnCalculator
from OCC.Core.gp import *
from OCC.Core.GC import *
from OCC.Core.BRepBuilderAPI import *
from OCC.Core.TopoDS import *
from OCC.Core.TopExp import *
from OCC.Core.TopAbs import *
from OCC.Core.BRepAlgoAPI import *
from OCC.Core.BRepFilletAPI import *
from OCC.Core.BRepPrimAPI import *
from OCC.Core.BRepFeat import *
from OCC.Core.Geom import *
from OCC.Core.Geom2d import *
from OCC.Core.GCE2d import *
from OCC.Core.BRepOffsetAPI import *
from OCC.Core.IGESControl import *
from OCC.Core.TopTools import *
from OCC.Core.Standard import *
from OCC.Core.TopLoc import *
from OCC.Core.AIS import AIS_Shape
from OCC.Core.IntAna2d import *
from OCC.Core.BRepAdaptor import *
from OCC.Core.CPnts import *
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static_SetCVal
from OCC.Core.IFSelect import IFSelect_RetDone
import OCC.Core.BRepLib as BRepLib
import OCC.Core.BRep as BRep
#import OCCUtils.Construct
#import myStepXcafReader
import OCC.Display.OCCViewer
import OCC.Display.backend
used_backend = OCC.Display.backend.load_backend()
from OCC.Display import qtDisplay
from OCC import VERSION


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
        #self.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.contextMenu)
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
        super().__init__()
        self.canva = qtDisplay.qtViewer3d(self)
        #self.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.contextMenu)
        self.popMenu = QMenu(self)
        self.setWindowTitle("Simple CAD App using pythonOCC-%s ('qt' backend)"%VERSION)
        self.resize(960,720)
        self.setCentralWidget(self.canva)
        #self.treeDockWidget = QDockWidget("Assy/Part Structure", self)
        #self.treeDockWidget.setObjectName("treeDockWidget")
        #self.treeDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        #self.asyPrtTree = TreeList()   # Assy/Part structure (display)
        #self.asyPrtTree.itemClicked.connect(self.asyPrtTreeItemClicked)
        #self.asyPrtTree.itemChanged.connect(self.asyPrtTreeItemChanged)
        #self.treeDockWidget.setWidget(self.asyPrtTree)
        #self.addDockWidget(Qt.LeftDockWidgetArea, self.treeDockWidget)
        if not sys.platform == 'darwin':
            self.menu_bar = self.menuBar()
        else:
            # create a parentless menubar see:
            # http://stackoverflow.com/questions/11375176/qmenubar-and-qmenu-doesnt-show-in-mac-os-x?lq=1
            # noticeable is that the menu ( alas ) is created in the topleft of the screen,
            # just next to the apple icon
            # still does ugly things like showing the "Python" menu in bold
            self.menu_bar = QMenuBar()
        self._menus = {}
        self._menu_methods = {}
        # place the window in the center of the screen, at half the screen size
        self.centerOnScreen()
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
        
        self.lineEdit.textChanged.connect(self.appendToStack)
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
        #self.tree = QTreeWidget()  # Assy/Part Structure (model)
        #self.tree.create_node('/', 0, None, {'a':True, 'l':None, 'c':None, 's':None})   # Root Node in TreeModel
        #itemName = ['/', str(0)]
        #self.asyPrtTreeRoot = QTreeWidgetItem(self.asyPrtTree, itemName)    # Root Item in TreeView
        #self.asyPrtTree.expandItem(self.asyPrtTreeRoot)
        self.itemClicked = None   # TreeView item that has been mouse clicked
        self.floatStack = []  # storage stack for floating point values
        self.ptStack = []  # storage stack for point picks
        self.edgeStack = []  # storage stack for edge picks
        self.faceStack = []  # storage stack for face picks
        self.context = None
        self.calculator = None
        
    ####  PyQt general & menuBar:

    def launchCalc(self):
        if not self.calculator:
            self.calculator = rpnCalculator.Calculator(self)
            self.calculator.show()

    def setUnits(self, units):
        if units in self._unitDict.keys():
            self.units = units
            self.unitscale = self._unitDict[self.units]
            self.unitsLabel.setText("Units: %s " % self.units)
    
    def valueFromCalc(self, value):
        """Receive value from calculator."""
        print(value)

    def keybrdEntry(self, event):   # from cadvas
        """Store user entered values on stack.
        POINTS:
        points are stored in mm units in ECS on self.pt_stack.
        This is one of the places where unit scale is applied.

        FLOATS:
        floats are stored as unitless numbers on self.float_stack. Because a
        float value may be used for anything: radius, angle, x value, y value,
        whatever; it is not possible to know here how a float value will
        be used. It remains the responsibility of the using function to
        condition the float value appropriately by applying unitscale for
        distances, etc.
        """
        if self.op:
            text = self.entry.get()
            self.entry.delete(0, len(text))
            if self.text_entry_enable:
                self.text = text
            else:
                list = text.split(',')
                if len(list) == 1:
                    val = list[0]
                    self.float_stack.append(string.atof(val))
                elif len(list) == 2 and self.sel_mode == 'pnt':
                    # user entered points are already in ECS units
                    x, y = list
                    x = string.atof(x) * self.unitscale
                    y = string.atof(y) * self.unitscale
                    self.pt_stack.append((x, y))
            func = 'self.%s()' % self.op
            eval(func)

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
            #self.connect(_action, SIGNAL("triggered()"), _callable)
            _action.triggered.connect(_callable)
            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError('the menu item %s does not exist' % (menu_name))

    def closeEvent(self, event):
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
            print("This node is not an assembly")
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

    ####  Relay functions:

    def distPtPt(self):
        distPtPt()

    def edgeLen(self):
        edgeLen()

    ####  CAD model related methods:

    def printCurrUID(self):
        print(self._currentUID)

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

    def appendToStack(self):    # text input stack
        self.lineEditStack.append(unicode(self.lineEdit.text()))
        self.lineEdit.clear()
        cb = self.registeredCallback
        if cb:
            cb([])
        else:
            self.lineEditStack.pop()

    def clearStack(self):
        self.lineEditStack = []

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
            self.currOpLabel.setText("Current Operation: None ")
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
            print('initialized self.context')
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
                
                for cline in wp.clineList:
                    self.canva._display.DisplayShape(cline)
                for point in wp.intersectPts():
                    self.canva._display.DisplayShape(point)
                for ccirc in wp.ccircList:
                    self.canva._display.DisplayShape(ccirc)
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
            print("Load step cancelled")
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
            print("Save step cancelled.")
            return
        fname = str(fname)
        
        # initialize the STEP exporter
        step_writer = STEPControl_Writer()
        Interface_Static_SetCVal("write.step.schema", "AP203")

        # transfer shapes and write file
        step_writer.Transfer(self.activePart, STEPControl_AsIs)
        status = step_writer.Write(fname)
        assert(status == IFSelect_RetDone)
        
# Workplane creation functions...

def wpBy3Pts(initial=True):
    """
    Direction from pt1 to pt2 sets wDir, pt2 is wpOrigin.
    direction from pt2 to pt3 sets uDir
    """
    if initial:
        win.registerCallback(wpBy3PtsC)
        display.selected_shape = None
        display.SetSelectionModeVertex()
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
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if (len(win.ptStack) == 1):
        statusText = "Now select point 2 (wp origin)."
        win.statusBar().showMessage(statusText)
    elif (len(win.ptStack) == 2):
        statusText = "Now select point 3 to set uDir."
        win.statusBar().showMessage(statusText)
    elif (len(win.ptStack) == 3):
        wpBy3Pts(initial=False)

def wpOnFace(initial=True): # This doesn't work reliably. See Workplane class.
    """ First face defines plane of wp. Second face defines uDir.
    """
    if initial:
        win.registerCallback(wpOnFaceC)
        display.selected_shape = None
        display.SetSelectionModeFace()
        statusText = "Select face for workplane."
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
    print(shapelist)
    print(kwargs)
    for shape in shapeList:
        print(type(shape))
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (len(win.faceStack) == 1):
        statusText = "Select face for workplane U direction."
        win.statusBar().showMessage(statusText)
    elif (len(win.faceStack) == 2):
        wpOnFace(initial=False)

def makeWP():
    wp = workplane.WorkPlane(100)
    win.getNewPartUID(wp, typ='w')
    win.redraw()

# 2d geometry functions...

def makeHVcLine():
    win.activeWp.hvcl((0, 0))
    win.redraw()

def makeHcLine():
    win.activeWp.hcl((0, 30))
    win.redraw()

def makeAng_cLine():
    win.activeWp.acl((0,10), ang=30)
    win.redraw()

def linBisec_cLine(initial=True):
    if initial:
        win.registerCallback(linBisec_cLineC)
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
        
def linBisec_cLineC(shapeList, *kwargs):  # callback (collector) for line2Pts
    print(shapeList)
    print(kwargs)
    for shape in shapeList:
        print(type(shape))
        vrtx = topods_Vertex(shape)
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if len(win.ptStack) == 2:
        linBisec_cLine(initial=False)

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
    print(shapelist)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        print(type(vrtx))
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if win.ptStack:
        makeWireCircle(initial=False)

def line2Pts(initial=True):
    if initial:
        win.registerCallback(line2PtsC)
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
        wp.acl(pnt1, pnt2)
        win.ptStack = []
        win.redraw()
        
def line2PtsC(shapeList, *kwargs):  # callback (collector) for line2Pts
    print(shapelist)
    print(kwargs)
    for shape in shapeList:
        print(type(shape))
        vrtx = topods_Vertex(shape)
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        win.ptStack.append(gpPt)
    if len(win.ptStack) == 2:
        line2Pts(initial=False)

# 3D Geometry creation functions...

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
    
# 3D Geometry positioning functons...

def rotateAP():
    aisShape = AIS_Shape(win.activePart)
    ax1 = gp_Ax1(gp_Pnt(0., 0., 0.), gp_Dir(1., 0., 0.))
    aRotTrsf = gp_Trsf()
    angle = math.pi/6
    aRotTrsf.SetRotation(ax1, angle)
    aTopLoc = TopLoc_Location(aRotTrsf)
    win.activePart.Move(aTopLoc)
    win.redraw()
    return

# 3D Measure functons...

def distPtPt(initial=True):
    if initial:
        win.registerCallback(distPtPtC)
        display.SetSelectionModeShape()
        display.SetSelectionModeVertex()
        statusText = "pick 2 points."
        win.statusBar().showMessage(statusText)
    elif len(win.ptStack) == 2:
        p2 = win.ptStack.pop()
        p1 = win.ptStack.pop()
        vec = gp_Vec(p1, p2)
        dist = vec.Magnitude()
        dist = dist / win.unitscale
        win.calculator.putx(dist)
        win.redraw()
        
def distPtPtC(shapeList, *kwargs):  # callback (collector) for distPtPt
    print(shapelist)
    print(kwargs)
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        print(type(gpPt))
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
    print(shapelist)
    print(kwargs)
    for shape in shapeList:
        edge = topods_Edge(shape)
        win.edgeStack.append(edge)
    if win.edgeStack:
        edgeLen(initial=False)
    
# 3D Geometry modification functons...

def hole(initial=True):
    if initial:
        win.registerCallback(holeC)
        display.SetSelectionModeVertex()
        display.SetSelectionModeShape()
        win.lineEditStack = []
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
    print(shapelist)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        vrtx = topods_Vertex(shape)
        gpPt = BRep.BRep_Tool.Pnt(vrtx) # convert vertex to gp_Pnt
        print(type(gpPt))
        win.ptStack.append(gpPt)
    if (win.ptStack and win.lineEditStack):
        hole(initial=False)

def fillet(initial=True):
    if initial:
        win.registerCallback(filletC)
        display.SetSelectionModeEdge()
        win.lineEditStack = []
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
    print(shapelist)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        print(type(shape))
        edge = topods_Edge(shape)
        win.edgeStack.append(edge)
    if (win.edgeStack and win.lineEditStack):
        fillet(initial=False)

def shell(initial=True):
    if initial:
        win.registerCallback(shellC)
        display.SetSelectionModeFace()
        win.lineEditStack = []
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
    print(shapelist)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        print(type(shape))
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        shell(initial=False)

def lift(initial=True):
    if initial:
        win.registerCallback(liftC)
        display.SetSelectionModeFace()
        win.lineEditStack = []
        statusText = "Select face to offset and specify offset distance."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.faceStack):
        text = win.lineEditStack.pop()
        dist = float(text)
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        face = win.faceStack.pop()
        norm = OCCUtils.Construct.face_normal(face)
        liftVec = OCCUtils.Construct.dir_to_vec(norm).Scaled(dist)
        #toolBody = OCCUtils.Construct.make_prism(face, liftVec)
        # alternatively:
        toolBody = BRepPrimAPI_MakePrism(face, liftVec).Shape()
        #fused = OCCUtils.Construct.boolean_fuse(workPart, toolBody)
        # alternatively:
        join = BRepAlgoAPI_Fuse(workPart, toolBody)
        #join.RefineEdges() # join.FuseEdges() = False w/ or w/out this line
        print('flag of edge refining: ', join.FuseEdges())
        fused = join.Shape()
        join.Destroy()
        win.getNewPartUID(fused, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Lift operation complete')
        win.clearCallback()

def liftC(shapeList, *kwargs):  # callback (collector) for offset
    print(shapelist)
    print(kwargs)
    win.lineEdit.setFocus()
    for shape in shapeList:
        print(type(shape))
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        lift(initial=False)

def silo():
    partName = 'Silo'
    wire = win.activeWp.wire
    prismVec = gp_Vec(win.activeWp.wDir)
    prismVec.Scale(50)
    myBody = BRepPrimAPI_MakePrism(wire, prismVec).Shape()
    win.getNewPartUID(myBody, name=partName)
    win.redraw()

def punchHole():
    """ Punch hole in active part."""
    # No errors but this doesn't seem to work.
    origin = gp_Pnt(30,30,0)
    wDir = gp_Dir(0,0,1)
    ax1 = gp_Ax1(origin, wDir)
    mch = BRepFeat_MakeCylindricalHole()
    mch.Init(win.activePart, ax1)
    mch.Perform(10)

####  Info & Utility functions:
        
def printActPart():
    uid = win.activePartUID
    if uid:
        name = win._nameDict[uid]
        print("Active Part: %s [uid=%i]" % (name, int(uid)))
    else:
        print(None)

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
        
app = QApplication(sys.argv)
win = MainWindow()
win.add_menu('File')
win.add_function_to_menu('File', "Load STEP", win.loadStep)
win.add_function_to_menu('File', "Save STEP (Act Prt)", win.saveStepActPrt)
win.add_menu('Workplane')
win.add_function_to_menu('Workplane', "Workplane on face", wpOnFace)
win.add_function_to_menu('Workplane', "Workplane by 3 points", wpBy3Pts)
win.add_function_to_menu('Workplane', "(Def) Workplane @Z=0", makeWP)
win.add_menu('2D Construct')
win.add_function_to_menu('2D Construct', "Make HV cLine", makeHVcLine)
win.add_function_to_menu('2D Construct', "Make H cLine", makeHcLine)
win.add_function_to_menu('2D Construct', "Make Ang cLine", makeAng_cLine)
win.add_function_to_menu('2D Construct', "line by 2 Pts", line2Pts)
win.add_function_to_menu('2D Construct', "Linear Bisector cLine", linBisec_cLine)
win.add_menu('2D Geometry')
win.add_function_to_menu('2D Geometry', "Make Wire Circle", makeWireCircle)
win.add_function_to_menu('2D Geometry', "make Silo", silo)
win.add_menu('Create 3D')
win.add_function_to_menu('Create 3D', "Box", makeBox)
win.add_function_to_menu('Create 3D', "Cylinder", makeCyl)
win.add_menu('Modify Active Part')
win.add_function_to_menu('Modify Active Part', "Rotate Act Part", rotateAP)
win.add_function_to_menu('Modify Active Part', "Make Hole", hole)
win.add_function_to_menu('Modify Active Part', "Fillet", fillet)
win.add_function_to_menu('Modify Active Part', "Shell", shell)
win.add_function_to_menu('Modify Active Part', "Lift Face", lift)
win.add_menu('Utility')
win.add_function_to_menu('Utility', "print current UID", win.printCurrUID)    
win.add_function_to_menu('Utility', "print active part", printActPart)    
win.add_function_to_menu('Utility', "print drawList", printDrawList)    
win.add_function_to_menu('Utility', "Clear Stack", win.clearStack)    
win.add_function_to_menu('Utility', "Checked inSync w/ DL?", printInSync) 
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

#win.asyPrtTree.popMenu.addAction('Set Active', win.setActive)
#win.asyPrtTree.popMenu.addAction('Make Transparent', win.setTransparent)
#win.asyPrtTree.popMenu.addAction('Make Opaque', win.setOpaque)
#win.asyPrtTree.popMenu.addAction('Edit Name', win.editName)

win.show()
win.canva.InitDriver()
display = win.canva._display

selectSubMenu = QMenu('Select Mode')
win.popMenu.addMenu(selectSubMenu)    
selectSubMenu.addAction('Points', display.SetSelectionModeVertex)    
selectSubMenu.addAction('Lines', display.SetSelectionModeEdge)    
selectSubMenu.addAction('Faces', display.SetSelectionModeFace)    
selectSubMenu.addAction('Shapes', display.SetSelectionModeShape)    
selectSubMenu.addAction('Neutral', display.SetSelectionModeNeutral)    
win.popMenu.addAction('Clear Callback', win.clearCallback)

win.raise_() # bring the app to the top
app.exec_()

