# SPDX-License-Identifier: GPL-3.0-or-later
"""Validated display metadata for round/rectangular families, not mesh recipes."""
from __future__ import annotations
import argparse
import copy
import json
import re
import sys
from .geometry import ModelError, keys, number
from .__main__ import load_recipe

SOURCE_STATUSES = {"SYNTHETIC_EXAMPLE", "USER_DEFINED_NOT_MEASURED",
                   "USER_ENTERED_MEASUREMENTS", "MANUAL_TRACE_UNVERIFIED"}
BODY_REQUIRED = {
    "round": {"top_diameter_mm", "height_mm"},
    "rectangular": {"top_length_mm", "top_width_mm", "height_mm"},
}
BODY_OPTIONAL = {
    "round": {"base_diameter_mm", "cavity_depth_mm"},
    "rectangular": {"cavity_depth_mm", "foot_length_mm", "foot_width_mm",
                    "bottom_panel_length_mm", "bottom_panel_width_mm"},
}
LID_REQUIRED = {
    "round": {"diameter_mm", "height_mm"},
    "rectangular": {"length_mm", "width_mm", "height_mm"},
}
LID_OPTIONAL = {"round": set(), "rectangular": {"platform_length_mm", "platform_width_mm"}}


def _text(value, name, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ModelError(f"{name}: expected nonempty text up to {limit} characters")


def _id(value, seen):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}", value):
        raise ModelError("catalog id: ASCII letter then up to 47 letters/digits/_/-")
    if value in seen:
        raise ModelError("duplicate catalog id")
    seen.add(value)


def _dimensions(value, required, optional):
    keys(value, required | optional, required, "dimensions_mm")
    for name, dim in value.items():
        number(dim, name, 0.05, 2000)
    if "cavity_depth_mm" in value and value["cavity_depth_mm"] >= value["height_mm"]:
        raise ModelError("cavity depth must be smaller than body height")


def validate_catalog(catalog):
    """Return an independent copy after structural and numeric validation.

    This checks assertions in the input, never physical fit or measurement accuracy.
    IDs are labels; no asset path, URL, recipe or script is resolved.
    """
    root_keys = {"catalog_schema_version", "units", "families"}
    keys(catalog, root_keys, root_keys, "catalog")
    if type(catalog["catalog_schema_version"]) is not int or catalog["catalog_schema_version"] != 1:
        raise ModelError("only catalog_schema_version 1 is supported")
    if catalog["units"] != "mm":
        raise ModelError("catalog units must be mm")
    families = catalog["families"]
    if not isinstance(families, list) or not 1 <= len(families) <= 32:
        raise ModelError("expected 1..32 families")
    seen = set()
    for family in families:
        required = {"id", "shape", "source_status", "source_note", "verification_scope",
                    "shared_lid", "models", "display_assumptions"}
        keys(family, required, required, "family")
        _id(family["id"], seen)
        shape = family["shape"]
        if not isinstance(shape, str) or shape not in BODY_REQUIRED:
            raise ModelError("shape must be round or rectangular")
        status = family["source_status"]
        if not isinstance(status, str) or status not in SOURCE_STATUSES:
            raise ModelError("unsupported source_status")
        _text(family["source_note"], "source_note")
        if family["verification_scope"] != "INPUT_DATA_ONLY_PHYSICAL_ACCURACY_NOT_VERIFIED":
            raise ModelError("catalog verification scope must disclose unverified physical accuracy")
        lid = family["shared_lid"]
        keys(lid, {"id", "dimensions_mm"}, {"id", "dimensions_mm"}, "shared_lid")
        _id(lid["id"], seen)
        _dimensions(lid["dimensions_mm"], LID_REQUIRED[shape], LID_OPTIONAL[shape])
        models = family["models"]
        if not isinstance(models, list) or not 1 <= len(models) <= 64:
            raise ModelError("expected 1..64 models per family")
        for model in models:
            model_keys = {"id", "shared_lid_id", "dimensions_mm"}
            keys(model, model_keys, model_keys, "model")
            _id(model["id"], seen)
            if model["shared_lid_id"] != lid["id"]:
                raise ModelError("model shared_lid_id must reference its family lid")
            _dimensions(model["dimensions_mm"], BODY_REQUIRED[shape], BODY_OPTIONAL[shape])
        assumptions = family["display_assumptions"]
        if not isinstance(assumptions, list) or len(assumptions) > 32:
            raise ModelError("expected 0..32 display assumptions")
        for assumption in assumptions:
            keys(assumption, {"id", "description", "value_mm"}, {"id", "description"}, "assumption")
            _id(assumption["id"], seen)
            _text(assumption["description"], "assumption description")
            if "value_mm" in assumption:
                number(assumption["value_mm"], "assumed value_mm", 0, 2000)
    return copy.deepcopy(catalog)


def load_catalog(path):
    """Read at most 256 KB; reject duplicate JSON keys and invalid metadata."""
    return validate_catalog(load_recipe(path))


def display_rows(catalog):
    """Flatten families to independent display records with explicit shared lids."""
    catalog = validate_catalog(catalog)
    return [{"family_id": family["id"], "shape": family["shape"], "units": "mm",
             "model_id": model["id"], "body_dimensions_mm": copy.deepcopy(model["dimensions_mm"]),
             "shared_lid": copy.deepcopy(family["shared_lid"]),
             "source_status": family["source_status"], "source_note": family["source_note"],
             "verification_scope": family["verification_scope"],
             "display_assumptions": copy.deepcopy(family["display_assumptions"])}
            for family in catalog["families"] for model in family["models"]]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate display metadata; does not generate 3D models.")
    parser.add_argument("catalog")
    args = parser.parse_args(argv)
    try:
        rows = display_rows(load_catalog(args.catalog))
        print(json.dumps({"status": "VALID_CATALOG", "rows": rows}, allow_nan=False))
        return 0
    except (ModelError, OSError, RecursionError) as error:
        print(json.dumps({"status": "ERROR", "message": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
