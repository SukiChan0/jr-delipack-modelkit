# SPDX-License-Identifier: GPL-3.0-or-later
"""OBJ and glTF 2.0 binary exports. glTF uses metres and Y-up."""
import json
import struct
from . import __version__

def glb_bytes(meshes):
    blob=bytearray(); views=[]; access=[]; gm=[]; nodes=[]; mats=[]
    def add(values, component, kind, target, bounds=False):
        while len(blob)%4: blob.append(0)
        start=len(blob)
        flat=[x for row in values for x in row] if kind!="SCALAR" else values
        code="f" if component==5126 else "I"
        blob.extend(struct.pack("<"+str(len(flat))+code,*flat))
        vi=len(views)
        views.append({"buffer":0,"byteOffset":start,"byteLength":len(blob)-start,"target":target})
        a={"bufferView":vi,"componentType":component,"count":len(values),"type":kind}
        if bounds:
            a["min"]=[min(v[k] for v in values) for k in range(3)]
            a["max"]=[max(v[k] for v in values) for k in range(3)]
        access.append(a)
        return len(access)-1
    for m in meshes:
        # (X,Y,Z) Z-up millimetres -> (X,Z,-Y) Y-up metres; determinant +1.
        pos=[[x/1000,z/1000,-y/1000] for x,y,z in m["vertices_mm"]]
        normals=[[x,z,-y] for x,y,z in m["normals"]]
        pi=add(pos,5126,"VEC3",34962,True)
        ni=add(normals,5126,"VEC3",34962)
        ii=add([i for face in m["faces"] for i in face],5125,"SCALAR",34963)
        mi=len(mats)
        mats.append({"name":m["id"]+"_material","pbrMetallicRoughness":{
            "baseColorFactor":m["color"]+[1.0],"metallicFactor":0.0,"roughnessFactor":0.35}})
        gm.append({"name":m["id"],"primitives":[{"attributes":{"POSITION":pi,"NORMAL":ni},
                   "indices":ii,"material":mi,"mode":4}]})
        x,y,z=m["position_mm"]
        nodes.append({"name":m["id"],"mesh":len(gm)-1,"translation":[x/1000,z/1000,-y/1000]})
    doc={"asset":{"version":"2.0","generator":"JR Delipack ModelKit " + __version__},
         "scene":0,"scenes":[{"nodes":list(range(len(nodes)))}],"nodes":nodes,"meshes":gm,
         "materials":mats,"buffers":[{"byteLength":len(blob)}],"bufferViews":views,"accessors":access,
         "extras":{"purpose":"visual_reference_only","fit_validation":"NOT_IMPLEMENTED"}}
    js=json.dumps(doc,ensure_ascii=True,separators=(",",":"),allow_nan=False).encode()
    js+=b" "*((-len(js))%4)
    blob+=b"\0"*((-len(blob))%4)
    size=12+8+len(js)+8+len(blob)
    return (struct.pack("<4sII",b"glTF",2,size)+struct.pack("<I4s",len(js),b"JSON")+js+
            struct.pack("<I4s",len(blob),b"BIN\0")+blob)

def obj_text(meshes):
    lines=["# JR Delipack ModelKit; coordinates in millimetres, Z-up.",
           "# Synthetic/reference geometry, not a manufacturing or fit certification."]
    offset=0
    for m in meshes:
        lines.append("o "+m["id"])
        for v in m["vertices_mm"]:
            p=[v[k]+m["position_mm"][k] for k in range(3)]
            lines.append("v "+" ".join(f"{x:.9g}" for x in p))
        for f in m["faces"]:
            lines.append("f "+" ".join(str(i+offset+1) for i in f))
        offset+=len(m["vertices_mm"])
    return "\n".join(lines)+"\n"
