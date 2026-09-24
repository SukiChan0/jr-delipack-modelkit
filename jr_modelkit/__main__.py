# SPDX-License-Identifier: GPL-3.0-or-later
"""python -m jr_modelkit build recipe.json --out NEW_DIRECTORY"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from . import __version__
from .geometry import ModelError, generate
from .exporters import glb_bytes, obj_text

MAX_INPUT_BYTES=256_000

def load_recipe(path):
    with open(path,"rb") as f: raw=f.read(MAX_INPUT_BYTES+1)
    if len(raw)>MAX_INPUT_BYTES: raise ModelError("recipe is larger than 256 KB")
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ModelError("duplicate JSON key: "+k)
            out[k]=v
        return out
    try:
        return json.loads(raw,object_pairs_hook=pairs)
    except (ValueError, UnicodeError, RecursionError) as e:
        raise ModelError(f"invalid JSON recipe: {e}") from e

def build(path, output):
    recipe,meshes=generate(load_recipe(path))
    output=Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ModelError("output already exists; choose a NEW directory (no overwrite)")
    output.parent.mkdir(parents=True,exist_ok=True)
    canonical=json.dumps(recipe,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    summary={"version":__version__,"recipe_sha256":hashlib.sha256(canonical).hexdigest(),
             "input_units":"mm","obj_units":"mm","glb_units":"metres",
             "photo_reconstruction":"NOT_IMPLEMENTED", "fit_validation":"NOT_IMPLEMENTED",
             "manufacturing_validation":"NOT_IMPLEMENTED", "parts":[]}
    for m in meshes:
        summary["parts"].append({k:m[k] for k in ["id","source_status","bounds_mm",
                                    "position_mm","closed_material_surface","material_volume_mm3"]}
                               | {"vertices":len(m["vertices_mm"]),"triangles":len(m["faces"]),
                                  "note":"material volume is NOT usable container capacity"})
    stage=Path(tempfile.mkdtemp(prefix=".jr-stage-",dir=output.parent))
    try:
        (stage/"model.glb").write_bytes(glb_bytes(meshes))
        (stage/"model.obj").write_text(obj_text(meshes),encoding="utf-8")
        for name,data in [("recipe.resolved.json",recipe),("report.json",summary),
                          ("mesh.json",{"schema_version":1,"units":"mm","parts":meshes})]:
            (stage/name).write_text(json.dumps(data,indent=2,allow_nan=False),encoding="utf-8")
        # Reserve the destination with mkdir(exist_ok=False). Never overwrite user files.
        output.mkdir(exist_ok=False)
        try:
            for source in stage.iterdir(): os.replace(source,output/source.name)
        except Exception:
            # Keep partial output for diagnostics; never delete an existing user's path.
            raise
    finally:
        shutil.rmtree(stage,ignore_errors=True)
    return summary

def main(argv=None):
    p=argparse.ArgumentParser(description="Local rotational packaging prototype; not photo AI.")
    p.add_argument("--version",action="version",version=__version__)
    sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("build"); b.add_argument("recipe"); b.add_argument("--out",required=True)
    v=sub.add_parser("validate"); v.add_argument("recipe")
    args=p.parse_args(argv)
    try:
        if args.command=="build":
            result=build(args.recipe,args.out)
            print(json.dumps({"status":"BUILT","output":str(Path(args.out).absolute()),
                              "parts":len(result["parts"]),"recipe_sha256":result["recipe_sha256"]}))
        else:
            _,meshes=generate(load_recipe(args.recipe))
            print(json.dumps({"status":"VALID_RECIPE_AND_MESH","parts":len(meshes),
                              "real_world_accuracy":"NOT_VERIFIED"}))
        return 0
    except (ModelError,OSError,RecursionError) as e:
        print(json.dumps({"status":"ERROR","message":str(e)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=="__main__": raise SystemExit(main())
