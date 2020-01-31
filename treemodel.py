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

from OCC.Core.TCollection import (TCollection_ExtendedString,
                                  TCollection_AsciiString)
from OCC.Core.TDataStd import TDataStd_Name, TDataStd_Name_GetID
from OCC.Core.TDF import (TDF_Label, TDF_LabelSequence,
                          TDF_ChildIterator)
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool,
                              XCAFDoc_DocumentTool_LayerTool,
                              XCAFDoc_DocumentTool_MaterialTool,
                              XCAFDoc_ColorSurf)


class TreeModel():
    """XCAF Tree Model of heirarchical CAD assembly data."""

    def __init__(self, title):
        # Create the application and document
        doc = TDocStd_Document(TCollection_ExtendedString(title))
        app = XCAFApp_Application_GetApplication()
        app.NewDocument(TCollection_ExtendedString("MDTV-CAF"), doc)
        self.app = app
        self.doc = doc
        # Initialize tools
        self.shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
        self.shape_tool.SetAutoNaming(True)
        self.color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())
        self.layer_tool = XCAFDoc_DocumentTool_LayerTool(doc.Main())
        self.l_materials = XCAFDoc_DocumentTool_MaterialTool(doc.Main())
        self.allChildLabels = []

    def getChildLabels(self, label):
        """Return list of child labels directly below label."""
        itlbl = TDF_ChildIterator(label, True)
        childlabels = []
        while itlbl.More():
            childlabels.append(itlbl.Value())
            itlbl.Next()
        return childlabels

    def getAllChildLabels(self, label, first=True):
        """Return list of all child labels (recursively) below label.

        This doesn't find anything at the second level down because
        the component labels of root do not have children, but rather
        they have references."""
        print("Entering 'getAllChildLabels'")
        if first:
            self.allChildlabels = []
        childlabels = self.getChildLabels(label)
        print(f"len(childLabels) = {len(childlabels)}")
        self.allChildlabels += childlabels
        print(f"len(allChildLabels) = {len(self.allChildlabels)}")
        for lbl in childlabels:
            self.getAllChildLabels(lbl, first=False)
        return self.allChildlabels

    def saveDoc(self, filename):
        """Save doc to file (for educational purposes) (not working yet)
        """
        logger.debug("Saving doc to file")
        savefilename = TCollection_ExtendedString(filename)
        app.SaveAs(doc, savefilename)
