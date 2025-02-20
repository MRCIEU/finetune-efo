library(fedmatch)
library(dplyr)
library(data.table)


dat <- fread("/local-scratch/projects/genotype-phenotype-map/results/studies_processed.tsv")

str(dat)

dat %>% filter(data_type == "phenotype") %>% group_by(data_type, variant_type, source) %>% summarise(n = n())

dat <- subset(dat, data_type == "phenotype" & source != "ebi_catalog")

# Match rare and common studies

az_exwas vs ukb
backman vs ukb
genebass vs ukb


do_matches <- function(dat, sourcestring) {

    match_exact <- merge_plus(
        subset(dat, source == sourcestring & variant_type == "rare_exome") %>% select(study_name_rare = study_name, trait, source),
        subset(dat, source == "ukb" & variant_type == "common") %>% select(study_name_common = study_name, trait, source),
        by=c("trait"),
        suffixes=c("_rare", "_common"),
        unique_key_1="study_name_rare",
        unique_key_2="study_name_common",
        match_type = "exact"
    )

    dat2 <- subset(dat, ! study_name %in% match_exact$matches$study_name_rare)

    match_fuzzy <- merge_plus(
        subset(dat2, source == sourcestring & variant_type == "rare_exome") %>% select(study_name_rare = study_name, trait, source),
        subset(dat2, source == "ukb" & variant_type == "common") %>% select(study_name_common = study_name, trait, source),
        by=c("trait"),
        suffixes=c("_rare", "_common"),
        unique_key_1="study_name_rare",
        unique_key_2="study_name_common",
        match_type = "fuzzy"
    )

    dat3 <- subset(dat2, ! study_name %in% match_fuzzy$matches$study_name_rare)

    # clean up trait by removing special characters
    dat3$trait2 <- gsub("[^[:alnum:]$]", " ", dat3$trait) %>% tolower() 
    # remove extraneous spaces
    dat3$trait2 <- gsub("\\s+", " ", dat3$trait2)
    head(dat3 %>% select(trait, trait2))

    match_fuzzy2 <- merge_plus(
        subset(dat3, source == sourcestring & variant_type == "rare_exome") %>% select(study_name_rare = study_name, trait, trait2, source),
        subset(dat3, source == "ukb" & variant_type == "common") %>% select(study_name_common = study_name, trait, trait2, source),
        by=c("trait2"),
        suffixes=c("_rare", "_common"),
        unique_key_1="study_name_rare",
        unique_key_2="study_name_common",
        match_type = "fuzzy"
    )

    dat4 <- subset(dat3, ! study_name %in% match_fuzzy2$matches$study_name_rare)

    match_fuzzy3 <- merge_plus(
        subset(dat4, source == sourcestring & variant_type == "rare_exome") %>% select(study_name_rare = study_name, trait, trait2, source),
        subset(dat4, source == "ukb" & variant_type == "common") %>% select(study_name_common = study_name, trait, trait2, source),
        by=c("trait2"),
        suffixes=c("_rare", "_common"),
        unique_key_1="study_name_rare",
        unique_key_2="study_name_common",
        match_type = "fuzzy",
        fuzzy_settings = build_fuzzy_settings(p=0.15)
    )


    match_fuzzy4 <- merge_plus(
        subset(dat4, source == sourcestring & variant_type == "rare_exome") %>% select(study_name_rare = study_name, trait, trait2, source),
        subset(dat4, source == "ukb" & variant_type == "common") %>% select(study_name_common = study_name, trait, trait2, source),
        by=c("trait2"),
        suffixes=c("_rare", "_common"),
        unique_key_1="study_name_rare",
        unique_key_2="study_name_common",
        match_type = "fuzzy",
        fuzzy_settings = build_fuzzy_settings(method = "wgt_jaccard", nthread = 10, maxDist = .2)
    )



    result <- bind_rows(
        tryCatch(match_exact$matches %>% mutate(match_type = "exact"), error = function(e) data.frame()),
        tryCatch(match_fuzzy$matches %>% mutate(match_type = "fuzzy"), error = function(e) data.frame()),
        tryCatch(match_fuzzy2$matches %>% mutate(match_type = "fuzzy2"), error = function(e) data.frame()),
        tryCatch(match_fuzzy3$matches %>% mutate(match_type = "fuzzy3"), error = function(e) data.frame()),
        tryCatch(match_fuzzy4$matches %>% mutate(match_type = "fuzzy4"), error = function(e) data.frame())
    ) %>% select(-c(trait2_common, trait2_rare))

    return(result)
}

az_matches <- do_matches(dat, "az_exwas")
backman_matches <- do_matches(dat, "backman")
genebass_matches <- do_matches(dat, "genebass")

dim(backman_matches)
dim(genebass_matches)
dim(az_matches)

str(az_matches)

write.csv(bind_rows(az_matches, backman_matches, genebass_matches), "rare_common_ukb.csv", row.names = FALSE)
