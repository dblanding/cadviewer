import math
from OCC.gp import *
from OCC.GC import *
from OCC.BRep import *
from OCC.BRepBuilderAPI import *
from OCC.GCE2d import *
from OCC.Geom import *
from OCC.Geom2d import *
from OCC.GeomAPI import *
from OCC.GeomLProp import *
from OCC.BRepTools import breptools_UVBounds
from OCC.TopAbs import TopAbs_REVERSED
import OCCUtils.Construct
import OCC.BRepGProp
import OCC.GProp

#===========================================================================
# 
# Math & geometry 2D utility functions
# 
#===========================================================================

def intersection(cline1, cline2):
    """Return intersection (x,y) of 2 clines expressed as (a,b,c) coeff."""
    a,b,c = cline1
    d,e,f = cline2
    i = b*f-c*e
    j = c*d-a*f
    k = a*e-b*d
    if k:
        return (i/k, j/k)
    else:
        return None

def cnvrt_2pts_to_coef(pt1, pt2):
    """Return (a,b,c) coefficients of cline defined by 2 (x,y) pts."""
    x1, y1 = pt1
    x2, y2 = pt2
    a = y2 - y1
    b = x1 - x2
    c = x2*y1-x1*y2
    return (a, b, c)

def proj_pt_on_line(cline, pt):
    """Return point which is the projection of pt on cline."""
    a, b, c = cline
    x, y = pt
    denom = a**2 + b**2
    if not denom:
        return pt
    xp = (b**2*x - a*b*y -a*c)/denom
    yp = (a**2*y - a*b*x -b*c)/denom
    return (xp, yp)

def pnt_in_box_p(pnt, box):
    '''Point in box predicate: Return True if pnt is in box.'''
    x, y = pnt
    x1, y1, x2, y2 = box
    if x1<x<x2 and y1<y<y2: return True
    else: return False

def midpoint(p1, p2, f=.5):
    """Return point part way (f=.5 by def) between points p1 and p2."""
    return (((p2[0]-p1[0])*f)+p1[0], ((p2[1]-p1[1])*f)+p1[1])

def p2p_dist(p1, p2):
    """Return the distance between two points"""
    x, y = p1
    u, v = p2
    return math.sqrt((x-u)**2 + (y-v)**2)

def p2p_angle(p0, p1):
    """Return angle (degrees) from p0 to p1."""
    return math.atan2(p1[1]-p0[1], p1[0]-p0[0])*180/math.pi

def add_pt(p0, p1):
    return (p0[0]+p1[0], p0[1]+p1[1])

def sub_pt(p0, p1):
    return (p0[0]-p1[0], p0[1]-p1[1])

def line_circ_inters(x1, y1, x2, y2, xc, yc, r):
    '''Return list of intersection pts of line defined by pts x1,y1 and x2,y2
    and circle (cntr xc,yc and radius r).
    Uses algorithm from Paul Bourke's web page.'''
    intpnts = []
    num = (xc - x1)*(x2 - x1) + (yc - y1)*(y2 - y1)
    denom = (x2 - x1)*(x2 - x1) + (y2 - y1)*(y2 - y1)
    if denom == 0:
        return
    u = num / denom
    xp = x1 + u*(x2-x1)
    yp = y1 + u*(y2-y1)

    a = (x2 - x1)**2 + (y2 - y1)**2
    b = 2*((x2-x1)*(x1-xc) + (y2-y1)*(y1-yc))
    c = xc**2+yc**2+x1**2+y1**2-2*(xc*x1+yc*y1)-r**2
    q = b**2 - 4*a*c
    if q == 0:
        intpnts.append((xp, yp))
    elif q:
        u1 = (-b+math.sqrt(abs(q)))/(2*a)
        u2 = (-b-math.sqrt(abs(q)))/(2*a)
        intpnts.append(((x1 + u1*(x2-x1)), (y1 + u1*(y2-y1))))
        intpnts.append(((x1 + u2*(x2-x1)), (y1 + u2*(y2-y1))))
    return intpnts

def circ_circ_inters(x1, y1, r1, x2, y2, r2):
    '''Return list of intersection pts of 2 circles.
    Uses algorithm from Robert S. Wilson's web page.'''
    pts = []
    D = (x2-x1)**2 + (y2-y1)**2
    if not D:
        return pts  # circles have same cntr; no intersection
    try:
        q = math.sqrt(abs(((r1+r2)**2-D)*(D-(r2-r1)**2)))
    except:
        return pts  # circles don't interect
    pts = [((x2+x1)/2+(x2-x1)*(r1**2-r2**2)/(2*D)+(y2-y1)*q/(2*D),
            (y2+y1)/2+(y2-y1)*(r1**2-r2**2)/(2*D)-(x2-x1)*q/(2*D)),
           ((x2+x1)/2+(x2-x1)*(r1**2-r2**2)/(2*D)-(y2-y1)*q/(2*D),
            (y2+y1)/2+(y2-y1)*(r1**2-r2**2)/(2*D)+(x2-x1)*q/(2*D))]
    if same_pt_p(pts[0], pts[1]):
        pts.pop()   # circles are tangent
    return pts

def same_pt_p(p1, p2):
    '''Return True if p1 and p2 are within 1e-10 of each other.'''
    if p2p_dist(p1, p2) < 1e-6:
        return True
    else:
        return False

def cline_box_intrsctn(cline, box):
    """Return tuple of pts where line intersects edges of box."""
    x0, y0, x1, y1 = box
    pts = []
    segments = [((x0, y0), (x1, y0)),
                ((x1, y0), (x1, y1)),
                ((x1, y1), (x0, y1)),
                ((x0, y1), (x0, y0))]
    for seg in segments:
        pt = intersection(cline, cnvrt_2pts_to_coef(seg[0], seg[1]))
        if pt:
            if p2p_dist(pt, seg[0]) <= p2p_dist(seg[0], seg[1]) and \
               p2p_dist(pt, seg[1]) <= p2p_dist(seg[0], seg[1]):
                if pt not in pts:
                    pts.append(pt)
    return tuple(pts)

def para_line(cline, pt):
    """Return coeff of newline thru pt and parallel to cline."""
    a, b, c = cline
    x, y = pt
    cnew = -(a*x + b*y)
    return (a, b, cnew)

def para_lines(cline, d):
    """Return 2 parallel lines straddling line, offset d."""
    a, b, c = cline
    c1 = math.sqrt(a**2 + b**2)*d
    cline1 = (a, b, c + c1)
    cline2 = (a, b, c - c1)
    return (cline1, cline2)

def perp_line(cline, pt):
    """Return coeff of newline thru pt and perpend to cline."""
    a, b, c = cline
    x, y = pt
    cnew = a*y - b*x
    return (b, -a, cnew)

def closer(p0, p1, p2):
    """Return closer of p1 or p2 to point p0."""
    d1 = (p1[0] - p0[0])**2 + (p1[1] - p0[1])**2
    d2 = (p2[0] - p0[0])**2 + (p2[1] - p0[1])**2
    if d1 < d2: return p1
    else: return p2

def farther(p0, p1, p2):
    """Return farther of p1 or p2 from point p0."""
    d1 = (p1[0] - p0[0])**2 + (p1[1] - p0[1])**2
    d2 = (p2[0] - p0[0])**2 + (p2[1] - p0[1])**2
    if d1 > d2: return p1
    else: return p2

def find_fillet_pts(r, commonpt, end1, end2):
    """Return ctr of fillet (radius r) and tangent pts for corner
    defined by a common pt, and two adjacent corner pts."""
    line1 = cnvrt_2pts_to_coef(commonpt, end1)
    line2 = cnvrt_2pts_to_coef(commonpt, end2)
    # find 'interior' clines
    cl1a, cl1b = para_lines(line1, r)
    p2a = proj_pt_on_line(cl1a, end2)
    p2b = proj_pt_on_line(cl1b, end2)
    da = p2p_dist(p2a, end2)
    db = p2p_dist(p2b, end2)
    if da <= db: cl1 = cl1a
    else: cl1 = cl1b
    cl2a, cl2b = para_lines(line2, r)
    p1a = proj_pt_on_line(cl2a, end1)
    p1b = proj_pt_on_line(cl2b, end1)
    da = p2p_dist(p1a, end1)
    db = p2p_dist(p1b, end1)
    if da <= db: cl2 = cl2a
    else: cl2 = cl2b
    pc = intersection(cl1, cl2)
    p1 = proj_pt_on_line(line1, pc)
    p2 = proj_pt_on_line(line2, pc)
    return (pc, p1, p2)

def find_common_pt(apair, bpair):
    """Return (common pt, other pt from a, other pt from b), where a and b
    are coordinate pt pairs in (p1, p2) format."""
    p0, p1 = apair
    p2, p3 = bpair
    if same_pt_p(p0, p2):
        cp = p0     # common pt
        opa = p1    # other pt a
        opb = p3    # other pt b
    elif same_pt_p(p0, p3):
        cp = p0
        opa = p1
        opb = p2
    elif same_pt_p(p1, p2):
        cp = p1
        opa = p0
        opb = p3
    elif same_pt_p(p1, p3):
        cp = p1
        opa = p0
        opb = p2
    else:
        return
    return (cp, opa, opb)

def cr_from_3p(p1, p2, p3):
    """Return ctr pt and radius of circle on which 3 pts reside.
    From Paul Bourke's web page."""
    chord1 = cnvrt_2pts_to_coef(p1, p2)
    chord2 = cnvrt_2pts_to_coef(p2, p3)
    radial_line1 = perp_line(chord1, midpoint(p1, p2))
    radial_line2 = perp_line(chord2, midpoint(p2, p3))
    ctr = intersection(radial_line1, radial_line2)
    if ctr:
        radius =  p2p_dist(p1, ctr)
        return (ctr, radius)

def extendline(p0, p1, d):
    """Return point which lies on extension of line segment p0-p1,
    beyond p1 by distance d."""
    pts = line_circ_inters(p0[0], p0[1], p1[0], p1[1], p1[0], p1[1], d)
    if pts:
        return farther(p0, pts[0], pts[1])
    else:
        return

def shortenline(p0, p1, d):
    """Return point which lies on line segment p0-p1,
    short of p1 by distance d."""
    pts = line_circ_inters(p0[0], p0[1], p1[0], p1[1], p1[0], p1[1], d)
    if pts:
        return closer(p0, pts[0], pts[1])
    else:
        return

def line_tan_to_circ(circ, p):
    """Return tan pts on circ of line through p."""
    c, r = circ
    d = p2p_dist(c, p)
    ang0 = p2p_angle(c, p)*math.pi/180
    theta = math.asin(r/d)
    ang1 = ang0+math.pi/2-theta
    ang2 = ang0-math.pi/2+theta
    p1 = (c[0]+(r*math.cos(ang1)), c[1]+(r*math.sin(ang1)))
    p2 = (c[0]+(r*math.cos(ang2)), c[1]+(r*math.sin(ang2)))
    return (p1, p2)

def line_tan_to_2circs(circ1, circ2):
    """Return tangent pts on line tangent to 2 circles.
    Order of circle picks determines which tangent line."""
    c1, r1 = circ1
    c2, r2 = circ2
    d = p2p_dist(c1, c2)    # distance between centers
    ang_loc = p2p_angle(c2, c1)*math.pi/180  # angle of line of centers
    f = (r2/r1-1)/d # reciprocal dist from c1 to intersection of loc & tan line
    theta = math.asin(r1*f)    # angle between loc and tangent line
    ang1 = (ang_loc + math.pi/2 - theta)
    ang2 = (ang_loc - math.pi/2 + theta)
    p1 = (c1[0]+(r1*math.cos(ang1)), c1[1]+(r1*math.sin(ang1)))
    p2 = (c2[0]+(r2*math.cos(ang1)), c2[1]+(r2*math.sin(ang1)))
    return (p1, p2)

def angled_cline(pt, angle):
    """Return cline through pt at angle (degrees)"""
    ang = angle * math.pi / 180
    dx = math.cos(ang)
    dy = math.sin(ang)
    p2 = (pt[0]+dx, pt[1]+dy)
    cline = cnvrt_2pts_to_coef(pt, p2)
    return cline

def ang_bisector(p0, p1, p2, f=0.5):
    """Return cline coefficients of line through vertex p0, factor=f
    between p1 and p2."""
    ang1 = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
    ang2 = math.atan2(p2[1]-p0[1], p2[0]-p0[0])
    deltang = ang2 - ang1
    ang3 = (f * deltang + ang1)*180/math.pi
    return angled_cline(p0, ang3)


def pt_on_RHS_p(pt, p0, p1):
    """Return True if pt is on right hand side going from p0 to p1."""
    angline = p2p_angle(p0, p1)
    angpt = p2p_angle(p0, pt)
    if angline >= 0:
        if angline > angpt > angline-180:
            return True
    else:
        angline += 360
        if angpt < 0:
            angpt += 360
        if angline > angpt > angline-180:
            return True

def rotate_pt(pt, ang, ctr):
    """Return coordinates of pt rotated ang (deg) CCW about ctr.
    This is a 3-step process:
    1. translate to place ctr at origin.
    2. rotate about origin (CCW version of Paul Bourke's algorithm.
    3. apply inverse translation. """
    x, y = sub_pt(pt, ctr)
    A = ang * math.pi / 180
    u = x * math.cos(A) - y * math.sin(A)
    v = y * math.cos(A) + x * math.sin(A)
    return add_pt((u, v), ctr)

#===========================================================================

class WorkPlane(object):
    """
    A 2D plane for making 2D profiles to create and modify 3D geometry.
    Workplane is defined by an (invisible) underlying surface of type=Geom_Plane.
    There are three typical ways for creating a new workplane:
    1- Lying in an existing face, with U-dir specified by normal dir of another face
    2- By specification of a gp_Ax3 axis
    3- Default (located at the Origin in the X-Y plane, with U,V,W aligned with X,Y,Z)
    """
    def __init__(self, size, face=None, faceU=None, ax3=None):
        # gp_Ax3 of XYZ coord system
        origin = gp_Pnt(0,0,0)
        wDir = gp_Dir(0,0,1)
        uDir = gp_Dir(1,0,0)
        vDir = gp_Dir(0,1,0)
        xyzAx3 = gp_Ax3(origin, wDir, uDir)          
        if (not face and not ax3):  # create default wp (in XY plane at 0,0,0)
            axis3 = xyzAx3
            gpPlane = gp_Pln(xyzAx3)
            self.gpPlane = gpPlane              # type: gp_Pln
            self.plane = Geom_Plane(gpPlane)    # type: Geom_Plane
            self.surface = Handle_Geom_Surface(Geom_Plane(gpPlane)) # type: Handle_Geom_Surface
        elif face:  # create workplane on face, uDir defined by faceU
            wDir = OCCUtils.Construct.face_normal(face)
            props = OCC.GProp.GProp_GProps()
            OCC.BRepGProp.brepgprop_SurfaceProperties(face, props)
            origin = props.CentreOfMass()
            '''
            surface = BRep_Tool_Surface(face) # type: Handle_Geom_Surface
            plane = Handle_Geom_Plane.DownCast(surface).GetObject() # type: Geom_Plane
            gpPlane = plane.Pln() # type: gp_Pln
            origin = gpPlane.Location() # type: gp_Pnt
            '''
            uDir = OCCUtils.Construct.face_normal(faceU)
            axis3 = gp_Ax3(origin, wDir, uDir)
            vDir = axis3.YDirection()
            self.gpPlane = gp_Pln(axis3)
            self.plane = Geom_Plane(self.gpPlane)    # type: Geom_Plane
            self.surface = Handle_Geom_Surface(self.plane) # type: Handle_Geom_Surface
        elif ax3:
            axis3 = ax3
            uDir = axis3.XDirection()
            vDir = axis3.YDirection()
            wDir = axis3.Axis().Direction()
            origin = axis3.Location()
            self.gpPlane = gp_Pln(axis3)
            self.plane = Geom_Plane(self.gpPlane)    # type: Geom_Plane
            self.surface = Handle_Geom_Surface(self.plane) # type: Handle_Geom_Surface
            
        self.Trsf = gp_Trsf()
        self.Trsf.SetTransformation(axis3)
        self.Trsf.Invert()
        self.origin = origin
        self.uDir = uDir
        self.vDir = vDir
        self.wDir = wDir
        self.face = face
        self.size = size
        self.border = self.makeWpBorder(self.size)
        self.clList = [] # List of 'native' construction lines
        self.clineList = [] # List of pyOCC construction lines
        self.ccircList = [] # List of pyOCC construction circles
        self.wireList = [] # List of pyOCC wires
        self.wire = None
        self.hvcl((0,0))    # Make H-V clines through origin
        self.accuracy = 0.001   # min distance between two points
        
    def makeSqProfile(self, size):
        # points and segments need to be in CW sequence to get W pointing along Z
        p1 = gp_Pnt2d(-size, size)
        p2 = gp_Pnt2d(size, size)
        p3 = gp_Pnt2d(size, -size)
        p4 = gp_Pnt2d(-size, -size)
        seg1 = GCE2d_MakeSegment(p1, p2)
        seg2 = GCE2d_MakeSegment(p2, p3)
        seg3 = GCE2d_MakeSegment(p3, p4)
        seg4 = GCE2d_MakeSegment(p4, p1)
        e1 = BRepBuilderAPI_MakeEdge(seg1.Value(), self.surface)
        e2 = BRepBuilderAPI_MakeEdge(seg2.Value(), self.surface)
        e3 = BRepBuilderAPI_MakeEdge(seg3.Value(), self.surface)
        e4 = BRepBuilderAPI_MakeEdge(seg4.Value(), self.surface)
        aWire = BRepBuilderAPI_MakeWire(e1.Edge(), e2.Edge(), e3.Edge(), e4.Edge())
        myWireProfile = aWire.Wire()
        return myWireProfile # TopoDS_Wire

    def makeWpBorderAlt(self, size): # This doesn't produce a visible border
        wireProfile = self.makeSqProfile(size)
        mkf = BRepBuilderAPI_MakeFace()
        mkf.Init(self.surface, False, 1e-6)
        mkf.Add(wireProfile)
        mkf.Build()
        if mkf.IsDone():
            border = mkf.Face()
        return border

    def makeWpBorder(self, size):
        wireProfile = self.makeSqProfile(size)
        myFaceProfile = BRepBuilderAPI_MakeFace(wireProfile)
        if myFaceProfile.IsDone():
            border = myFaceProfile.Face()
        return border # TopoDS_Face

    #=======================================================================
    # Construction
    # construction lines (clines) are "infinite" length lines
    # described by the equation:            ax + by + c = 0
    # they are defined by coefficients:     (a, b, c)
    #
    # circles are defined by coordinates:   (pc, r)
    # points are defined by coordinates:    (x, y)
    #=======================================================================

    def cline_gen(self, cline):
        '''Generate a cline extending to the edge of the border.
        cline coords (a,b,c) are in (mm) values.'''
        self.clList.append(cline)
        # TopLft & BotRgt corners of the border
        trimbox = (-self.size, self.size, self.size, -self.size)
        endpts = cline_box_intrsctn(cline, trimbox)
        if len(endpts) == 2:
            ep1, ep2 = endpts
            aPnt1 = gp_Pnt2d(ep1[0], ep1[1])
            aPnt2 = gp_Pnt2d(ep2[0], ep2[1])
            aSegment = GCE2d_MakeSegment(aPnt1, aPnt2).Value() #type: Handle_Geom2d_TrimmedCurve
            # convert 2d line segment to 3d line
            aLine = geomapi_To3d(aSegment, self.gpPlane) # type: Handle_Geom_Curve
            self.clineList.append(aLine)

    def hcl(self, pnt=None):
        """Create horizontal construction line from a point (x,y)."""
        if pnt:
            cline = angled_cline(pnt, 0)
            self.cline_gen(cline)

    def vcl(self, pnt=None):
        """Create vertical construction line from a point (x,y)."""
        if pnt:
            cline = angled_cline(pnt, 90)
            self.cline_gen(cline)

    def hvcl(self, pnt=None):
        """Create a horiz & vert construction line pair at a point."""
        if pnt:
            self.cline_gen(angled_cline(pnt, 0))
            self.cline_gen(angled_cline(pnt, 90))

    def acl(self, pnt1, pnt2=None, ang=None):
        """Create a construction line thru a first point, then through
        a second specified point or at a specified angle."""
        if pnt1 and pnt2:
            cline = cnvrt_2pts_to_coef(pnt1, pnt2)
            self.cline_gen(cline)
        elif pnt1 and ang:
            cline = angled_cline(pnt1, ang)
            self.cline_gen(cline)

    def lbcl(self, p1, p2, f=.5):
        """Create a linear bisector construction line."""
        p0 = midpoint(p1, p2, f)
        baseline = cnvrt_2pts_to_coef(p1, p2)
        newline = perp_line(baseline, p0)
        self.cline_gen(newline)

    def intersectPts(self):
        """Return list of intersection points among construction lines
        """
        lineList = list(self.clList) # copy list of 'native' 2d lines
        pointList = []  # List of 'native' 2d points
        for i in range(len(lineList)):
            line0 = lineList.pop()
            for line in lineList:
                P = intersection(line0, line)
                if P:
                    if not pointList:
                        pointList.append(P) # first point in list
                    else:
                        for point in pointList:
                            if p2p_dist(P, point) > self.accuracy:
                                if P not in pointList:
                                    pointList.append(P)
                        
        pntList = []    # list of gp_Pnt2d points
        for point in pointList:
            if point:
                x,y = point
                pnt = gp_Pnt(x,y,0)
                pnt.Transform(self.Trsf)
                pntList.append(pnt)
        return pntList

    def circ(self, cntr, rad, constr=False):
        """Create a construction circle """
        cx, cy = cntr
        cntrPt = gp_Pnt(cx, cy, 0)
        ax2 = gp_Ax2(cntrPt, gp_Dir(0,0,1))
        geomCirc = Geom_Circle(ax2, rad)
        geomCirc.Transform(self.Trsf)
        if constr:
            self.ccircList.append(geomCirc)
        else:
            edge = BRepBuilderAPI_MakeEdge(Handle_Geom_Curve(geomCirc))
            self.wire = BRepBuilderAPI_MakeWire(edge.Edge()).Wire()
            self.wireList.append(self.wire)
