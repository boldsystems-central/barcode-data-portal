-- BUCKET: BCDM

CREATE COLLECTION `BCDM`.`_default`.`primary` IF NOT EXISTS;

-- BUCKET: DERIVED

CREATE COLLECTION `DERIVED`.`_default`.`accepted_terms` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`tax_geo_inst_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`country_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`institution_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`sequence_run_site_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`bin_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`dataset_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`primer_summaries` IF NOT EXISTS;
CREATE COLLECTION `DERIVED`.`_default`.`taxonomy_summaries` IF NOT EXISTS;

-- BUCKET: ANCILLARY

CREATE COLLECTION `ANCILLARY`.`_default`.`barcodeclusters` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`datasets` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`publications` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`countries` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`institutions` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`primers` IF NOT EXISTS;
CREATE COLLECTION `ANCILLARY`.`_default`.`taxonomies` IF NOT EXISTS;
