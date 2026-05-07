# Command-Area Source Assessment

This note documents how the available command-area exports should be interpreted
in the Paper 1 workflow.

## Recommendation

Use `No_Crop_Vectorized_Command_Area_shp_path` as the main command-area source,
pointing to `Physical_Envelope_Command_Areas_AnyUse_Hgt15`.

This is the most defensible source for the paper estimand because it is the
final/vectorized physical-envelope command-area product: one cleaned feature per
valid GDW dam, capacity/yield constrained, bounded by basin/elevation context
and reservoir distance, and carrying QA attributes such as `validCA`, `MaxDist`,
`MaxRadCap`, `TheoryArea`, `Yield`, and `ResCapBath`.

The Initial command-area layers should be treated as sensitivity inputs, not the
headline paper source.

## How the GEE Logic Works

The Earth Engine command-area script creates two products per dam:

- `initialCA`: the broad physical candidate envelope.
  It is defined as pixels in a selected HydroBASINS unit that are below the
  reservoir elevation plus `dz`, clipped to the country/reservoir context, with
  the reservoir itself removed. This is a topographic/basin feasibility mask,
  not a capacity-limited command area.
- `vectorized`: the final command-area approximation.
  It estimates theoretical irrigable area from reservoir capacity and a country
  yield term, computes the fraction of eligible area that could be served, then
  keeps the nearest eligible pixels to the reservoir up to that fraction.

In the pasted script, the final vectorized layer uses a 2019 land-cover cropland
mask (`crp = lc.eq(40)`). That would be problematic as the main infrastructure
mask for 1980-2015 expansion because it conditions the command area on land
cover observed near the end of the outcome period.

The local export used for final runs should be named
`No_CropOutput_CropCalibrated_Command_Areas_AnyUse_Hgt15_ModelUnits`, and its
`type` field should include `vectorized_nocropmask`. That indicates it is the
modified no-crop-output version of the final vectorized product, which is the
preferred main source. The yearly command-area builder checks this field for
final/vectorized sources and stops unless no-crop provenance is confirmed.

The distinction matters. A strict run that removes the 2019 crop layer from both
the distance calibration and the final geometry produced only 27 command areas
and about 0.0065 Mha, because the greatly expanded candidate envelope drove the
distance percentile very close to each reservoir. The primary paper source
therefore preserves the original model's crop-calibrated distance threshold but
exports the final geometry without cropping it to the 2019 land-cover layer.

## Dam-Use Definition

For the paper, dams should be included when irrigation is any listed GDW use, not
only when irrigation is the `MAIN_USE`. In the local GDW attributes this is best
represented by a non-empty `USE_IRRI` value, which can be `Main`, `Major`, or
`Sec`. The Paper 1 input-preparation script now uses `USE_IRRI` when that field
is present and falls back to `MAIN_USE` only when no irrigation-use field exists.

The current local no-crop command-area export was generated from the older GEE
selection shown in the pasted script:

```js
var dams = dams0.filter(ee.Filter.eq('MAIN_USE', 'Irrigation'))
                .filter(ee.Filter.gt('DAM_HGT_M', 15));
```

To align the command-area export with the paper definition, regenerate the GEE
export with the irrigation-use field:

```js
var dams = dams0.filter(ee.Filter.inList('USE_IRRI', ['Main', 'Major', 'Sec']))
                .filter(ee.Filter.gt('DAM_HGT_M', 15));
```

The full updated script is saved at
`Code/paper1_command_area_growth/gee_export_no_crop_anyuse_command_areas.js`.
It normalizes numeric-looking DBF fields before filtering, removes the 2019 crop
mask from the final exported geometry, preserves the original model's
capacity/yield scaling and crop-calibrated distance threshold, and exports a dam
audit CSV and command-area diagnostics CSV alongside the final and initial
command-area shapefiles.

This matters because local GDW inspection found four arid-SSA dams taller than
15 m with `USE_IRRI` listed but `MAIN_USE` not equal to irrigation. Those dams
have matched GDW reservoirs but are not present in the current command-area
export, so the Python-side dam filter alone cannot add their command areas.

## Local Export Comparison

| Source | Records | Unique GDW IDs | Summed raw area | Interpretation |
| --- | ---: | ---: | ---: | --- |
| `Physical_Envelope_Command_Areas_AnyUse_Hgt15` | 174 | 174 | ~1.00 Mha | Main source. Physical-envelope final export with irrigation as any listed GDW use, height >15 m, no 2019 cropland conditioning, and a 50 km radius cap. |
| `No_CropOutput_CropCalibrated_Command_Areas_AnyUse_Hgt15_ModelUnits` | 23 local export | 23 | ~0.004 Mha | Superseded crop-calibrated lineage; retained only as a diagnostic/sensitivity artifact. |
| `No_Crop_Vectorized_Command_Area` | 171 | 171 | ~5.99 Mha | Older main-use-only baseline. Useful as a sanity check, not final any-use paper source. |
| `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15` | 24 | 24 | ~0.006 Mha | Superseded failed/suspicious export. Do not use for final results. |
| `No_Crop_Vectorized_Command_Areas_AnyUse_Hgt15_ModelUnits` | 27 | 27 | ~0.0065 Mha | Strict pure-no-crop sensitivity. Not the main source because the distance threshold collapses. |
| `No_Crop_Initial_CA` | 5,566 | 171 | ~47.76 Mha | Sensitivity only. Raw topographic/basin candidate envelope, highly fragmented and much broader. |
| `No_Crop_All_Height_Initial_CA` | 8,343 | 270 | ~70.80 Mha | Sensitivity only. Even broader initial envelope with additional height treatment and extra dam IDs. |

## Paper Framing

The main result should be phrased as irrigation expansion inside versus outside
the modeled, no-crop, capacity-limited large-dam command-area footprint. It is
not a direct observed irrigation-district boundary.

Yearly command-area layers should include dams only while they are active:
commissioned by the analysis year and not removed/decommissioned by that year.
The local GDW barrier layer includes `REM_YEAR`; in the current arid-SSA data it
is `-99` for all records inspected, so it does not change the current run.

The Initial layers can support a robustness appendix:

- If outside-command-area growth remains dominant under the broad Initial mask,
  the decentralization result is very robust.
- If the Initial mask absorbs much more growth, report that as an upper-bound
  sensitivity, but do not make it the primary estimand.
