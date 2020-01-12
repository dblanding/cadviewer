# Copyright 2020 Doug Blanding (dblanding@gmail.com)
#
# This file is part of cadViewer.
#
# This module provides classes to read and write eXtended Data to and
# from step files, enabling the saving and loading (in STEP format)
# of a top assembly with its heirarchical structure (including all its
# component parts and subassemblies) with their names & colors.
#
# The latest  version of this file can be found at:
# //https://github.com/dblanding/cadviewer
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

import logging
import os.path
import treelib

from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.STEPCAFControl import (STEPCAFControl_Reader,
                                     STEPCAFControl_Writer)
from OCC.Core.TCollection import (TCollection_ExtendedString,
                                  TCollection_AsciiString)
from OCC.Core.TDataStd import TDataStd_Name, TDataStd_Name_GetID
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool,
                              XCAFDoc_DocumentTool_LayerTool,
                              XCAFDoc_DocumentTool_MaterialTool,
                              XCAFDoc_ColorSurf)
from OCC.Extend.TopologyUtils import TopologyExplorer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # set to DEBUG | INFO | ERROR

class StepImporter():
    """
    Read a step file with the goal of collecting a complete and accurate
    Assembly/Part structure, including the names of parts and assemblies,
    part color, and with all components shown in their correct positions.
    Data stored in self.tree
    """
    def __init__(self, filename, nextUID=0):

        self.filename = filename
        print(filename)
        self.tree = treelib.tree.Tree()  # to hold assembly structure
        self._currentUID = nextUID
        self.assyUidStack = [0]
        self.assyLocStack = []
        self.doc = self.read_file()  # TDocStd_Document

    def getNewUID(self):
        uid = self._currentUID + 1
        self._currentUID = uid
        return uid

    def getName(self, label):
        '''Get part name from label.'''
        return label.GetLabelName()

    def getColor(self, shape):
        # Get the part color
        #string_seq = self.layer_tool.GetObject().GetLayers(shape)
        color = Quantity_Color()
        self.color_tool.GetColor(shape, XCAFDoc_ColorSurf, color)
        logger.debug("color: {0}, {1}, {2}".format(color.Red(),
                                                   color.Green(),
                                                   color.Blue()))
        return color

    def findComponents(self, label, comps): # Discover Components of an Assembly
        logger.debug("")
        logger.debug("Finding components of label (entry = %s)" % label.EntryDumpToString())
        for j in range(comps.Length()):
            logger.debug("loop %i of %i" % (j+1, comps.Length()))
            cLabel = comps.Value(j+1)
            cShape = self.shape_tool.GetShape(cLabel)
            logger.debug("Label %i - type : %s" % (j+1, type(cLabel)))
            logger.debug("Entry: %s" % cLabel.EntryDumpToString())
            name = self.getName(cLabel)
            logger.debug("Part name: %s" % name)
            logger.debug("Is Assembly? %s" % self.shape_tool.IsAssembly(cLabel))
            logger.debug("Is Component? %s" % self.shape_tool.IsComponent(cLabel))
            logger.debug("Is Simple Shape? %s" % self.shape_tool.IsSimpleShape(cLabel))
            logger.debug("Is Reference? %s" % self.shape_tool.IsReference(cLabel))
            refLabel = TDF_Label()
            isRef = self.shape_tool.GetReferredShape(cLabel, refLabel)
            if isRef:
                refShape = self.shape_tool.GetShape(refLabel)
                refLabelEntry = refLabel.EntryDumpToString()
                logger.debug("Entry of referred shape: %s" % refLabelEntry)
                refName = self.getName(refLabel)
                logger.debug("Name of referred shape: %s" % refName)
                logger.debug("Is Assembly? %s" % self.shape_tool.IsAssembly(refLabel))
                logger.debug("Is Component? %s" % self.shape_tool.IsComponent(refLabel))
                logger.debug("Is Simple Shape? %s" % self.shape_tool.IsSimpleShape(refLabel))
                logger.debug("Is Reference? %s" % self.shape_tool.IsReference(refLabel))
                if self.shape_tool.IsSimpleShape(refLabel):
                    tempAssyLocStack = list(self.assyLocStack)
                    tempAssyLocStack.reverse()

                    for loc in tempAssyLocStack:
                        cShape.Move(loc)

                    color = self.getColor(refShape)
                    self.tree.create_node(name,
                                          self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None, 'c': color, 's': cShape})
                elif self.shape_tool.IsAssembly(refLabel):
                    name = self.getName(cLabel)  # Instance name
                    aLoc = TopLoc_Location()
                    aLoc = self.shape_tool.GetLocation(cLabel)
                    self.assyLocStack.append(aLoc)
                    newAssyUID = self.getNewUID()
                    self.tree.create_node(name,
                                          newAssyUID,
                                          self.assyUidStack[-1],
                                          {'a': True, 'l': aLoc, 'c': None, 's': None})
                    self.assyUidStack.append(newAssyUID)
                    rComps = TDF_LabelSequence() # Components of Assy
                    subchilds = False
                    isAssy = self.shape_tool.GetComponents(refLabel, rComps, subchilds)
                    logger.debug("Assy name: %s" % name)
                    logger.debug("Is Assembly? %s" % isAssy)
                    logger.debug("Number of components: %s" % rComps.Length())
                    if rComps.Length():
                        self.findComponents(refLabel, rComps)
        self.assyUidStack.pop()
        self.assyLocStack.pop()
        return

    def read_file(self):
        """Build self.tree (treelib.Tree()) containing CAD data read from a step file.

        Each node of self.tree contains the following:
        (Name, UID, ParentUID, {Data}) where the Data keys are:
        'a' (isAssy?), 'l' (TopLoc_Location), 'c' (Quantity_Color), 's' (TopoDS_Shape)
        """
        logger.info("Reading STEP file")
        doc = TDocStd_Document(TCollection_ExtendedString("STEP"))

        # Create the application
        app = XCAFApp_Application_GetApplication()
        app.NewDocument(TCollection_ExtendedString("MDTV-CAF"), doc)

        # Get root shapes
        shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
        shape_tool.SetAutoNaming(True)
        self.color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())
        layer_tool = XCAFDoc_DocumentTool_LayerTool(doc.Main())
        l_materials = XCAFDoc_DocumentTool_MaterialTool(doc.Main())

        step_reader = STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)

        status = step_reader.ReadFile(self.filename)
        if status == IFSelect_RetDone:
            logger.info("Transfer doc to STEPCAFControl_Reader")
            step_reader.Transfer(doc)

        """
        # Save doc to file (for educational purposes) (not working yet)
        logger.debug("Saving doc to file")
        savefilename = TCollection_ExtendedString('../doc.txt')
        app.SaveAs(doc, savefilename)
        """

        labels = TDF_LabelSequence()
        color_labels = TDF_LabelSequence()

        shape_tool.GetShapes(labels)
        self.shape_tool = shape_tool
        logger.info('Number of labels at root : %i' % labels.Length())
        try:
            rootlabel = labels.Value(1) # First label at root
        except RuntimeError:
            return
        name = self.getName(rootlabel)
        logger.info('Name of root label: %s' % name)
        isAssy = shape_tool.IsAssembly(rootlabel)
        logger.info("First label at root holds an assembly? %s" % isAssy)
        if isAssy:
            # If first label at root holds an assembly, it is the Top Assembly.
            # Through this label, the entire assembly is accessible.
            # No need to examine other labels at root explicitly.
            topLoc = TopLoc_Location()
            topLoc = shape_tool.GetLocation(rootlabel)
            self.assyLocStack.append(topLoc)
            entry = rootlabel.EntryDumpToString()
            logger.debug("Entry: %s" % entry)
            logger.debug("Top assy name: %s" % name)
            # Create root node for top assy
            newAssyUID = self.getNewUID()
            self.tree.create_node(name,
                                  newAssyUID,
                                  None,
                                  {'a': True, 'l': None, 'c': None, 's': None})
            self.assyUidStack.append(newAssyUID)
            topComps = TDF_LabelSequence() # Components of Top Assy
            subchilds = False
            isAssy = shape_tool.GetComponents(rootlabel, topComps, subchilds)
            logger.debug("Is Assembly? %s" % isAssy)
            logger.debug("Number of components: %s" % topComps.Length())
            logger.debug("Is Reference? %s" % shape_tool.IsReference(rootlabel))
            if topComps.Length():
                self.findComponents(rootlabel, topComps)
        else:
            # Labels at root can hold solids or compounds (which are 'crude' assemblies)
            # Either way, we will need to create a root node in self.tree
            newAssyUID = self.getNewUID()
            self.tree.create_node(os.path.basename(self.filename),
                                  newAssyUID,
                                  None,
                                  {'a': True, 'l': None, 'c': None, 's': None})
            self.assyUidStack = [newAssyUID]
            for j in range(labels.Length()):
                label = labels.Value(j+1)
                name = self.getName(label)
                isAssy = shape_tool.IsAssembly(label)
                logger.debug("Label %i is assembly?: %s" % (j+1, isAssy))
                shape = shape_tool.GetShape(label)
                color = self.getColor(shape)
                isSimpleShape = self.shape_tool.IsSimpleShape(label)
                logger.debug("Is Simple Shape? %s" % isSimpleShape)
                shapeType = shape.ShapeType()
                logger.debug("The shape type is: %i" % shapeType)
                if shapeType == 0:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_COMPOUND")
                    topo = TopologyExplorer(shape)
                    #topo = aocutils.topology.Topo(shape)
                    logger.debug("Nb of compounds : %i" % topo.number_of_compounds())
                    logger.debug("Nb of solids : %i" % topo.number_of_solids())
                    logger.debug("Nb of shells : %i" % topo.number_of_shells())
                    newAssyUID = self.getNewUID()
                    for i, solid in enumerate(topo.solids()):
                        name = "P%s" % str(i+1)
                        self.tree.create_node(name,
                                              self.getNewUID(),
                                              self.assyUidStack[-1],
                                              {'a': False, 'l': None,
                                               'c': color, 's': solid})
                elif shapeType == 2:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_SOLID")
                    self.tree.create_node(name,
                                          self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None,
                                           'c': color, 's': shape})
                elif shapeType == 3:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_SHELL")
                    self.tree.create_node(name,
                                          self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None,
                                           'c': color, 's': shape})

        return doc  # <class 'OCC.Core.TDocStd.TDocStd_Document'>
