# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional developer check; requires separately installed trimesh. Not runtime dependency."""
import json
from pathlib import Path

def main():
    import trimesh
    root=Path(__file__).resolve().parents[1]
    records=[]
    for folder in ['generated','custom_generated']:
        path=root/'examples'/folder/'model.glb'
        scene=trimesh.load(path,force='scene')
        for name,mesh in scene.geometry.items():
            record={'fixture':folder,'part':name,'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
                    'closed_material_surface':bool(mesh.is_watertight),
                    'winding_consistent':bool(mesh.is_winding_consistent),
                    'material_volume_m3':float(mesh.volume),'extents_local_metres':mesh.extents.tolist()}
            assert record['closed_material_surface'] and record['winding_consistent'] and record['material_volume_m3']>0
            records.append(record)
        obj=trimesh.load(root/'examples'/folder/'model.obj',force='scene')
        assert len(obj.geometry)>0
    report={'checker':'trimesh '+trimesh.__version__,'status':'PASS',
            'scope':'Two synthetic fixtures; GLB and OBJ parse; individual GLB material topology and local metric extents',
            'official_gltf_validator':'NOT_RUN','physical_accuracy':'NOT_TESTED','records':records}
    (root/'evidence/independent-mesh-check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
