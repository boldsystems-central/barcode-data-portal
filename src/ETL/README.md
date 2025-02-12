# Database Specification - Couchbase Documents

## Primary Data - `BCDM`.`_default`.`primary`
```json
{
  "bin_created_date": "2013-01-12",
  "bin_uri": "BOLD:ACC4615",
  "bold_recordset_code_arr": [
    "DS-19GMPFI1",
    "DS-20GMP28",
    "DS-BRACDQ",
    "DS-EURINSCT",
    "DS-GMTPC",
    "GMFID"
  ],
  "class": "Insecta",
  "collection_code": "BIOUG",
  "collection_date_end": "2012-07-07",
  "collection_date_start": "2012-06-27",
  "collectors": "Marko Mutanen",
  "coord": [
    65.148,
    25.838
  ],
  "coord_source": "GPS",
  "country/ocean": "Finland",
  "country_iso": "FI",
  "ecoregion": "Scandinavian_and_Russian_taiga",
  "family": "Braconidae",
  "fieldid": "GMP#00460",
  "funding_src": "iBOL:WG1.6",
  "genus": "Ichneutes",
  "geoid": 4364,
  "identification": "Ichneutes",
  "identification_method": "Morphology (Apr 2018)",
  "identification_rank": "genus",
  "identified_by": "M. J. Sharkey",
  "inst": "Centre for Biodiversity Genomics",
  "kingdom": "Animalia",
  "marker_code": "COI-5P",
  "marker_count": 1,
  "museumid": "BIOUG04081-D06",
  "nuc": "AATTTTATATTTTTTGTTTGGTATATGATCTGGTATTATAGGTTTATCTTTGAGGATGATTATTCGTATAGAATTAAGAATTTGTGGTAAATTAATTAATAATGATCAAATTTATAATAGAATTGTTACATTACATGCTTTTGTAATAATTTTTTTTATAGTTATACCAGTTATAATTGGAGGATTTGGTAATTGATTGATTCCTTTAATGTTAGGGTCTCCAGATATGGCTTTCCCTCGAATAAATAATATAAGATTTTGATTACTTGTACCTTCAATATTTTTTTTAATAGTTAGAAGATTAATAATGAGGGGGGTTGGGACAGGATGAACTATTTATCCTCCATTATCTTTAAATATAGGACATAGAGGTATATCAGTAGATTTATGTATTTTTTCATTACATTTAGCTGGAATTTCTTCAATTATAGGTGCTATTAATTTTATTACAACTATTATAAATTTACGTTCAAATTTATTTTTAATGGATAAAATTTCTTTATTTAGTTGATCTGTAATAATTACTGCTATTTTATTATTATTATCTTTACCAGTATTAGCAGGGGCTATTACTATATTATTAACAGATCGTAATTTAAATACTTCATTTTTTgaTCCaTCAG-----------",
  "nuc_basecount": 623,
  "order": "Hymenoptera",
  "phylum": "Arthropoda",
  "pre_md5hash": "95618640d83dfcf20c4c1f40c7ed53b2",
  "primers_forward": [
    "LepF1:ATTCAACCAATCATAAAGATATTGG"
  ],
  "primers_reverse": [
    "LepR1:TAAACTTCTGGATGTCCAAAAAATCA"
  ],
  "processid": "GMFID492-12",
  "processid_minted_date": "2012-11-23",
  "province/state": "Northern Ostrobothnia",
  "realm": "Palearctic",
  "record_id": "GMFID492-12.COI-5P",
  "region": "Oulu, NE of Kiiminki",
  "reproduction": " ",
  "sampleid": "BIOUG04081-D06",
  "sampling_protocol": "Malaise Trap",
  "sequence_run_site": "Centre for Biodiversity Genomics",
  "sequence_upload_date": "2013-04-30",
  "sex": " ",
  "site_code": "BIOUG:OULU",
  "specimenid": 2931994,
  "subfamily": "Ichneutinae",
  "taxid": 204095,
  "taxonomy_notes": "CollectionsID",
  "voucher_type": "Vouchered:Registered Collection"
}
```

## Summary - `DERIVED`.`_default`.`tax_geo_summaries`
```json
{
  "country/ocean": "Finland",
  "counts": {
    "bin_uri": 1,
    "species": 1,
    "specimens": 5,
    "sequences": 5
  },
  "aggregates": {
    "identified_by": {
      "Marko Mutanen": 5
    },
    "marker_code": {
      "COI-5P": 5
    },
    "country/ocean": {
      "Finland": 5
    },
    "inst": {
      "University of Oulu, Zoological Museum": 5
    },
    "coord": {
      "(64.9, 25.6)": 1,
      "(65.1, 25.7)": 1,
      "(66.3, 29.2)": 1,
      "(65.1, 25.8)": 1,
      "(66.3, 29.6)": 1
    },
    "sequence_upload_date": {
      "2010-07": 1,
      "2011-03": 2,
      "2012-01": 2
    },
    "sequence_run_site": {
      "Centre for Biodiversity Genomics": 5
    },
    "collection_date": {
      "2009-06": 1,
      "2005-06": 1,
      "2003-07": 1,
      "2011-06": 2
    },
    "species": {
      "Phiaris turfosana": 5
    },
    "bin_uri": {
      "BOLD:ACF5701": 5
    }
  },
  "kingdom": "Animalia",
  "phylum": "Arthropoda",
  "class": "Insecta",
  "order": "Lepidoptera",
  "family": "Tortricidae",
  "subfamily": "Olethreutinae",
  "tribe": "Olethreutini",
  "genus": "Phiaris",
  "species": "Phiaris turfosana",
  "subspecies": null,
  "province": null,
  "taxid": 183458,
  "geoid": 198
}
```

## Terms - `DERIVED`.`_default`.`accepted_terms`
```json
{
  "geoid": 198,
  "scope": "geo",
  "field": "country/ocean",
  "geo_path": {
    "geoid": 198,
    "country/ocean": "Finland"
  },
  "records": 64327,
  "summaries": 0,
  "term": "Finland"
}
```

## Datasets - `ANCILLARY`.`_default`.`datasets`
```json
{
  "dataset.code": "DS-GMTPC",
  "dataset.created": "2021-04-23",
  "dataset.descr": "The dataset includes all Finnish barcode records of the Global Malaise campaign of 2012.",
  "dataset.doi": "10.5883/DS-GMTPC",
  "dataset.title": "Global Malaise 2012 - Finland",
  "dataset.type": "personal",
  "pre_md5hash": "438cb9419732f4871ce41fe3c8216bd6",
  "users": [
    "Mikko Pentinsaari",
    "Panu Somervuo",
    "Tomas Roslin",
    "Marko Mutanen"
  ],
  "users_access": [
    10,
    10,
    10,
    12
  ],
  "users_affiliation": [
    "Centre for Biodiversity Genomics",
    "University of Helsinki",
    "University of Helsinki",
    "University of Oulu"
  ]
}
```

## Barcode Clusters - `ANCILLARY`.`_default`.`barcodeclusters`
```json
{
  "barcodecluster.avgdist": 1.07596,
  "barcodecluster.doi": "10.5883/BOLD:AEY9263",
  "barcodecluster.maxdist": 2.08668,
  "barcodecluster.mindist": 0,
  "barcodecluster.nn_dist": 1.12179,
  "barcodecluster.uri": "BOLD:AEY9263",
  "nearestneighbour.uri": "BOLD:AAA4194",
  "pre_md5hash": "c80ad84fb7b0c20150f20589e02b6575",
  "record_count": "38",
  "unique_taxids": 1
}
```

## Publications - `ANCILLARY`.`_default`.`publications`
```json
{

}
```
