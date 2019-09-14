def tweakFace(mFace, workPart, tPlane):
    # Move mFace (on workPart) to target plane
    # All other faces remain in their original planes.
    # Only works if all adjacent faces are planar.
    """
    The algorithm is to first find the four vertices of mFace (to be moved) then
    at each vertex, identify the edge that is *not* contained in mFace. The
    intersection of each of these edges with the target plane is a new vertex.
    The mFace is replaced by a new face defined by the four new vertices.
    The adjacent faces are stretched to the new vertices, remaining in their
    initial planes. The part is then sewn back together.
    """
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
                newPntList.append(intersectPnt(line, tPlane))
                break

    print 'number of new points = ', len(newPntList)

    for i in range(len(newPntList)):
        P = newPntList[i]
        display.DisplayShape(P)
        pstring = "P%i" % i
        display.DisplayMessage(P, pstring)


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
    tolerance = 1e-7
    sew = BRepBuilderAPI_Sewing(tolerance)
    
    print 'Number of other faces: ', len(otherFaces)
    for f in otherFaces:
        sew.Add(f)
    
    for f in adjFaces:
        sew.Add(f)
    sew.Add(newFace)
    sew.Perform()
    res = sew.SewedShape()
    return res

def makeToolBody(mFace, tPlane):
    # Make toolBody on mFace (of active part) to target surface.
    # (target surface is ignored for now) Far face is parallel to mFace.
    # All other faces remain in their original planes.
    """
    This algorithm follows the procedure of the 'intelligent local operation'
    used by HP SolidDesigner, in which a toolbody is constructed so that its
    'near' face mates against mFace and its 'far' face is aligned to the target
    surface. The toolbody's 'side faces' align with the faces adjacent to mFace
    on the workpart. The toolbody can then be fused to the workpart so mFace
    gets effectively 'moved' out to the target surface. If the target surface is
    'inside' the workpart, then the toolbody is subtracted from the workpart.
    
    Here it is in detail, assuming mFace is planar and has only one wire (no
    holes.) Target surface is assumed to be completely outside the workpart.
    
    Use the underlying wire of mFace to create an identical tool face which can
    then be extruded into a prism. The side faces of the prism will corespond
    exactly with the edges of mFace. This prism becomes the toolbody.
    One by one, tweak the adjacent faces of the toolbody into alignment with the
    adjacent faces of the workpart, and align the 'far' face of the prism to the
    target surface. To correlate the toolbody side faces with the sidefaces of
    the workPart to which they will become aligned, keep track of their common
    edge. 
    """
    workPart = win.activePart
    wrkPrtUID = win.activePartUID
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
    nEdges = 0
    for edge in topo.ordered_edges_from_wire(mF_wire):
        mF_edgeList.append(edge)
        nEdges += 1
    
    # make an ordered list of faces adjacent to mFace
    faces = topo.faces_from_solids(win.activePart) # all faces
    adjFacesDict = {} # key=seq : value=face
    for face in faces:
        edges = topo.edges_from_face(face)
        if face.IsSame(mFace):
            pass # This is mFace
        else:
            adjacentFace = False # assume face is not adjacent...
            for e in edges:
                seq = 0 # keep track of which edge in ordered list is matched
                for f in mF_edgeList:
                    seq += 1
                    if (hash(e) == hash(f)): # common edge
                        adjacentFace = True # until discovered that it is
                        break
                if adjacentFace:
                    break
            if adjacentFace:
                adjFacesDict[seq] = face
    mF_adjFaceList = adjFacesDict.values() # ordered list of adjacent faces
    
    # create a toolBody that mates against mFace
    faceNormal = Construct.face_normal(mFace) # type: gp_Dir
    vctr = gp_Vec(faceNormal).Multiplied(10)
    toolBody = BRepPrimAPI_MakePrism(mFace, vctr).Shape()

    # find toolBody face sharing an edge with workpart adjacent face
    # compare face normals to see if toolBody face needs to be tweaked
    # keep track by index of wp ordered list
    facesToTweak = {} # key = edge index ; value = toolBody faceNormal
    tb_topo = Topology.Topo(toolBody)
    tb_faces = tb_topo.faces_from_solids(toolBody) # all faces of toolBody
    for i in range(len(mF_edgeList)):
        print i
        we = mF_edgeList[i] # workpart edge
        for tb_face in tb_faces:
            adjacentFace = False # assume face is not adjacent...
            if tb_face.IsSame(mFace):
                print 'found mated face'
            else:
                tb_edges = tb_topo.edges_from_face(tb_face)
                for tb_e in tb_edges:
                    if tb_e.IsSame(we): # common edge
                        adjacentFace = True # until discovered that it is
                        #break
                if adjacentFace:
                    print 'found TB face matching workPart adjFace %i:' % i
                    # check coplanarity between tb_face and wp_face
                    wp_face = mF_adjFaceList[i]
                    wpFaceNormal = Construct.face_normal(wp_face) # type: gp_Dir
                    tbFaceNormal = Construct.face_normal(tb_face) # type: gp_Dir
                    angle = wpFaceNormal.Angle(tbFaceNormal)
                    if angle > 1e-10:
                        print 'face needs to be tweaked'
                        facesToTweak[i] = tbFaceNormal
                    else:
                        print 'no need to tweak face'
                    break
                else:
                    print 'found other face'

    # Tweak toolBody faces that need to be aligned to workPart faces
    for k,v in facesToTweak.items():
        print 'Tweaking face ', k
        tb_topo = Topology.Topo(toolBody)
        tb_faces = tb_topo.faces_from_solids(toolBody) # all faces of toolBody
        targetFace = mF_adjFaceList[k]
        targetPlane = planeOfFace(targetFace)
        for tb_face in tb_faces:
            tbFaceNormal = Construct.face_normal(tb_face)
            angle = tbFaceNormal.Angle(v)
            if angle < 1e-10:
                sharedEdge = edgeOnFaceP(mF_edgeList[k], tb_face)
                if sharedEdge:
                    print 'Common edge test: ', sharedEdge
                    toolBody = tweakFace(tb_face, toolBody, targetPlane)
    win.getNewPartUID(toolBody)
                
def alignFace(initial=True):
    """
    Align a selected face on the active part to some other face.
    This involves 'stretching' adjacent faces to reach the new aligned face.
    All the faces (of the active part) are then sewn back together.
    """
    # This only works if all adjacent faces are planar.
    
    if initial:
        win.registerCallback(alignFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        tFace = win.faceStack.pop() # target face (to be aligned to)
        tPlane = planeOfFace(tFace)
        mFace = win.faceStack.pop() # face to be moved
        res = tweakFace(mFace, workPart, tPlane)
        win.getNewPartUID(res, ancestor=wrkPrtUID)

        win.statusBar().showMessage('Align Face operation complete')
        win.clearCallback()
        
def offsetEndFace(initial=True):
    """
    Offset one end face of a simple cylinder (the active part) by a dist value.
    This involves 'stretching' the cylindrical face to reach the new end face.
    The faces are then sewn back together.
    """
    if initial:
        win.registerCallback(offsetEndFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif (win.lineEditStack and win.faceStack):
        text = win.lineEditStack.pop()
        value = float(text) * win.unitscale
        mFace = win.faceStack.pop() # face to be moved
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        topo = Topology.Topo(workPart)
        faces = topo.faces_from_solids(workPart) # all faces
        for face in faces:
            '''
            This is tricky.
            Below, I decide a face is cylindrical if it has three edges.
            But that is only true if the cylinder is one 360-deg face.
            As I discovered in the 'plate' part of the step file,
            those cylindrical holes were comprised of two 180-deg faces,
            each with 4 edges. So this is not going to be reliable.

            Maybe it would be smarter to first decide whether a face
            is the end face of a cylinder, then look for adjacent faces.

            That gives me two problems that need reliable solutions:
            1- How to test whether a face is the end face of a cylinder
            2- How to find adjacent cylinder faces

            I recall a short utility function for testing 'IsPlanar'...
            '''
            nbrEdges = topo.number_of_edges_from_face(face)
            print nbrEdges
            edges = topo.edges_from_face(face)
            if face == mFace: # This is the face to be moved
                pass
            elif nbrEdges == 3:
                cylFace = face
            else:
                othrEndFace = face
        print '\n'
        print 'Topology Info for mFace:'
        face = mFace
        print 'Number of Edges of mFace = ', topo.number_of_edges_from_face(face)
        print '\n'
        faceEdges = topo.edges_from_face(face)
        for faceEdge in faceEdges:
            hCurve, umin, umax = BRep_Tool.Curve(faceEdge)
            curve = hCurve.GetObject()
            vectr = curve.DN(0.0, 2)
            print 'curvature at u=0: ', vectr.Magnitude()
            print 'first: ', curve.FirstParameter()
            print 'last: ', curve.LastParameter()
            print '\n'
        print 'Number of Vertices of mFace = ', topo.number_of_vertices_from_face(face)

        print '\n'
        print 'Topology Info for cylFace:'
        face = cylFace
        print 'Number of Edges of cylFace = ', topo.number_of_edges_from_face(face)
        print '\n'
        faceEdges = topo.edges_from_face(face)
        for faceEdge in faceEdges:
            hCurve, umin, umax = BRep_Tool.Curve(faceEdge)
            curve = hCurve.GetObject()
            vectr = curve.DN(0.0, 2)
            print 'curvature at u=0: ', vectr.Magnitude()
            print 'first: ', curve.FirstParameter()
            print 'last: ', curve.LastParameter()
            print '\n'
        print 'Number of Vertices of cylFace = ', topo.number_of_vertices_from_face(face)
        brlSurf = BRepLib_FindSurface(face) # type: BRepLib_FindSurface
        print type(brlSurf)
        isPlanarSurf = GeomLib_IsPlanarSurface(brlSurf.Surface(), TOLERANCE).IsPlanar()
        print 'Planar: ', isPlanarSurf
        mFaceVertices = topo.vertices_from_face(mFace)
        
        win.statusBar().showMessage('Offset Face operation complete')
        win.clearCallback()
        
def offsetEndFaceC(shapeList, *kwargs):  # callback (collector) for offsetEndFace
    print shapeList
    print kwargs
    win.lineEdit.setFocus()
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if (win.faceStack and win.lineEditStack):
        offsetEndFace(initial=False)
    elif len(win.faceStack) == 1:
        statusText = "Enter distance value."
        win.statusBar().showMessage(statusText)

def alignEndFace(initial=True):
    """
    Align one end face of a simple cylinder (the active part) to a target face.
    This involves 'stretching' the cylindrical face to reach the new end face.
    The faces are then sewn back together.
    """
    if initial:
        win.registerCallback(alignEndFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        tFace = win.faceStack.pop() # target face
        tSurf = BRep_Tool_Surface(tFace)
        mFace = win.faceStack.pop() # face to be moved
        workPart = win.activePart
        wrkPrtUID = win.activePartUID
        topo = Topology.Topo(workPart)
        faces = topo.faces_from_solids(workPart) # all faces
        for face in faces:
            isPlanar = face_is_plane(face)
            print 'Planar: ', isPlanar
            if face == mFace:
                print 'found mFace'
            elif isPlanar:
                otherEndFace = face
                print 'found other end face'
            else:
                cylFace = face
                print 'found cylFace'
        cylSurf = BRep_Tool_Surface(cylFace)
        cylEdges = [] # edges of new cylindrical face
        for face in (tFace, otherEndFace):
            planeSurf = BRep_Tool_Surface(face)
            inters = GeomAPI_IntSS()
            inters.Perform(cylSurf, planeSurf, 1.0e-7)
            if inters.IsDone():
                nbLines = inters.NbLines()
                print nbLines
                curve = inters.Line(nbLines) # type: Handle_Geom_curve
                edge = BRepBuilderAPI_MakeEdge(curve).Edge()
                cylEdges.append(edge)
        newCylFace = brepfill.Face(cylEdges[0], cylEdges[1])
        newWire = BRepBuilderAPI_MakeWire(cylEdges[0]).Wire()
        newFace = BRepBuilderAPI_MakeFace(newWire).Face()
        # sew all the faces together
        tolerance = 1e-7
        sew = BRepBuilderAPI_Sewing(tolerance)
        sew.Add(otherEndFace)
        sew.Add(newCylFace)
        sew.Add(newFace)
        sew.Perform()
        res = sew.SewedShape()
        win.getNewPartUID(res, ancestor=wrkPrtUID)
        win.statusBar().showMessage('Offset Face operation complete')
        win.clearCallback()
        
def alignEndFaceC(shapeList, *kwargs):  # callback (collector) for alignEndFace
    print shapeList
    print kwargs
    win.lineEdit.setFocus()
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if len(win.faceStack) == 1:
        statusText = "Select target face."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        alignEndFace(initial=False)
    
def testFace(initial=True):
    """
    Test makeToolBody
    """
    
    if initial:
        win.registerCallback(testFaceC)
        display.SetSelectionModeFace()
        statusText = "Select face to move (on active part)."
        win.statusBar().showMessage(statusText)
    elif len(win.faceStack) == 2:
        tFace = win.faceStack.pop() # target face (to be aligned to)
        tPlane = planeOfFace(tFace)
        mFace = win.faceStack.pop() # face to be moved
        makeToolBody(mFace, tPlane)
        win.statusBar().showMessage('Align Face operation complete')
        win.clearCallback()
        
def testFaceC(shapeList, *kwargs):  # callback (collector) for testFace
    print shapeList
    print kwargs
    for shape in shapeList:
        face = topods_Face(shape)
        win.faceStack.append(face)
    if len(win.faceStack) == 1:
        statusText = "Select face to align to."
        win.statusBar().showMessage(statusText)
    if len(win.faceStack) == 2:
        testFace(initial=False)

