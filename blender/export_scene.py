# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional: run in a NEW background Blender process; never in a user's GUI session.
blender --background --factory-startup --python blender/export_scene.py -- \
    --recipe examples/demo_set.json --out build/blender-demo
"""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from jr_modelkit.__main__ import load_recipe, build
from jr_modelkit.geometry import generate

def main():
    import bpy
    if not bpy.app.background:
        raise RuntimeError('Use a separate background Blender process, not the active GUI.')
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--recipe',required=True);p.add_argument('--out',required=True)
    a=p.parse_args(args)
    recipe,meshes=generate(load_recipe(a.recipe))
    out=Path(a.out).absolute()
    build(a.recipe,out) # validates and refuses ANY existing output directory
    scene=bpy.context.scene
    # Only remove objects from the new factory background scene, never save over an input.
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
    scene.unit_settings.length_unit='MILLIMETERS'
    group=bpy.data.collections.new('JR_GENERATED');scene.collection.children.link(group)
    for m,part in zip(meshes,recipe['parts']):
        data=bpy.data.meshes.new(m['id']+'_mesh')
        data.from_pydata([[x/1000,y/1000,z/1000] for x,y,z in m['vertices_mm']],[],m['faces'])
        data.update()
        obj=bpy.data.objects.new(m['id'],data);group.objects.link(obj)
        obj.location=[v/1000 for v in m['position_mm']]
        mat=bpy.data.materials.new(m['id']+'_material');mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value=(*m['color'],1)
            bsdf.inputs['Metallic'].default_value=0
            bsdf.inputs['Roughness'].default_value=.35
        obj.data.materials.append(mat)
        obj['source_status']=m['source_status'];obj['fit_validation']='NOT_IMPLEMENTED'
        # Preserve an editable source profile curve, not only a generated mesh.
        curve=bpy.data.curves.new(m['id']+'_profile','CURVE');curve.dimensions='3D'
        spline=curve.splines.new('POLY');spline.points.add(len(part['section_rz_mm'])-1)
        for point,(r,z) in zip(spline.points,part['section_rz_mm']):point.co=(r/1000,0,z/1000,1)
        spline.use_cyclic_u=True
        profile=bpy.data.objects.new(m['id']+'_source_profile',curve);group.objects.link(profile)
        profile.location=obj.location;profile.hide_render=True;profile.hide_viewport=True
    # The pure Python writer supplies the GLB; this adapter only adds a .blend scene.
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'),check_existing=True)
    print(json.dumps({'status':'BLEND_SAVED','file':str(out/'scene.blend'),
                      'blender_version':bpy.app.version_string,'rendered':False}))

if __name__=='__main__':main()
