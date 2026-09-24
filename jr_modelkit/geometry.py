# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic millimetre-space geometry. No image inference, network or eval."""
from __future__ import annotations
import math
import re
from collections import Counter
from typing import Any

EPS = 1e-8
MAX_PARTS = 8
MAX_POINTS = 256
MAX_SEGMENTS = 256

class ModelError(ValueError):
    """Invalid, ambiguous or over-budget recipe."""

def number(v: Any, name: str, lo: float, hi: float) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ModelError(f"{name}: expected a finite number")
    try:
        v = float(v)
    except OverflowError as e:
        raise ModelError(f"{name}: expected a finite number") from e
    if not math.isfinite(v) or not lo <= v <= hi:
        raise ModelError(f"{name}: expected {lo} <= value <= {hi}")
    return v

def keys(obj: Any, allowed: set[str], required: set[str], name: str) -> None:
    if not isinstance(obj, dict):
        raise ModelError(f"{name}: expected an object")
    missing, unknown = required - obj.keys(), obj.keys() - allowed
    if missing or unknown:
        raise ModelError(f"{name}: missing={sorted(missing)}, unknown={sorted(unknown)}")

def cross2(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

def intersects(a, b, c, d):
    def on(p, q, r):
        return (abs(cross2(p,q,r)) <= EPS and
                min(p[0],q[0])-EPS <= r[0] <= max(p[0],q[0])+EPS and
                min(p[1],q[1])-EPS <= r[1] <= max(p[1],q[1])+EPS)
    o1,o2,o3,o4 = cross2(a,b,c),cross2(a,b,d),cross2(c,d,a),cross2(c,d,b)
    if ((o1>EPS and o2<-EPS) or (o1<-EPS and o2>EPS)) and \
       ((o3>EPS and o4<-EPS) or (o3<-EPS and o4>EPS)):
        return True
    return on(a,b,c) or on(a,b,d) or on(c,d,a) or on(c,d,b)

def validate_section(raw: Any) -> list[tuple[float, float]]:
    if not isinstance(raw, list) or not 3 <= len(raw) <= MAX_POINTS:
        raise ModelError(f"section_rz_mm: expected 3..{MAX_POINTS} points")
    pts=[]
    for i,p in enumerate(raw):
        if not isinstance(p,(list,tuple)) or len(p)!=2:
            raise ModelError(f"section point {i}: expected [radius_mm, height_mm]")
        r=number(p[0],f"radius[{i}]",0,1000)
        z=number(p[1],f"height[{i}]",0,1000)
        pts.append((0.0 if r<EPS else r,z))
    # Permit one repeated closing point; no other duplicates or zero edges.
    if math.dist(pts[0],pts[-1])<EPS:
        pts.pop()
    n=len(pts)
    if n<3:
        raise ModelError("section needs three distinct vertices")
    for i in range(n):
        for j in range(i+1,n):
            if math.dist(pts[i],pts[j])<EPS:
                raise ModelError("section contains duplicate vertices")
    for i in range(n):
        a,b=pts[i],pts[(i+1)%n]
        for j in range(i+1,n):
            if j==(i+1)%n or i==(j+1)%n:
                continue
            if intersects(a,b,pts[j],pts[(j+1)%n]):
                raise ModelError("section self-intersects or self-touches")
    # Collinear reversal creates overlapping adjacent edges and invalid material.
    for i in range(n):
        a,b,c=pts[i-1],pts[i],pts[(i+1)%n]
        if abs(cross2(a,b,c))<=EPS and \
           (a[0]-b[0])*(c[0]-b[0])+(a[1]-b[1])*(c[1]-b[1])>EPS:
            raise ModelError("section contains a collinear reversal")
    area=sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1]
             for i in range(n))/2
    if abs(area)<1e-6:
        raise ModelError("section has zero material area")
    axis=[i for i,p in enumerate(pts) if p[0]==0]
    if axis and (len(axis)!=2 or ((axis[1]-axis[0]) not in (1,n-1))):
        raise ModelError("axis contact must be one edge with two distinct endpoints")
    return pts if area>0 else list(reversed(pts))

def tapered_section(p: Any):
    req={"top_diameter_mm","base_diameter_mm","height_mm",
         "wall_thickness_mm","floor_thickness_mm"}
    keys(p,req,req,"tapered_bowl")
    rt=number(p["top_diameter_mm"],"top diameter",4,2000)/2
    rb=number(p["base_diameter_mm"],"base diameter",4,2000)/2
    h=number(p["height_mm"],"height",2,1000)
    t=number(p["wall_thickness_mm"],"normal wall thickness",0.05,100)
    b=number(p["floor_thickness_mm"],"floor thickness",0.05,100)
    if rt<rb or b>=h:
        raise ModelError("preset requires top >= base diameter and floor < height")
    slope=(rt-rb)/h
    # Parallel straight wall offset: horizontal separation is NOT equal to
    # normal thickness on a tapered wall.
    delta=t*math.sqrt(1+slope*slope)
    ri_bottom=rb+slope*b-delta
    if min(rt-delta,ri_bottom)<=0.1:
        raise ModelError("wall thickness removes the internal cavity")
    return validate_section([[0,0],[rb,0],[rt,h],[rt-delta,h],[ri_bottom,b],[0,b]])

def normalize(recipe: Any):
    keys(recipe,{"schema_version","units","segments","parts","notes"},
         {"schema_version","units","parts"},"recipe")
    if type(recipe["schema_version"]) is not int or recipe["schema_version"]!=1:
        raise ModelError("only schema_version 1 is supported")
    if recipe["units"]!="mm":
        raise ModelError("input units must be mm; radii are not diameters")
    seg=recipe.get("segments",96)
    if type(seg) is not int or not 24<=seg<=MAX_SEGMENTS or seg%4:
        raise ModelError("segments must be a multiple of 4 in [24,256]")
    parts=recipe["parts"]
    if not isinstance(parts,list) or not 1<=len(parts)<=MAX_PARTS:
        raise ModelError("expected 1..8 parts")
    notes=recipe.get("notes","")
    if not isinstance(notes,str) or len(notes)>4000:
        raise ModelError("notes must be text of at most 4000 characters")
    out=[]; ids=set()
    for p in parts:
        keys(p,{"id","section_rz_mm","tapered_bowl","position_mm","color",
                "source_status"},{"id"},"part")
        pid=p["id"]
        if not isinstance(pid,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}",pid):
            raise ModelError("part id: ASCII letter then up to 47 letters/digits/_/-")
        if pid in ids:
            raise ModelError("duplicate part id")
        ids.add(pid)
        if ("section_rz_mm" in p)==("tapered_bowl" in p):
            raise ModelError("choose exactly one of section_rz_mm or tapered_bowl")
        section=(validate_section(p["section_rz_mm"]) if "section_rz_mm" in p
                 else tapered_section(p["tapered_bowl"]))
        pos=p.get("position_mm",[0,0,0])
        col=p.get("color",[0.16,0.19,0.21])
        if not isinstance(pos,list) or len(pos)!=3 or not isinstance(col,list) or len(col)!=3:
            raise ModelError("position_mm and color require three numbers")
        pos=[number(v,"position",-10000,10000) for v in pos]
        col=[number(v,"color",0,1) for v in col]
        status=p.get("source_status","USER_DEFINED_NOT_MEASURED")
        if not isinstance(status,str) or status not in {"SYNTHETIC_EXAMPLE","USER_DEFINED_NOT_MEASURED",
                          "USER_ENTERED_MEASUREMENTS","MANUAL_TRACE_UNVERIFIED"}:
            raise ModelError("unsupported source_status")
        out.append({"id":pid,"section_rz_mm":section,"position_mm":pos,
                    "color":col,"source_status":status})
    return {"schema_version":1,"units":"mm","segments":seg,"parts":out,"notes":notes}

def vector_cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def build_mesh(part, segments):
    pts=part["section_rz_mm"]
    vertices=[]; rings=[]; faces=[]
    for r,z in pts:
        if r==0:
            rings.append([len(vertices)])
            vertices.append([0.0,0.0,z])
        else:
            ring=[]
            for j in range(segments):
                theta=2*math.pi*j/segments
                ring.append(len(vertices))
                vertices.append([r*math.cos(theta),r*math.sin(theta),z])
            rings.append(ring)
    for i,a in enumerate(rings):
        b=rings[(i+1)%len(rings)]
        if len(a)==len(b)==1:
            continue
        for j in range(segments):
            k=(j+1)%segments
            if len(a)==1:
                faces.append([a[0],b[k],b[j]])
            elif len(b)==1:
                faces.append([a[j],a[k],b[0]])
            else:
                faces.extend([[a[j],a[k],b[j]],[a[k],b[k],b[j]]])
    normals=[[0.,0.,0.] for _ in vertices]
    volume=0.; undirected=Counter(); directed=Counter()
    for a,b,c in faces:
        va,vb,vc=vertices[a],vertices[b],vertices[c]
        n=vector_cross([vb[k]-va[k] for k in range(3)],
                       [vc[k]-va[k] for k in range(3)])
        if math.sqrt(sum(x*x for x in n))<1e-9:
            raise ModelError("degenerate generated triangle")
        for idx in (a,b,c):
            for k in range(3): normals[idx][k]+=n[k]
        volume+=sum(va[k]*vector_cross(vb,vc)[k] for k in range(3))/6
        for u,v in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((u,v)))
            undirected[key]+=1
            directed[key]+=1 if u<v else -1
    if any(v!=2 for v in undirected.values()) or any(directed.values()) or volume<=EPS:
        raise ModelError("generated material surface is not consistently closed/outward")
    for n in normals:
        length=math.sqrt(sum(x*x for x in n))
        if length<=EPS: raise ModelError("invalid normal")
        for k in range(3): n[k]/=length
    bounds=[[min(v[k] for v in vertices) for k in range(3)],
            [max(v[k] for v in vertices) for k in range(3)]]
    return {"id":part["id"],"vertices_mm":vertices,"faces":faces,"normals":normals,
            "position_mm":part["position_mm"],"color":part["color"],
            "source_status":part["source_status"],"bounds_mm":bounds,
            "material_volume_mm3":volume,"closed_material_surface":True}

def generate(recipe):
    recipe=normalize(recipe)
    meshes=[build_mesh(p,recipe["segments"]) for p in recipe["parts"]]
    return recipe, meshes
