#
# myStepXcafReader.py
# The goal of this module is to be able to read (and write) step files with complete
# Assembly / Part structure, including the names of parts and assemblies, colors
# of parts, and with all components shown in their correct positions.
# The latest  version of this file can be found at:
# https://sites.google.com/site/pythonocc/
#
# Author: Doug Blanding   <dblanding at gmail dot com>
#
# myStepXcafReader is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# myStepXcafReader is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# if not, write to the Free Software Foundation, Inc.
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#


from __future__ import print_function

import logging
import os.path
import OCC.BRep
import OCC.IFSelect
import OCC.Interface
import OCC.Quantity
import OCC.STEPCAFControl
import OCC.STEPControl
import OCC.TDataStd
import OCC.TCollection
import OCC.TColStd
import OCC.TDF
import OCC.TDocStd
import OCC.TopAbs
import OCC.TopoDS
import OCC.XCAFApp
import OCC.XCAFDoc
import OCC.XSControl
import aocutils.topology
import treelib

logger = logging.getLogger(__name__)
logger.setLevel(20) # 20 for info only

class StepXcafImporter(object):
    """
    Read a step file with the goal of collecting a complete and accurate
    Assembly/Part structure, including the names of parts and assemblies,
    part color, and with all components shown in their correct positions.
    Data stored in self.tree
    """
    def __init__(self, filename, nextUID=0):

        self.filename = filename
        self.tree = treelib.tree.Tree()  # to hold assembly structure
        self._currentUID = nextUID
        self.assyUidStack = [0]
        self.assyLocStack = []
        
        self.read_file()

    def getNewUID(self):
        uid = self._currentUID + 1
        self._currentUID = uid
        return uid

    def getName(self, label):
        # Get the part name
        h_name = OCC.TDataStd.Handle_TDataStd_Name()
        label.FindAttribute(OCC.TDataStd.TDataStd_Name_GetID(), h_name)
        strdump = h_name.GetObject().DumpToString()
        name = strdump.split('|')[-2]
        return name
        
    def getColor(self, shape):
        # Get the part color
        #string_seq = self.layer_tool.GetObject().GetLayers(shape)
        color = OCC.Quantity.Quantity_Color()
        self.color_tool.GetObject().GetColor(shape,
                                             OCC.XCAFDoc.XCAFDoc_ColorSurf, color)
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
            refLabel = OCC.TDF.TDF_Label()
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
                    aLoc = OCC.TopLoc.TopLoc_Location()
                    aLoc = self.shape_tool.GetLocation(cLabel)
                    self.assyLocStack.append(aLoc)
                    newAssyUID = self.getNewUID()
                    self.tree.create_node(name,
                                          newAssyUID,
                                          self.assyUidStack[-1],
                                          {'a': True, 'l': aLoc, 'c': None, 's': None})
                    self.assyUidStack.append(newAssyUID)
                    rComps = OCC.TDF.TDF_LabelSequence() # Components of Assy
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
        """
        Build self.tree (treelib.Tree()) containing the CAD data read from a step file.
        Each node of self.tree contains the following: 
        (Name, UID, ParentUID, {Data}) where the Data keys are:
        'a' (isAssy?), 'l' (TopLoc_Location), 'c' (Quantity_Color), 's' (TopoDS_Shape)
        """
        logger.info("Reading STEP file")
        h_doc = OCC.TDocStd.Handle_TDocStd_Document()

        # Create the application
        app = OCC.XCAFApp._XCAFApp.XCAFApp_Application_GetApplication().GetObject()
        app.NewDocument(OCC.TCollection.TCollection_ExtendedString("MDTV-CAF"), h_doc)

        # Get root shapes
        doc = h_doc.GetObject()
        h_shape_tool = OCC.XCAFDoc.XCAFDoc_DocumentTool().ShapeTool(doc.Main())
        self.color_tool = OCC.XCAFDoc.XCAFDoc_DocumentTool().ColorTool(doc.Main())
        self.layer_tool = OCC.XCAFDoc.XCAFDoc_DocumentTool().LayerTool(doc.Main())
        
        step_reader = OCC.STEPCAFControl.STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)

        status = step_reader.ReadFile(str(self.filename))

        if status == OCC.IFSelect.IFSelect_RetDone:
            logger.info("Transfer doc to STEPCAFControl_Reader")
            step_reader.Transfer(doc.GetHandle())

        labels = OCC.TDF.TDF_LabelSequence()
        # TopoDS_Shape a_shape;
        self.shape_tool = h_shape_tool.GetObject()
        self.shape_tool.GetShapes(labels)
        logger.info('Number of labels at root : %i' % labels.Length())
        label = labels.Value(1) # First label at root
        name = self.getName(label)
        isAssy = self.shape_tool.IsAssembly(label)
        logger.info("First label at root holds an assembly? %s" % isAssy)
        if isAssy:
            # If first label at root holds an assembly, it is the Top Assembly.
            # Through this label, the entire assembly is accessible.
            # No need to examine other labels at root explicitly.
            topLoc = OCC.TopLoc.TopLoc_Location()
            topLoc = self.shape_tool.GetLocation(label)
            self.assyLocStack.append(topLoc)
            entry = label.EntryDumpToString()
            logger.debug("Entry: %s" % entry)
            logger.debug("Top assy name: %s" % name)
            # Create root node for top assy
            newAssyUID = self.getNewUID()
            self.tree.create_node(name,
                                  newAssyUID,
                                  None,
                                  {'a': True, 'l': None, 'c': None, 's': None})
            self.assyUidStack.append(newAssyUID)
            topComps = OCC.TDF.TDF_LabelSequence() # Components of Top Assy
            subchilds = False
            isAssy = self.shape_tool.GetComponents(label, topComps, subchilds)
            logger.debug("Is Assembly? %s" % isAssy)
            logger.debug("Number of components: %s" % topComps.Length())
            logger.debug("Is Reference? %s" % self.shape_tool.IsReference(label))
            if topComps.Length():
                self.findComponents(label, topComps)
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
                isAssy = self.shape_tool.IsAssembly(label)
                logger.debug("Label %i is assembly?: %s" % (j+1, isAssy))
                shape = self.shape_tool.GetShape(label)
                color = self.getColor(shape)
                isSimpleShape = self.shape_tool.IsSimpleShape(label)
                logger.debug("Is Simple Shape? %s" % isSimpleShape)
                shapeType = shape.ShapeType()
                logger.debug("The shape type is: %i" % shapeType)
                if shapeType == 0:
                    logger.debug("The shape type is OCC.TopAbs.TopAbs_COMPOUND")
                    topo = aocutils.topology.Topo(shape)
                    logger.debug("Nb of compounds : %i" % topo.number_of_compounds)
                    logger.debug("Nb of solids : %i" % topo.number_of_solids)
                    logger.debug("Nb of shells : %i" % topo.number_of_shells)
                    newAssyUID = self.getNewUID()
                    for i, solid in enumerate(topo.solids):
                        name = "P%s" % str(i+1)
                        self.tree.create_node(name,
                                              self.getNewUID(),
                                              self.assyUidStack[-1],
                                              {'a': False, 'l': None, 'c': color, 's': solid})
                elif shapeType == 2:
                    logger.debug("The shape type is OCC.TopAbs.TopAbs_SOLID")
                    self.tree.create_node(name,
                                          self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None, 'c': color, 's': shape})
                elif shapeType == 3:
                    logger.debug("The shape type is OCC.TopAbs.TopAbs_SHELL")
                    self.tree.create_node(name,
                                          self.getNewUID(),
                                          self.assyUidStack[-1],
                                          {'a': False, 'l': None, 'c': color, 's': shape})
                
        return True

