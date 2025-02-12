
-------BUCKET: BCDM; COLLECTION: primary

CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`

--geography
create index bcdm_country_ocean IF NOT EXISTS on BCDM._default.`primary`(`country/ocean`);
create index bcdm_province_state IF NOT EXISTS on BCDM._default.`primary`(`province/state`);

--taxonomy
create index bcdm_subspecies IF NOT EXISTS on BCDM._default.`primary`(`subspecies`);
create index bcdm_species IF NOT EXISTS on BCDM._default.`primary`(`species`);
create index bcdm_genus IF NOT EXISTS on BCDM._default.`primary`(`genus`);
create index bcdm_tribe IF NOT EXISTS on BCDM._default.`primary`(`tribe`);
create index bcdm_subfamily IF NOT EXISTS on BCDM._default.`primary`(`subfamily`);
create index bcdm_family IF NOT EXISTS on BCDM._default.`primary`(`family`);
create index bcdm_class IF NOT EXISTS on BCDM._default.`primary`(`class`);
create index bcdm_order IF NOT EXISTS on BCDM._default.`primary`(`order`);
create index bcdm_phylum IF NOT EXISTS on BCDM._default.`primary`(`phylum`);
create index bcdm_kingdom IF NOT EXISTS on BCDM._default.`primary`(`kingdom`);
create index bcdm_bin_uri IF NOT EXISTS on BCDM._default.`primary`(`bin_uri`);

--institutions
create index bcdm_inst IF NOT EXISTS on BCDM._default.`primary`(`inst`);
create index bcdm_sequence_run_site IF NOT EXISTS on BCDM._default.`primary`(`sequence_run_site`);

--identifiers
create index bcdm_processid IF NOT EXISTS on BCDM._default.`primary`(`processid`);
create index bcdm_sampleid IF NOT EXISTS on BCDM._default.`primary`(`sampleid`);
create index bcdm_fieldid IF NOT EXISTS on BCDM._default.`primary`(`fieldid`);
create index bcdm_specimenid IF NOT EXISTS on BCDM._default.`primary`(`specimenid`);


--dates
create index bcdm_collection_date_start IF NOT EXISTS on BCDM._default.`primary`(`collection_date_start`);
create index bcdm_sequence_upload_date IF NOT EXISTS on BCDM._default.`primary`(`sequence_upload_date`);


--create index bcdm_processid_minted_date IF NOT EXISTS on BCDM._default.`primary`(processid_minted_date);


--extensions
--create index bcdm_marker_code IF NOT EXISTS on BCDM._default.`primary`(marker_code);


--recordset array
CREATE INDEX bcdm_recordset_arr IF NOT EXISTS on `default`:`BCDM`.`_default`.`primary`((distinct (array `val` for `val` in `bold_recordset_code_arr` end)))

--covering indexes
CREATE INDEX idx_province_state_search_stats IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`(`province/state`,`species`,`processid`,`inst`,`bin_uri`)

CREATE INDEX idx_phylum_search_stats IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`(`phylum`,`species`,`processid`,`inst`,`bin_uri`)
CREATE INDEX idx_class_search_stats IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`(`class`,`species`,`processid`,`inst`,`bin_uri`)
CREATE INDEX idx_order_search_stats IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`(`order`,`species`,`processid`,`inst`,`bin_uri`)
CREATE INDEX idx_familydown_search_stats IF NOT EXISTS ON `default`:`BCDM`.`_default`.`primary`(`subspecies`,`species`,`genus`,`tribe`,`subfamily`,`family`,`processid`,`inst`,`bin_uri`)



-------BUCKET: DERIVED; COLLECTION: accepted_terms
CREATE PRIMARY INDEX  IF NOT EXISTS on  `default`:`DERIVED`.`_default`.`accepted_terms`
CREATE INDEX accepted_terms_combined IF NOT EXISTS ON `DERIVED`.`_default`.`accepted_terms` (`standardized_term`,`scope`,`field`,`records`);
CREATE INDEX accepted_terms_combined_original IF NOT EXISTS ON `DERIVED`.`_default`.`accepted_terms` (`term`,`scope`,`field`,`records`);



-------BUCKET: DERIVED; COLLECTION: tax_geo_inst_summaries

CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`tax_geo_inst_summaries`
CREATE INDEX idx_tax_geo_inst_summaries_tax_geo_inst_id IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`tax_geo_inst_id`)
CREATE INDEX idx_tax_geo_inst_summaries_inst IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`inst`)
CREATE INDEX idx_tax_geo_inst_summaries_country_ocean IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`country/ocean`)
CREATE INDEX idx_tax_geo_inst_summaries_province_state IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`province/state`)
CREATE INDEX idx_tax_geo_inst_summaries_kingdom IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`kingdom`)
CREATE INDEX idx_tax_geo_inst_summaries_phylum IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`phylum`)
CREATE INDEX idx_tax_geo_inst_summaries_class IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`class`)
CREATE INDEX idx_tax_geo_inst_summaries_order IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`order`)
CREATE INDEX idx_tax_geo_inst_summaries_family IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`family`)
CREATE INDEX idx_tax_geo_inst_summaries_subfamily IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`subfamily`)
CREATE INDEX idx_tax_geo_inst_summaries_tribe IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`tribe`)
CREATE INDEX idx_tax_geo_inst_summaries_genus IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`genus`)
CREATE INDEX idx_tax_geo_inst_summaries_species IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`species`)
CREATE INDEX idx_tax_geo_inst_summaries_subspecies IF NOT EXISTS ON `DERIVED`.`_default`.`tax_geo_inst_summaries`(`subspecies`)

CREATE INDEX tax_geo_inst_summaries_combined IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`tax_geo_inst_summaries`(`inst`,`country/ocean`,`province/state`,`kingdom`,`phylum`,`class`,`order`,`family`,`subfamily`,`aggregates`.`inst`,`aggregates`.`identified_by`,`aggregates`.`collection_date_start`,`aggregates`.`sequence_run_site`,`aggregates`.`sequence_upload_date`)

-------BUCKET: DERIVED; COLLECTION: institution_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`institution_summaries`
CREATE INDEX idx_institution_summaries_name IF NOT EXISTS ON `DERIVED`.`_default`.`institution_summaries`(`inst`)
-------BUCKET: DERIVED; COLLECTION: sequence_run_site_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`sequence_run_site_summaries`;
CREATE INDEX idx_sequence_run_site_summaries_name IF NOT EXISTS ON `DERIVED`.`_default`.`sequence_run_site_summaries`(`sequence_run_site`);
-------BUCKET: DERIVED; COLLECTION: country_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`country_summaries`
CREATE INDEX idx_country_summaries_name IF NOT EXISTS ON `DERIVED`.`_default`.`country_summaries`(`country/ocean`)
-------BUCKET: DERIVED; COLLECTION: bin_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`bin_summaries`
CREATE INDEX idx_bin_summaries_binuri IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`bin_summaries`(`bin_uri`)
-------BUCKET: DERIVED; COLLECTION: dataset_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`dataset_summaries`;
CREATE INDEX idx_dataset_summaries_datasetcode IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`dataset_summaries`(`dataset.code`);
CREATE INDEX idx_dataset_summaries_recordset_arr IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`dataset_summaries`((distinct (array `val` for `val` in `bold_recordset_code_arr` end)));
-------BUCKET: DERIVED; COLLECTION: primer_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`primer_summaries`;
CREATE INDEX idx_primer_summaries_name IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`primer_summaries`(`name`);
-------BUCKET: DERIVED; COLLECTION: taxonomy_summaries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`taxonomy_summaries`;
CREATE INDEX idx_taxonomy_summaries_taxid IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`taxonomy_summaries`(`taxid`);
CREATE INDEX idx_taxonomy_summaries_parent_taxid IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`taxonomy_summaries`(`parent_taxid`);
CREATE INDEX idx_taxonomy_summaries_taxon IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`taxonomy_summaries`(`taxon`);
CREATE INDEX idx_taxonomy_summaries_rank_name IF NOT EXISTS ON `default`:`DERIVED`.`_default`.`taxonomy_summaries`(`rank_name`);

-------BUCKET: ANCILLARY; COLLECTION: datasets
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`datasets`;
CREATE INDEX datasets_code IF NOT EXISTS on ANCILLARY._default.datasets (`dataset.code`)


-------BUCKET: ANCILLARY; COLLECTION: barcodeclusters
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`barcodeclusters`;
CREATE INDEX barcodeclusters_uri IF NOT EXISTS on ANCILLARY._default.barcodeclusters (`barcodecluster.uri`)


-------BUCKET: ANCILLARY; COLLECTION: countries
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`countries`;
CREATE INDEX countries_name IF NOT EXISTS ON ANCILLARY._default.countries (`name`);
CREATE INDEX countries_iso_alpha_2 IF NOT EXISTS ON ANCILLARY._default.countries (`iso_alpha_2`);

-------BUCKET: ANCILLARY; COLLECTION: institutions
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`institutions`;
CREATE INDEX institution_name IF NOT EXISTS ON ANCILLARY._default.institutions (`name`);

-------BUCKET: ANCILLARY; COLLECTION: primers
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`primers`;
CREATE INDEX primer_name IF NOT EXISTS ON ANCILLARY._default.primers (`name`);

-------BUCKET: ANCILLARY; COLLECTION: taxonomies
CREATE PRIMARY INDEX IF NOT EXISTS ON `default`:`ANCILLARY`.`_default`.`taxonomies`;
CREATE INDEX taxonomy_taxid IF NOT EXISTS ON ANCILLARY._default.taxonomies (`taxid`);
