// Export physical-envelope command areas for Paper 1.
//
// Required Code Editor imports, matching the original script:
//   dams0   - GDW dams/barriers
//   ResPM   - GDW reservoir polygons matched by GDW_ID
//   demx    - DEM image collection with band "DEM"
//   Country - country boundaries with ADM0_CODE
//   Yields  - country yield/capacity table with fields gaul and Yield
//   bas5, bas6, bas7 - HydroBASINS feature collections at levels 5, 6, and 7
//
// What this script does (and why):
//   1. Filters dams to any-use irrigation, height > 15 m (GDW USE_IRRI / MAIN_USE).
//   2. For each dam, builds a "service envelope" defined purely by physical
//      irrigation constraints:
//        - elevation: pixels below reservoir surface elevation + DZ_M
//        - basin context: HydroBASIN containing the dam, level chosen by
//          reservoir capacity
//        - country boundary
//        - distance: capacity-derived equivalent-circle radius, capped at
//          MAX_RADIUS_CAP_M
//   3. Vectorizes the envelope and exports it.
//
// Difference from the previous (no-crop / crop-calibrated) lineage:
//   - No 2019 cropland layer is used. Distance is derived from capacity and
//     country yield, not from where cropland happens to sit. This decouples
//     the command-area definition from the AEI data we will later intersect
//     against, and avoids dropping arid-SSA dams whose 2019 footprint is
//     fallow.
//   - Dams with missing country yield (yieldValue == 0) drop out via the
//     validCA flag and are visible in the diagnostics CSV.

// -----------------------------
// User settings
// -----------------------------

var MIN_DAM_HEIGHT_M = 15;
var DZ_M = 10;
var RESOLUTION_M = 30;
var MIN_VECTOR_AREA_M2 = 10000;
var MAX_DISTANCE_M = 2000000;
var SIMPLIFY_TOLERANCE_M = 0;
var SIMPLIFY_INITIAL_COMMAND_AREAS = false;

// Absolute cap on the service-envelope radius. 50 km matches typical arid-SSA
// gravity-fed schemes (e.g., Office du Niger). Multi-lift outliers like
// Gezira (~100 km) are not the target population; rerun with a larger cap to
// sensitivity-test those.
var MAX_RADIUS_CAP_M = 50000;

// Keep these false for normal runs. Map preview layers and command-area counts
// force interactive tile/count requests and can hit GEE request-rate limits.
var SHOW_MAP_LAYERS = false;
var PRINT_HEAVY_COMMAND_AREA_COUNTS = false;

var EXPORT_FINAL_COMMAND_AREAS = true;
var EXPORT_INITIAL_COMMAND_AREAS = false;
var EXPORT_DAM_AUDIT = true;
var EXPORT_COMMAND_AREA_DIAGNOSTICS = true;

// Local GDW inspection found USE_IRRI values "Main", "Major", and "Sec".
var IRRIGATION_USE_VALUES = ['main', 'major', 'sec'];

// Export names. These names are intentionally explicit so old exports are not
// accidentally mistaken for this physical-envelope version.
var FINAL_EXPORT_DESCRIPTION = 'Physical_Envelope_Command_Areas_AnyUse_Hgt15';
var INITIAL_EXPORT_DESCRIPTION = 'Physical_Envelope_Initial_CA_AnyUse_Hgt15';
var DAM_AUDIT_EXPORT_DESCRIPTION = 'GDW_AnyUse_Irrigation_Dams_Hgt15_Audit';
var CA_DIAGNOSTIC_EXPORT_DESCRIPTION = 'Physical_Envelope_Command_Areas_AnyUse_Hgt15_Diagnostics';


// -----------------------------
// Helpers
// -----------------------------

var safeNumber = function(value) {
  // Converts null/blank/nodata strings to 0 and clips negative sentinels to 0.
  var text = ee.String(ee.Algorithms.If(
    ee.Algorithms.IsEqual(value, null),
    '0',
    value
  ));
  text = ee.String(ee.Algorithms.If(text.length().eq(0), '0', text));
  return ee.Number.parse(text).max(0);
};

var safeString = function(value) {
  return ee.String(ee.Algorithms.If(
    ee.Algorithms.IsEqual(value, null),
    '',
    value
  ));
};

var valueOrZero = function(value) {
  return ee.Number(ee.Algorithms.If(
    ee.Algorithms.IsEqual(value, null),
    0,
    value
  ));
};

var firstPropertyOrZero = function(collection, propertyName) {
  return safeNumber(ee.Algorithms.If(
    collection.size().gt(0),
    ee.Feature(collection.first()).get(propertyName),
    0
  ));
};

var keepPolygonFeatures = function(collection) {
  return collection
    .map(function(ft) {
      return ft.set('Geom_type', ft.geometry().type());
    })
    .filter(ee.Filter.inList('Geom_type', ['Polygon', 'MultiPolygon']));
};


// -----------------------------
// Dam and reservoir selection
// -----------------------------

var damsPrepared = dams0.map(function(ft) {
  return ft.set({
    'DAM_HGT_M_NUM': safeNumber(ft.get('DAM_HGT_M')),
    'CAP_REP_NUM': safeNumber(ft.get('CAP_REP')),
    'CAP_MAX_NUM': safeNumber(ft.get('CAP_MAX')),
    'CAP_MIN_NUM': safeNumber(ft.get('CAP_MIN')),
    'CAP_MCM_NUM': safeNumber(ft.get('CAP_MCM')),
    'USE_IRRI_NORM': safeString(ft.get('USE_IRRI')).toLowerCase(),
    'MAIN_USE_NORM': safeString(ft.get('MAIN_USE')).toLowerCase()
  });
});

var reservoirsPrepared = ResPM.map(function(ft) {
  return ft.set({
    'CAP_MCM_NUM': safeNumber(ft.get('CAP_MCM')),
    'AREA_SKM_NUM': safeNumber(ft.get('AREA_SKM')),
    'ELEV_MASL_NUM': safeNumber(ft.get('ELEV_MASL'))
  });
});

var irrigationUseFilter = ee.Filter.or(
  ee.Filter.inList('USE_IRRI_NORM', IRRIGATION_USE_VALUES),
  ee.Filter.eq('MAIN_USE_NORM', 'irrigation')
);

var dams = damsPrepared
  .filter(irrigationUseFilter)
  .filter(ee.Filter.gt('DAM_HGT_M_NUM', MIN_DAM_HEIGHT_M));

print('Any-use irrigation dams > ' + MIN_DAM_HEIGHT_M + ' m:', dams.size());
if (SHOW_MAP_LAYERS) {
  Map.addLayer(dams, {color: 'black'}, 'Any-use irrigation dams > 15 m');
}

var damIds = dams.aggregate_array('GDW_ID').distinct();

var Lakes = reservoirsPrepared
  .filter(ee.Filter.inList('GDW_ID', damIds))
  .map(function(ft) {
    var fid = ft.get('GDW_ID');
    var matchedDam = ee.Feature(dams.filter(ee.Filter.eq('GDW_ID', fid)).first());
    return ft.set({
      'DAM_HGT_M': matchedDam.get('DAM_HGT_M'),
      'DAM_HGT_M_NUM': matchedDam.get('DAM_HGT_M_NUM'),
      'DAM_YEAR': matchedDam.get('YEAR_DAM'),
      'DAM_REM_YEAR': matchedDam.get('REM_YEAR'),
      'DAM_MAIN_USE': matchedDam.get('MAIN_USE'),
      'DAM_USE_IRRI': matchedDam.get('USE_IRRI')
    });
  });

dams = dams.filter(ee.Filter.inList('GDW_ID', Lakes.aggregate_array('GDW_ID').distinct()));

print('Dams with matched reservoirs:', dams.size());
print('Matched reservoirs:', Lakes.size());


// -----------------------------
// Capacity backup coefficient
// -----------------------------

var dem = ee.Image(demx.mean()).select('DEM');

var ResPMCap = Lakes.filter(ee.Filter.gt('CAP_MCM_NUM', 0));
var meanAreaSqKm = ee.Number(ResPMCap.aggregate_mean('AREA_SKM_NUM'));
var meanCapMcm = ee.Number(ResPMCap.aggregate_mean('CAP_MCM_NUM'));
var meanHeightM = ee.Number(
  dams
    .filter(ee.Filter.inList('GDW_ID', ResPMCap.aggregate_array('GDW_ID').distinct()))
    .aggregate_mean('DAM_HGT_M_NUM')
);

// Backup coefficient for dams with no reported capacity. Same fallback the
// original model used; only retained because some GDW capacity fields are
// blank for arid-SSA dams.
var backupCapRatio = ee.Number(ee.Algorithms.If(
  meanHeightM.multiply(meanAreaSqKm).gt(0),
  meanCapMcm.divide(meanHeightM.multiply(meanAreaSqKm)),
  0
));

print('Backup capacity ratio:', backupCapRatio);


// -----------------------------
// Per-dam command-area builder
// -----------------------------

var getCA = function(dam) {
  dam = ee.Feature(dam);
  var gdwId = dam.get('GDW_ID');

  var countryFc = Country.filterBounds(dam.geometry());
  var countryCode = ee.Algorithms.If(
    countryFc.size().gt(0),
    ee.Feature(countryFc.first()).get('ADM0_CODE'),
    null
  );
  var yieldFc = Yields.filter(ee.Filter.eq('gaul', countryCode));
  var yieldValue = firstPropertyOrZero(yieldFc, 'Yield');

  var res0 = ee.Feature(Lakes.filter(ee.Filter.eq('GDW_ID', gdwId)).first());

  // Capacity sources intentionally follow the original command-area model's
  // scaling because the Yield table is calibrated against those units. Do
  // not homogenize these unless Yields is also re-derived.
  var capRepM3 = ee.Number(dam.get('CAP_REP_NUM')).multiply(1e6);
  var capMaxM3 = ee.Number(dam.get('CAP_MAX_NUM')).multiply(1e6);
  var capMinM3 = ee.Number(dam.get('CAP_MIN_NUM')).multiply(1e6);
  var capMcmM3 = ee.Number(dam.get('CAP_MCM_NUM')).multiply(1e6);
  var resCapGdwM3 = capRepM3.max(capMaxM3).max(capMinM3).max(capMcmM3);

  var resCapBathy = ee.Number(res0.get('CAP_MCM_NUM'));
  var resAreaSqKm = ee.Number(res0.get('AREA_SKM_NUM'));
  var damHeightM = ee.Number(dam.get('DAM_HGT_M_NUM'));
  var backupCap = ee.Number(ee.Algorithms.If(
    backupCapRatio.gt(0),
    damHeightM.divide(backupCapRatio).multiply(resAreaSqKm),
    0
  ));

  var capList = ee.List([resCapBathy, resCapGdwM3, backupCap])
    .filter(ee.Filter.gt('item', 0));

  var resCapModel = ee.Number(ee.Algorithms.If(
    capList.length().gt(0),
    capList.reduce(ee.Reducer.mean()),
    0
  ));

  // Select basin level by capacity. Thresholds are 100 MCM and 1000 MCM.
  var bas0 = ee.FeatureCollection(
    ee.Algorithms.If(
      resCapModel.lt(100e6),
      bas7,
      ee.Algorithms.If(resCapModel.lte(1000e6), bas6, bas5)
    )
  ).filterBounds(dam.geometry());

  var countryMask = Country.filterBounds(res0.geometry());

  // Initial candidate envelope: below reservoir elevation + DZ_M, in basin
  // and country context, excluding the reservoir polygon itself.
  var demBelowDam = ee.Image(1).updateMask(
    dem.lt(ee.Number(res0.get('ELEV_MASL_NUM')).add(DZ_M))
  );

  var reservoirImage = ee.FeatureCollection([res0])
    .reduceToImage(['GDW_ID'], ee.Reducer.count());

  var initialImage = demBelowDam
    .clip(bas0)
    .clip(countryMask)
    .subtract(reservoirImage);
  initialImage = initialImage.updateMask(initialImage.gt(0));

  // Physical service-envelope radius from capacity and country yield.
  // theoryAreaM2 is the dam's theoretical irrigable area (m^2) given its
  // capacity and country crop water demand. Its equivalent-circle radius
  // bounds the distance from the reservoir at which gravity delivery is
  // plausible. MAX_RADIUS_CAP_M caps the radius for very large reservoirs
  // (multi-lift schemes are out of scope for this paper).
  var theoryAreaM2 = yieldValue.multiply(resCapModel);
  var radiusFromArea = theoryAreaM2.divide(Math.PI).sqrt();
  var maxDistM = radiusFromArea.min(MAX_RADIUS_CAP_M);

  var resdist = ee.FeatureCollection([res0]).distance({
    searchRadius: MAX_DISTANCE_M,
    maxError: 100
  });

  // validInputs no longer requires cropland presence. A dam drops out only
  // if its capacity, country yield, basin, or country context is missing.
  // The diagnostics CSV records validCA = false for these so dropouts are
  // attributable.
  var validInputs = resCapModel.gt(0)
    .and(yieldValue.gt(0))
    .and(bas0.size().gt(0))
    .and(countryMask.size().gt(0))
    .and(maxDistM.gt(0));

  var finalImage = ee.Image(1).updateMask(
    resdist.lte(maxDistM).multiply(initialImage)
  );

  // reduceToVectors needs a nonzero geometry even when maxDistM is small; the
  // floor at RESOLUTION_M prevents Feature.buffer(0) errors.
  var vectorGeometry = res0.geometry().buffer(maxDistM.max(RESOLUTION_M), RESOLUTION_M);

  var finalVectors = finalImage.reduceToVectors({
    geometry: vectorGeometry,
    scale: RESOLUTION_M,
    geometryType: 'polygon',
    bestEffort: true,
    maxPixels: 1e15,
    tileScale: 4
  })
    .map(function(ft) {
      return ft.set('area_tmp', ft.geometry().area(RESOLUTION_M));
    })
    .filter(ee.Filter.gt('area_tmp', MIN_VECTOR_AREA_M2));

  var validFinal = validInputs.and(finalVectors.size().gt(0));

  var finalFeature = ee.Feature(ee.Algorithms.If(
    validFinal,
    ee.Feature(finalVectors.union(RESOLUTION_M).first()).set('validCA', true),
    ee.Feature(dam.geometry()).buffer(1, RESOLUTION_M).set('validCA', false)
  ));

  finalFeature = finalFeature.set({
    'area': finalFeature.geometry().area(RESOLUTION_M),
    'GDW_ID': gdwId,
    'MaxDist': maxDistM,
    'MaxRadCap': MAX_RADIUS_CAP_M,
    'TheoryArea': theoryAreaM2,
    'ResCapMod': resCapModel,
    'dH': DZ_M,
    'Yield': yieldValue,
    'CountryGAUL': countryCode,
    'ResArea': resAreaSqKm,
    'ResCapBath': resCapBathy,
    'ResElev': res0.get('ELEV_MASL_NUM'),
    'DAM_HGT_M': damHeightM,
    'YEAR_DAM': dam.get('YEAR_DAM'),
    'REM_YEAR': dam.get('REM_YEAR'),
    'MAIN_USE': dam.get('MAIN_USE'),
    'USE_IRRI': dam.get('USE_IRRI'),
    'Geom_type': finalFeature.geometry().type(),
    'type': 'vectorized_physical_envelope_anyuse'
  });

  var initialFeatures = initialImage.reduceToVectors({
    geometry: bas0.geometry(),
    scale: RESOLUTION_M,
    geometryType: 'polygon',
    eightConnected: false,
    labelProperty: 'zone',
    bestEffort: true,
    maxPixels: 1e15,
    tileScale: 4
  })
    .map(function(ft) {
      return ft.set({
        'GDW_ID': gdwId,
        'type': 'initialCA_physical_envelope_anyuse',
        'area': ft.geometry().area(RESOLUTION_M),
        'YEAR_DAM': dam.get('YEAR_DAM'),
        'REM_YEAR': dam.get('REM_YEAR'),
        'MAIN_USE': dam.get('MAIN_USE'),
        'USE_IRRI': dam.get('USE_IRRI'),
        'DAM_HGT_M': damHeightM
      });
    })
    .filter(ee.Filter.gt('area', MIN_VECTOR_AREA_M2));

  return ee.FeatureCollection([finalFeature]).merge(initialFeatures);
};


// -----------------------------
// Build and export
// -----------------------------

var CA_all = dams.map(getCA).flatten();

var finalCAs = CA_all
  .filter(ee.Filter.eq('type', 'vectorized_physical_envelope_anyuse'))
  .filter(ee.Filter.neq('Geom_type', 'Empty'));

// Diagnostics include both validCA true and false so dropouts are visible.
var finalCaDiagnostics = finalCAs.map(function(ft) {
  return ee.Feature(null, ft.toDictionary());
});

var initialCAs = CA_all
  .filter(ee.Filter.eq('type', 'initialCA_physical_envelope_anyuse'))
  .filter(ee.Filter.gt('area', MIN_VECTOR_AREA_M2));

// Shapefile export uses only valid command areas; placeholders remain in the
// diagnostics CSV for attribution. Do not simplify final command areas before
// export: many valid arid-SSA envelopes are small enough that a 100 m
// simplification collapses them out of the shapefile.
var validFinalCAs = finalCAs.filter(ee.Filter.eq('validCA', true));

var simpleFinalCAs = keepPolygonFeatures(validFinalCAs);

var simpleInitialCAs = keepPolygonFeatures(initialCAs);

if (SIMPLIFY_INITIAL_COMMAND_AREAS) {
  simpleInitialCAs = keepPolygonFeatures(simpleInitialCAs.map(function(ft) {
    return ft.setGeometry(ft.geometry().simplify(SIMPLIFY_TOLERANCE_M));
  }));
}

if (PRINT_HEAVY_COMMAND_AREA_COUNTS) {
  print('Final command areas (valid only):', simpleFinalCAs.size());
  print('Initial command-area polygons:', simpleInitialCAs.size());
}

if (SHOW_MAP_LAYERS) {
  Map.addLayer(simpleInitialCAs.limit(20), {color: 'blue'}, 'Initial CAs, physical envelope');
  Map.addLayer(simpleFinalCAs.limit(20), {color: 'green'}, 'Final CAs, physical envelope');
}

if (EXPORT_FINAL_COMMAND_AREAS) {
  Export.table.toDrive({
    collection: simpleFinalCAs,
    description: FINAL_EXPORT_DESCRIPTION,
    fileNamePrefix: FINAL_EXPORT_DESCRIPTION,
    fileFormat: 'SHP'
  });
}

if (EXPORT_INITIAL_COMMAND_AREAS) {
  Export.table.toDrive({
    collection: simpleInitialCAs,
    description: INITIAL_EXPORT_DESCRIPTION,
    fileNamePrefix: INITIAL_EXPORT_DESCRIPTION,
    fileFormat: 'SHP'
  });
}

if (EXPORT_DAM_AUDIT) {
  Export.table.toDrive({
    collection: dams,
    description: DAM_AUDIT_EXPORT_DESCRIPTION,
    fileNamePrefix: DAM_AUDIT_EXPORT_DESCRIPTION,
    fileFormat: 'CSV'
  });
}

if (EXPORT_COMMAND_AREA_DIAGNOSTICS) {
  Export.table.toDrive({
    collection: finalCaDiagnostics,
    description: CA_DIAGNOSTIC_EXPORT_DESCRIPTION,
    fileNamePrefix: CA_DIAGNOSTIC_EXPORT_DESCRIPTION,
    fileFormat: 'CSV'
  });
}
