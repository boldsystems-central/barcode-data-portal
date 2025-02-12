DROP VIEW IF EXISTS bold4_singlepane_view;
CREATE VIEW bold4_singlepane_view AS (
SELECT seqentry.id AS "seqentry.id",
    seqentry.processid AS "seqentry.processid",
    seqentry.processid || '.' || marker.code AS "seqentry.processid.marker.code",
    seqdata.gb_asc AS "seqdata.gb_asc",
    specimen.sampleid AS "specimen.sampleid",
    specimen.id AS "specimen.id",
    specimen.fk_tax AS "specimen.taxid",
    trim( regexp_replace(specimen.extrainfo, '[\n\r]+', ' ', 'g' )) AS "specimen.extrainfo",
    specimen.identification_method AS "specimen.identification_method",
    specimen.catalognum AS "specimen.catalognumber", -- museumid,
    specimen.isolate AS "specimen.isolate", -- fieldid,
    specimen.collectioncode AS "specimen.collectioncode",
    TO_CHAR(specimen.created, 'YYYY-MM-DD') AS "specimen.created",
    specimen__inst.name AS "specimen.inst.name",
    specimendetails.verbatim_depository AS "specimendetails.verbatim_depository",
    specimendetails.fundingsrc AS "specimendetails.fundingsrc",
    specimendetails.sex AS "specimendetails.sex",
    specimendetails.lifestage AS "specimendetails.lifestage",
    specimendetails.reproduction AS "specimendetails.reproduction",
    specimendetails.habitat AS "specimendetails.habitat",
    specimendetails.collectors AS "specimendetails.collectors",
    specimendetails.sitecode AS "specimendetails.sitecode",
    specimendetails.linkout AS "specimendetails.linkout",
    specimendetails.collection_event_id AS "specimendetails.collection_event_id",
    specimendetails.sampling_protocol AS "specimendetails.sampling_protocol",
    specimendetails.tissuetype AS "specimendetails.tissuetype",
    TO_CHAR(specimendetails.collectiondate, 'YYYY-MM-DD') AS "specimendetails.collectiondate",
    specimendetails.verbatim_collectiondate AS "specimendetails.verbatim_collectiondate",
    specimendetails.collectiontime AS "specimendetails.collectiontime",
    specimendetails.collectiondate_precision AS "specimendetails.collectiondate_precision",
    specimendetails.associated_taxa AS "specimendetails.associated_taxa",
    specimendetails.associated_specimens AS "specimendetails.associated_specimens",
    specimendetails.vouchertype AS "specimendetails.vouchertype",
    trim( regexp_replace(specimendetails__notes.note, '[\n\r]+', ' ', 'g' )) AS "specimendetails__notes.notes.note",
    trim( regexp_replace(specimendetails__taxnotes.note, '[\n\r]+', ' ', 'g' ))  AS "specimendetails__taxnotes.notes.note",
    trim( regexp_replace(specimendetails__collectionnote.note, '[\n\r]+', ' ', 'g' ))  AS "specimendetails__collectionnote.notes.note",
    specimendetails.verbatim_kingdom AS "specimendetails.verbatim_kingdom",
    specimendetails.verbatim_phylum AS "specimendetails.verbatim_phylum",
    specimendetails.verbatim_class AS "specimendetails.verbatim_class",
    specimendetails.verbatim_order AS "specimendetails.verbatim_order",
    specimendetails.verbatim_family AS "specimendetails.verbatim_family",
    specimendetails.verbatim_subfamily AS "specimendetails.verbatim_subfamily",
    specimendetails.verbatim_tribe AS "specimendetails.verbatim_tribe",
    specimendetails.verbatim_genus AS "specimendetails.verbatim_genus",
    specimendetails.verbatim_species AS "specimendetails.verbatim_species",
    specimendetails.verbatim_species_reference AS "specimendetails.verbatim_species_reference",
    specimendetails.verbatim_identifier AS "specimendetails.verbatim_identifier",

    location.fk_geopol AS "location.geopolid",
    location.verbatim_country AS "location.verbatim_country",
    location.verbatim_province AS "location.verbatim_province",
    location.verbatim_country_iso_alpha3 AS "location.verbatim_country_iso_alpha3",

    marker.code AS "marker.code",
    tax_division.name AS "tax__tax_division.tax_division.name",
    tax_denorm_mat.phylum AS "tax_denorm_mat.phylum",
    tax_denorm_mat.class AS "tax_denorm_mat.class",
    tax_denorm_mat."order" AS "tax_denorm_mat.order",
    tax_denorm_mat.family AS "tax_denorm_mat.family",
    tax_denorm_mat.subfamily AS "tax_denorm_mat.subfamily",
    tax_denorm_mat.tribe AS "tax_denorm_mat.tribe",
    tax_denorm_mat.genus AS "tax_denorm_mat.genus",
    tax_denorm_mat.species AS "tax_denorm_mat.species",
    tax_denorm_mat.subspecies AS "tax_denorm_mat.subspecies",
    tax.taxon AS "tax.taxon",
    tax_rank.rank_name AS "tax__tax_rank.tax_rank.name",
    tax_rank.numerical_posit AS "tax_rank.numerical_posit",
    trim( regexp_replace(tax.refr, '[\n\r]+', ' ', 'g' )) AS "tax.refr",
    person.fullname AS "specimendetails__identifier.person.fullname",
    person.email AS "specimendetails__identifier.person.email",
    seqdata__inst.name AS "seqdata__site.inst.name",
    seqdata.nucraw AS "seqdata.nucraw",
    seqdata.nucraw_a_count + seqdata.nucraw_c_count + seqdata.nucraw_g_count + seqdata.nucraw_t_count AS "seqdata.nucraw_basecount",
    TO_CHAR(seqdata.update, 'YYYY-MM-DD') AS "seqdata.updated",
    barcodecluster.uri AS "barcodecluster.uri",
    TO_CHAR(barcodecluster.created, 'YYYY-MM-DD') AS "barcodecluster.created",
    location.elev AS "location.elev",
    location.depth AS "location.depth",
    CASE
        WHEN location.lat IS NULL OR location.long IS NULL
        THEN NULL
        ELSE ARRAY[location.lat, location.long]
    END AS "location.coord",
    location.verbatim_coord AS "location.verbatim_coord",
    location.gps_source AS "location.gps_source",
    location.gps_accuracy AS "location.gps_accuracy",
    location.elev_accuracy AS "location.elev_accuracy",
    location.depth_accuracy AS "location.depth_accuracy",
    trim( regexp_replace(locatdesc.region, '[\n\r]+', ' ', 'g' ))  AS "locatdesc.region",
    trim( regexp_replace(locatdesc.sector, '[\n\r]+', ' ', 'g' )) AS "locatdesc.sector",
    trim( regexp_replace(locatdesc.site, '[\n\r]+', ' ', 'g' )) AS "locatdesc.site",
    geopol_denorm.country_iso AS "geopol_denorm.country_iso",
    geopol_denorm.country AS "geopol_denorm.country",
    geopol_denorm.province AS "geopol_denorm.province",
    --pcr_compact_view.primers_f AS "pcr_compact_view.primers_f",
    --pcr_compact_view.primers_r AS "pcr_compact_view.primers_r",
    ARRAY_PREPEND(project.code, dataset_seq_pivot_mat.dataset_code_arr) AS "recordset.code__arr"

    FROM seqentry

    LEFT JOIN seqdata ON seqdata.fk_seqentry = seqentry.id
    LEFT JOIN marker ON marker.id = seqdata.fk_marker
    LEFT JOIN specimen ON specimen.id = seqentry.fk_specimen
    LEFT JOIN specimendetails ON specimendetails.fk_specimen = specimen.id

    LEFT JOIN barcodecluster_seqentry ON barcodecluster_seqentry.fk_seqentry = seqentry.id
    LEFT JOIN barcodecluster ON barcodecluster.id = barcodecluster_seqentry.fk_barcodecluster

    LEFT JOIN tax_denorm_mat ON tax_denorm_mat.taxid = specimen.fk_tax
    LEFT JOIN tax ON tax.id = specimen.fk_tax
    LEFT JOIN tax_rank ON tax_rank.id = tax.fk_tax_rank
    LEFT JOIN tax_division ON tax_division.id = tax.fk_tax_division

    LEFT JOIN location ON location.fk_specimen = specimen.id
    LEFT JOIN locatdesc ON locatdesc.fk_location = location.id
    LEFT JOIN geopol_denorm ON geopol_denorm.id = location.fk_geopol

    LEFT JOIN person ON person.id = specimendetails.fk_identifier
    LEFT JOIN inst seqdata__inst ON seqdata__inst.id = seqdata.fk_site
    LEFT JOIN inst specimen__inst ON specimen__inst.id = specimen.fk_inst
    LEFT JOIN notes specimendetails__notes ON specimendetails__notes.id = specimendetails.fk_notes
    LEFT JOIN notes specimendetails__taxnotes ON specimendetails__taxnotes.id = specimendetails.fk_taxnotes
    LEFT JOIN notes specimendetails__collectionnote ON specimendetails__collectionnote.id = specimendetails.fk_collectionnote

    --LEFT JOIN pcr_compact_view ON pcr_compact_view.fk_seqentry = seqentry.id

    LEFT JOIN dataset_seq_pivot_mat ON dataset_seq_pivot_mat.fk_seqentry = seqentry.id
    LEFT JOIN project_seq ON project_seq.fk_seqentry = seqentry.id
    LEFT JOIN project ON project.id = project_seq.fk_project
);

GRANT SELECT ON bold4_singlepane_view TO apache;
GRANT SELECT ON bold4_singlepane_view TO datamanager;