"""ArcGIS source definitions for OpenSkagit."""

SOURCES = {
    "arcgis_parcels": {
        "table": "arcgis_parcels",
        "url": "https://gis.skagitcountywa.gov/arcgis/rest/services/OpenData/AssessorDataParcels/FeatureServer",
        "layer": 0,
    },
    "arcgis_zoning": {
        "table": "arcgis_zoning",
        "url": "https://gis.skagitcountywa.gov/arcgis/rest/services/Planning/ComprehensivePlanWebMap/MapServer",
        "layer": 14,
    },
}
