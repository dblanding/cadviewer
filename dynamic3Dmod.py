"""Dynamic 3D Modification functions excised from cadViewer while
work proceeds to get all the other stuff working. 
"""

#############################################
#
# Dynamic 3D Modification functons...
#
#############################################

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

