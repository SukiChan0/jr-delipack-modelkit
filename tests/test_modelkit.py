# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import contextlib
import io
import json
import math
from pathlib import Path
import random
import struct
import tempfile
import unittest
from jr_modelkit.geometry import ModelError, normalize, validate_section, tapered_section, generate
from jr_modelkit import __version__
from jr_modelkit.exporters import glb_bytes, obj_text
from jr_modelkit.__main__ import load_recipe, build, main
from tools.audit_github_html import audit

ROOT=Path(__file__).resolve().parents[1]
def example():return json.loads((ROOT/'examples/demo_set.json').read_text())

class GeometryTests(unittest.TestCase):
 def test_demo_two_parts(self):
  r,m=generate(example());self.assertEqual(len(m),2)
 def test_requested_dimensions(self):
  _,m=generate(example());b=m[0]['bounds_mm'];self.assertAlmostEqual(b[1][0]-b[0][0],160);self.assertEqual(b[1][2]-b[0][2],48)
 def test_closed_positive_material(self):
  for m in generate(example())[1]:self.assertTrue(m['closed_material_surface']);self.assertGreater(m['material_volume_mm3'],0)
 def test_normals_unit_length(self):
  for m in generate(example())[1]:
   for n in m['normals']:self.assertAlmostEqual(math.sqrt(sum(x*x for x in n)),1,places=7)
 def test_reverse_profile_equivalent(self):
  a=example();_,ma=generate(a);a['parts'][1]['section_rz_mm'].reverse();_,mb=generate(a);self.assertAlmostEqual(ma[1]['material_volume_mm3'],mb[1]['material_volume_mm3'])
 def test_repeated_closing_point_accepted(self):
  s=[[0,0],[10,0],[10,2],[0,2],[0,0]];self.assertEqual(len(validate_section(s)),4)
 def test_self_intersection(self):
  with self.assertRaises(ModelError):validate_section([[1,0],[5,5],[1,5],[5,0]])
 def test_self_touch(self):
  with self.assertRaises(ModelError):validate_section([[1,0],[5,0],[3,2],[5,4],[1,4],[3,2]])
 def test_collinear_reversal(self):
  with self.assertRaises(ModelError):validate_section([[0,0],[5,0],[3,0],[5,4],[0,4]])
 def test_axis_pinching_rejected(self):
  with self.assertRaises(ModelError):validate_section([[0,0],[10,0],[10,5],[0,5],[3,3]])
 def test_nan_rejected(self):
  with self.assertRaises(ModelError):validate_section([[0,0],[float('nan'),0],[0,3]])
 def test_negative_radius(self):
  with self.assertRaises(ModelError):validate_section([[0,0],[-3,0],[0,3]])
 def test_boolean_number_rejected(self):
  a=example();a['parts'][0]['tapered_bowl']['height_mm']=True
  with self.assertRaises(ModelError):generate(a)
 def test_huge_integer_rejected(self):
  a=example();a['parts'][0]['tapered_bowl']['height_mm']=10**399
  with self.assertRaises(ModelError):generate(a)
 def test_source_status_requires_string(self):
  for value in [[],{},1,None,True]:
   with self.subTest(value=value):
    a=example();a['parts'][0]['source_status']=value
    with self.assertRaises(ModelError):generate(a)
 def test_unknown_fields(self):
  a=example();a['shell_command']='dangerous'
  with self.assertRaises(ModelError):generate(a)
 def test_duplicate_ids(self):
  a=example();a['parts'][1]['id']=a['parts'][0]['id']
  with self.assertRaises(ModelError):generate(a)
 def test_path_name_rejected(self):
  a=example();a['parts'][0]['id']='../../output'
  with self.assertRaises(ModelError):generate(a)
 def test_wrong_units(self):
  a=example();a['units']='cm'
  with self.assertRaises(ModelError):generate(a)
 def test_segment_budget(self):
  for n in [True,8,95,260,1000000]:
   a=example();a['segments']=n
   with self.assertRaises(ModelError):generate(a)
 def test_normal_not_horizontal_thickness(self):
  p=example()['parts'][0]['tapered_bowl'];s=tapered_section(p);r0,z0=s[2];r1,z1=s[3];k=((p['top_diameter_mm']-p['base_diameter_mm'])/2)/p['height_mm'];self.assertAlmostEqual((r0-r1)/math.sqrt(1+k*k),p['wall_thickness_mm'])
 def test_wall_removes_cavity(self):
  p=example()['parts'][0]['tapered_bowl'];p['wall_thickness_mm']=99
  with self.assertRaises(ModelError):tapered_section(p)
 def test_floor_too_thick(self):
  p=example()['parts'][0]['tapered_bowl'];p['floor_thickness_mm']=48
  with self.assertRaises(ModelError):tapered_section(p)
 def test_tapered_property_cases(self):
  rng=random.Random(618)
  for _ in range(12):
   a=example();a['parts']=a['parts'][:1];p=a['parts'][0]['tapered_bowl'];p.update(base_diameter_mm=rng.uniform(40,150),height_mm=rng.uniform(20,80));p['top_diameter_mm']=p['base_diameter_mm']+rng.uniform(5,60);_,m=generate(a);self.assertTrue(m[0]['closed_material_surface'])
 def test_open_bowl_cavity_not_capped(self):
  m=generate(example())[1][0]
  # At top height only the material rim is present, never a central disk.
  for face in m['faces']:
   v=[m['vertices_mm'][i] for i in face]
   if all(abs(p[2]-48)<1e-7 for p in v):self.assertTrue(all(math.hypot(p[0],p[1])>75 for p in v))

class ExportTests(unittest.TestCase):
 def test_glb_header_lengths(self):
  data=glb_bytes(generate(example())[1]);magic,version,size=struct.unpack_from('<4sII',data);self.assertEqual((magic,version,size),(b'glTF',2,len(data)));jlen,jtype=struct.unpack_from('<I4s',data,12);self.assertEqual(jtype,b'JSON');self.assertEqual(jlen%4,0)
 def test_glb_units_and_nodes(self):
  data=glb_bytes(generate(example())[1]);n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);self.assertEqual(len(doc['nodes']),2);self.assertAlmostEqual(doc['accessors'][0]['max'][1],.048);self.assertAlmostEqual(doc['nodes'][1]['translation'][1],.058)
 def test_export_display_name(self):
  meshes=generate(example())[1];data=glb_bytes(meshes);n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n])
  self.assertEqual(doc['asset']['generator'],'JR Delipack ModelKit '+__version__)
  self.assertTrue(obj_text(meshes).startswith('# JR Delipack ModelKit;'))
 def test_glb_deterministic(self):
  m=generate(example())[1];self.assertEqual(glb_bytes(m),glb_bytes(m))
 def test_obj_parts(self):
  text=obj_text(generate(example())[1]);self.assertIn('o demo_bowl',text);self.assertIn('o demo_lid',text)
 def test_build_outputs_and_refuse_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'result';build(ROOT/'examples/demo_set.json',out);self.assertEqual(len(list(out.iterdir())),5)
   before=(out/'model.glb').read_bytes()
   with self.assertRaises(ModelError):build(ROOT/'examples/demo_set.json',out)
   self.assertEqual((out/'model.glb').read_bytes(),before)
 def test_invalid_recipe_no_output(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.json';p.write_text('{}');out=Path(d)/'result'
   with self.assertRaises(ModelError):build(p,out)
   self.assertFalse(out.exists())
 def test_duplicate_json_keys(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.json';p.write_text('{"units":"mm","units":"cm"}')
   with self.assertRaises(ModelError):load_recipe(p)
 def test_input_byte_budget(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'big.json';p.write_text(' '*256001)
   with self.assertRaises(ModelError):load_recipe(p)
 def test_cli_malformed_values_are_controlled_errors(self):
  with tempfile.TemporaryDirectory() as d:
   for index,value in enumerate([10**399,[],{}]):
    with self.subTest(value_type=type(value).__name__):
     a=example()
     if index==0:a['parts'][0]['tapered_bowl']['height_mm']=value
     else:a['parts'][0]['source_status']=value
     p=Path(d)/f'bad-{index}.json';p.write_text(json.dumps(a));out=Path(d)/f'out-{index}'
     stderr=io.StringIO()
     with contextlib.redirect_stderr(stderr):code=main(['build',str(p),'--out',str(out)])
     self.assertEqual(code,2);self.assertEqual(json.loads(stderr.getvalue())['status'],'ERROR')
     self.assertFalse(out.exists());self.assertNotIn('Traceback',stderr.getvalue())

class SeoAuditTests(unittest.TestCase):
 def test_meta_noindex(self):
  r=audit('<meta name="robots" content="noindex, follow">',{},'jrdelipack.com');self.assertTrue(r['noindex_seen']);self.assertEqual(r['account_restriction_status'],'UNKNOWN')
 def test_header_noindex(self):
  self.assertTrue(audit('',{'X-Robots-Tag':'noindex'},'jrdelipack.com')['noindex_seen'])
 def test_link_attributes(self):
  r=audit('<a href="https://jrdelipack.com/?x=1" rel="nofollow ugc">site</a>',{},'jrdelipack.com');self.assertEqual(len(r['website_links']),1);self.assertTrue(r['website_links'][0]['nofollow'])
 def test_noindex_absent_not_index_guarantee(self):
  r=audit('<h1>Project</h1>',None,'jrdelipack.com');self.assertFalse(r['noindex_seen']);self.assertEqual(r['google_index_status'],'UNKNOWN');self.assertEqual(r['x_robots_tag'],'HEADERS_NOT_PROVIDED')

if __name__=='__main__':unittest.main()
