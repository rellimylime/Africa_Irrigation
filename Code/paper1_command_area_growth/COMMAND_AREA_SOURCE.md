# Command-Area Source Assessment

This note documents which command-area export is used by the Paper 1 workflow
and how it should be described.

## Recommended Source

Use the config key:

`No_Crop_Vectorized_Command_Area_shp_path`

It currently points to:

`Data/Raw/Physical_Envelope_Command_Areas_AnyUse_Hgt15-shp`

This is the current main paper source. It represents modeled physical envelopes
around documented large dams, with irrigation included as any listed GDW use
(`Main`, `Major`, or `Sec`), dam height greater than 15 m, capacity-derived
service radius logic, and a 50 km cap.

## What The Layer Is

The layer is a modeled physical proxy for large-dam command-area influence. It
is not an observed irrigation-district or service-boundary dataset.

The final paper language should therefore use:

> modeled large-dam command-area envelopes

## Why This Source

The source is preferred because it:

- keeps one valid physical-envelope feature per modeled GDW dam;
- uses irrigation as any listed GDW use rather than only `MAIN_USE`;
- filters to large dams using height greater than 15 m;
- avoids defining the final command-area geometry from a late-period cropland
  mask;
- preserves diagnostics such as reservoir elevation, capacity model, maximum
  distance, yield, dam year, and `validCA`.

## Source Comparison

| Source | Interpretation |
| --- | --- |
| `Physical_Envelope_Command_Areas_AnyUse_Hgt15` | Main source. Current modeled large-dam physical-envelope layer. |
| `No_Crop_Vectorized_Command_Area` | Older main-use-only baseline. Useful as a sanity check, not final any-use source. |
| `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15` | Superseded failed/suspicious export with very small footprint. Do not use for final results. |
| `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15_ModelUnits` | Strict pure-no-crop sensitivity; footprint collapses and is not the main source. |
| `No_Crop_Initial_CA` | Broad initial candidate mask. Sensitivity/upper-bound context only. |
| `No_Crop_All_Height_Initial_CA` | Even broader initial candidate mask. Sensitivity/upper-bound context only. |

## Dam-Use Definition

For Paper 1, dams should be included when irrigation is any listed GDW use. In
the local GDW attributes this is represented by `USE_IRRI` when available. The
Python input-preparation step uses `USE_IRRI` when present and falls back to
`MAIN_USE` only when no irrigation-use field exists.

The GEE export logic is saved at:

`Code/paper1_command_area_growth/gee_export_no_crop_anyuse_command_areas.js`

That script should remain the reference for regenerating the command-area layer
or auditing it in Earth Engine.

## QA Implication

Local DEM QA flags many envelopes as including terrain above reservoir elevation
+10 m. That does not invalidate the inside/outside extraction mechanically, but
it limits interpretation. The next methodological audit should be GEE-side:
rerun the elevation checks with the exact DEM, projection, and thresholds used
to create the export. If GEE passes and local DEM fails, the issue is likely DEM
source, resampling, or projection mismatch. If GEE also flags the envelopes, the
export logic needs tightening.
