-------BUCKET: DERIVED; COLLECTION: accepted_terms
CREATE PRIMARY INDEX  IF NOT EXISTS on  `default`:`DERIVED`.`_default`.`accepted_terms`
CREATE INDEX accepted_terms_combined IF NOT EXISTS ON `DERIVED`.`_default`.`accepted_terms` (`standardized_term`,`scope`,`field`,`records`);
CREATE INDEX accepted_terms_combined_original IF NOT EXISTS ON `DERIVED`.`_default`.`accepted_terms` (`term`,`scope`,`field`,`records`);


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
