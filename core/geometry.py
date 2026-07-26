from math import radians,sin,cos,atan2,sqrt,degrees
R=6371.0088
def haversine_km(a,b,c,d):
    p1,p2=radians(a),radians(c); dp=radians(c-a); dl=radians(d-b)
    x=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*R*atan2(sqrt(x),sqrt(1-x))
def bearing_deg(a,b,c,d):
    p1,p2=radians(a),radians(c); dl=radians(d-b)
    return (degrees(atan2(sin(dl)*cos(p2),cos(p1)*sin(p2)-sin(p1)*cos(p2)*cos(dl)))+360)%360
def compass(v):
    if v is None:return 'unknown'
    return ['N','NE','E','SE','S','SW','W','NW'][round(v/45)%8]
def _point_in_ring(lat,lon,ring):
    inside=False; n=len(ring)
    for i in range(n):
        x1,y1=ring[i]; x2,y2=ring[(i+1)%n]
        if ((y1>lat)!=(y2>lat)) and (lon<(x2-x1)*(lat-y1)/(y2-y1)+x1):
            inside=not inside
    return inside
def point_in_geometry(lat,lon,geometry):
    if not geometry:return False
    t=geometry.get('type'); coords=geometry.get('coordinates') or []
    if t=='Polygon':polys=[coords]
    elif t=='MultiPolygon':polys=coords
    else:return False
    for poly in polys:
        if not poly:continue
        if _point_in_ring(lat,lon,poly[0]) and not any(_point_in_ring(lat,lon,hole) for hole in poly[1:]):
            return True
    return False
