# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from jr_modelkit.catalog import validate_catalog, load_catalog, display_rows, main
from jr_modelkit.geometry import ModelError, normalize

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/rt_series_dimensions.json"


def fixture():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def round_family():
    return {
        "id": "teaching_round", "shape": "round", "source_status": "SYNTHETIC_EXAMPLE",
        "source_note": "Invented test values, not a commercial round product.",
        "verification_scope": "INPUT_DATA_ONLY_PHYSICAL_ACCURACY_NOT_VERIFIED",
        "shared_lid": {"id": "demo_lid", "dimensions_mm": {"diameter_mm": 162, "height_mm": 12}},
        "models": [{"id": "demo_body", "shared_lid_id": "demo_lid",
                    "dimensions_mm": {"top_diameter_mm": 160, "height_mm": 48,
                                      "base_diameter_mm": 110, "cavity_depth_mm": 46}}],
        "display_assumptions": [],
    }


class CatalogTests(unittest.TestCase):
    def test_rt_transcription_and_shared_lid(self):
        rows = display_rows(load_catalog(CATALOG))
        self.assertEqual([r["model_id"] for r in rows], ["RT68", "RT78", "RT88"])
        self.assertEqual([r["body_dimensions_mm"]["height_mm"] for r in rows], [39, 45, 53])
        self.assertEqual([r["body_dimensions_mm"]["cavity_depth_mm"] for r in rows], [37, 43, 51])
        for row in rows:
            dims = row["body_dimensions_mm"]
            self.assertEqual((dims["top_length_mm"], dims["top_width_mm"]), (218, 149))
            self.assertEqual((dims["foot_length_mm"], dims["foot_width_mm"]), (175, 108))
            self.assertEqual((dims["bottom_panel_length_mm"], dims["bottom_panel_width_mm"]), (153, 85))
            self.assertEqual(row["shared_lid"], {"id": "RT_shared_lid", "dimensions_mm": {
                "length_mm": 220, "width_mm": 151, "height_mm": 20,
                "platform_length_mm": 190, "platform_width_mm": 118}})
            self.assertNotIn("floor_thickness_mm", dims)
            self.assertEqual(row["source_status"], "USER_ENTERED_MEASUREMENTS")
            self.assertEqual(row["display_assumptions"][0]["value_mm"], 1)

    def test_two_families_keep_independent_shapes_sources_and_lids(self):
        data = fixture()
        data["families"].append(round_family())
        rows = display_rows(data)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[-1]["shape"], "round")
        self.assertEqual(rows[-1]["source_status"], "SYNTHETIC_EXAMPLE")
        self.assertEqual(rows[-1]["shared_lid"]["dimensions_mm"]["diameter_mm"], 162)
        self.assertEqual(rows[-1]["body_dimensions_mm"]["top_diameter_mm"], 160)

    def test_reader_and_rows_do_not_alias_caller_or_each_other(self):
        original = fixture()
        baseline = copy.deepcopy(original)
        validated = validate_catalog(original)
        validated["families"][0]["models"][0]["dimensions_mm"]["height_mm"] = 10
        rows = display_rows(original)
        rows[0]["shared_lid"]["dimensions_mm"]["height_mm"] = 999
        rows[0]["display_assumptions"][0]["value_mm"] = 999
        self.assertEqual(original, baseline)
        self.assertEqual(rows[1]["shared_lid"]["dimensions_mm"]["height_mm"], 20)
        self.assertEqual(rows[1]["display_assumptions"][0]["value_mm"], 1)

    def test_invalid_dimensions_are_rejected(self):
        for value in [True, None, "39", [], float("nan"), float("inf"), -1, 0, 2001, 10**399]:
            with self.subTest(value_type=type(value).__name__):
                data = fixture()
                data["families"][0]["models"][0]["dimensions_mm"]["height_mm"] = value
                with self.assertRaises(ModelError): validate_catalog(data)

    def test_missing_or_wrong_family_dimension_is_rejected(self):
        for mutation in ["missing", "wrong_shape"]:
            data = fixture()
            dims = data["families"][0]["models"][0]["dimensions_mm"]
            if mutation == "missing": del dims["top_length_mm"]
            else: dims["top_diameter_mm"] = 218
            with self.assertRaises(ModelError): validate_catalog(data)

    def test_cavity_cannot_equal_body_height(self):
        data = fixture()
        data["families"][0]["models"][0]["dimensions_mm"]["cavity_depth_mm"] = 39
        with self.assertRaises(ModelError): validate_catalog(data)

    def test_unknown_lid_and_duplicate_ids_rejected(self):
        for key, value in [("shared_lid_id", "another_family_lid"), ("id", "RT78"), ("id", "../secret")]:
            data = fixture()
            data["families"][0]["models"][0][key] = value
            with self.assertRaises(ModelError): validate_catalog(data)

    def test_scope_and_shape_cannot_be_misrepresented(self):
        for key, value in [("source_status", []), ("shape", {}), ("shape", "box"),
                           ("verification_scope", "PHYSICALLY_CERTIFIED")]:
            data = fixture()
            data["families"][0][key] = value
            with self.assertRaises(ModelError): validate_catalog(data)

    def test_structure_and_budgets(self):
        for root_value in [[], {}, None]:
            with self.assertRaises(ModelError): validate_catalog(root_value)
        for key, value in [("catalog_schema_version", True), ("units", "metres"),
                           ("families", []), ("families", [round_family()] * 33)]:
            data = fixture()
            data[key] = value
            with self.assertRaises(ModelError): validate_catalog(data)
        for key, value in [("models", []), ("models", [{}] * 65), ("display_assumptions", [{}] * 33),
                           ("source_note", "x" * 1001)]:
            data = fixture()
            data["families"][0][key] = value
            with self.assertRaises(ModelError): validate_catalog(data)

    def test_catalog_is_not_silently_accepted_as_geometry_recipe(self):
        with self.assertRaises(ModelError): normalize(fixture())

    def test_duplicate_keys_oversized_and_malformed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for text in ['{"units":"mm","units":"cm"}', ' ' * 256001, '{']:
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ModelError): load_catalog(path)

    def test_cli_reports_data_and_controlled_errors(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout): code = main([str(CATALOG)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "VALID_CATALOG")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{}', encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr): code = main([str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(stderr.getvalue())["status"], "ERROR")
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__": unittest.main()
