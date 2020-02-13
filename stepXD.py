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


import logging
import os.path
import treelib
from treemodel import TreeModel
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.XCAFDoc import XCAFDoc_ColorSurf
from OCC.Extend.TopologyUtils import TopologyExplorer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # set to DEBUG | INFO | ERROR

class StepImporter():
    """Read .stp file, and create a TDocStd_Document OCAF document.

    Also, convert OCAF doc to a (disposable) treelib.Tree() structure.
    """
    def __init__(self, filename, nextUID=0):

        self.filename = filename
        self.tree = treelib.tree.Tree()  # 'disposable' ass'y structure
        self._currentUID = nextUID
        self.assyUidStack = [0]
        self.assyLocStack = []
        self.doc = self.read_file()  # TDocStd_Document

    def getNewUID(self):
        """Dispense a series of sequential integers as uids.

        Start with one more than the value held in win._currentUID.
        When finished, update the value held in win._currentUID."""
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
        logger.debug("color: %i, %i, %i", color.Red(), color.Green(), color.Blue())
        return color

    def findComponents(self, label, comps):
        """Discover components from comps (LabelSequence) of an assembly (label).

        Components of an assembly are, by definition, references which refer to
        either a shape or another assembly. Components are essentially 'instances'
        of the referred shape or assembly, and carry a location vector specifing
        the location of the referred shape or assembly.
        """
        logger.debug("")
        logger.debug("Finding components of label entry %s)", label.EntryDumpToString())
        for j in range(comps.Length()):
            logger.debug("loop %i of %i", j+1, comps.Length())
            cLabel = comps.Value(j+1)  # component label <class 'OCC.Core.TDF.TDF_Label'>
            cShape = self.shape_tool.GetShape(cLabel)
            logger.debug("Component number %i", j+1)
            logger.debug("Component entry: %s", cLabel.EntryDumpToString())
            name = self.getName(cLabel)
            logger.debug("Component name: %s", name)
            refLabel = TDF_Label()  # label of referred shape (or assembly)
            isRef = self.shape_tool.GetReferredShape(cLabel, refLabel)
            if isRef:  # I think all components are references, but just in case...
                refShape = self.shape_tool.GetShape(refLabel)
                refLabelEntry = refLabel.EntryDumpToString()
                logger.debug("Entry referred to: %s", refLabelEntry)
                refName = self.getName(refLabel)
                logger.debug("Name of referred item: %s", refName)
                if self.shape_tool.IsSimpleShape(refLabel):
                    logger.debug("Referred item is a Shape")
                    logger.debug("Name of Shape: %s", refName)
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
                    logger.debug("Referred item is an Assembly")
                    logger.debug("Name of Assembly: %s", refName)
                    name = self.getName(cLabel)  # Instance name
                    aLoc = TopLoc_Location()
                    # Location vector is carried by component
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
                    logger.debug("Assy name: %s", name)
                    logger.debug("Is Assembly? %s", isAssy)
                    logger.debug("Number of components: %s", rComps.Length())
                    if rComps.Length():
                        self.findComponents(refLabel, rComps)
        self.assyUidStack.pop()
        self.assyLocStack.pop()

    def read_file(self):
        """Build tree = treelib.Tree() to facilitate displaying the CAD model and

        constructing the tree view showing the assembly/component relationships.
        Each node of self.tree contains the following:
        (Name, UID, ParentUID, {Data}) where the Data keys are:
        'a' (isAssy?), 'l' (TopLoc_Location), 'c' (Quantity_Color), 's' (TopoDS_Shape)
        """
        logger.info("Reading STEP file")
        tmodel = TreeModel("STEP")
        self.shape_tool = tmodel.shape_tool
        self.color_tool = tmodel.color_tool

        step_reader = STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)

        status = step_reader.ReadFile(self.filename)
        if status == IFSelect_RetDone:
            logger.info("Transfer doc to STEPCAFControl_Reader")
            step_reader.Transfer(tmodel.doc)

        labels = TDF_LabelSequence()
        self.shape_tool.GetShapes(labels)
        logger.info('Number of labels at root : %i', labels.Length())
        try:
            rootlabel = labels.Value(1) # First label at root
        except RuntimeError:
            return
        name = self.getName(rootlabel)
        logger.info('Name of root label: %s', name)
        isAssy = self.shape_tool.IsAssembly(rootlabel)
        logger.info("First label at root holds an assembly? %s", isAssy)
        if isAssy:
            # If first label at root holds an assembly, it is the Top Assembly.
            # Through this label, the entire assembly is accessible.
            # there is no need to examine other labels at root explicitly.
            topLoc = TopLoc_Location()
            topLoc = self.shape_tool.GetLocation(rootlabel)
            self.assyLocStack.append(topLoc)
            entry = rootlabel.EntryDumpToString()
            logger.debug("Entry: %s", entry)
            logger.debug("Top assy name: %s", name)
            # Create root node for top assy
            newAssyUID = self.getNewUID()
            self.tree.create_node(name, newAssyUID, None,
                                  {'a': True, 'l': None, 'c': None, 's': None})
            self.assyUidStack.append(newAssyUID)
            topComps = TDF_LabelSequence() # Components of Top Assy
            subchilds = False
            isAssy = self.shape_tool.GetComponents(rootlabel, topComps, subchilds)
            logger.debug("Is Assembly? %s", isAssy)
            logger.debug("Number of components: %s", topComps.Length())
            logger.debug("Is Reference? %s", self.shape_tool.IsReference(rootlabel))
            if topComps.Length():
                self.findComponents(rootlabel, topComps)
        else:
            # Labels at root can hold solids or compounds (which are 'crude' assemblies)
            # Either way, we will need to create a root node in self.tree
            newAssyUID = self.getNewUID()
            self.tree.create_node(os.path.basename(self.filename),
                                  newAssyUID, None,
                                  {'a': True, 'l': None, 'c': None, 's': None})
            self.assyUidStack = [newAssyUID]
            for j in range(labels.Length()):
                label = labels.Value(j+1)
                name = self.getName(label)
                isAssy = self.shape_tool.IsAssembly(label)
                logger.debug("Label %i is assembly?: %s", j+1, isAssy)
                shape = self.shape_tool.GetShape(label)
                color = self.getColor(shape)
                isSimpleShape = self.shape_tool.IsSimpleShape(label)
                logger.debug("Is Simple Shape? %s", isSimpleShape)
                shapeType = shape.ShapeType()
                logger.debug("The shape type is: %i", shapeType)
                if shapeType == 0:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_COMPOUND")
                    topo = TopologyExplorer(shape)
                    #topo = aocutils.topology.Topo(shape)
                    logger.debug("Nb of compounds : %i", topo.number_of_compounds())
                    logger.debug("Nb of solids : %i", topo.number_of_solids())
                    logger.debug("Nb of shells : %i", topo.number_of_shells())
                    newAssyUID = self.getNewUID()
                    for i, solid in enumerate(topo.solids()):
                        name = "P%s" % str(i+1)
                        self.tree.create_node(name, self.getNewUID(),
                                              self.assyUidStack[-1],
                                              {'a': False, 'l': None,
                                               'c': color, 's': solid})
                elif shapeType == 2:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_SOLID")
                    self.tree.create_node(name, self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None,
                                           'c': color, 's': shape})
                elif shapeType == 3:
                    logger.debug("The shape type is OCC.Core.TopAbs.TopAbs_SHELL")
                    self.tree.create_node(name, self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None,
                                           'c': color, 's': shape})

        return tmodel.doc  # <class 'OCC.Core.TDocStd.TDocStd_Document'>
