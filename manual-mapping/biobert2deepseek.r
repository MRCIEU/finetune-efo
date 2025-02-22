library(glue)
library(dplyr)
library(data.table)
library(here)
library(jsonlite)

rm(list=ls())
a <- fread(here("manual-mapping", "bio-bert", "similarity.csv"))

run_prompt <- function(a, tr, model="deepseek-r1:7b") {
    efo <- a %>% 
        filter(trait == tr) %>%
        pull(efo) %>%
        paste("-", .) %>% paste(collapse = "\n")
    prompt <- glue("This is a term used to describe a trait that was analysed in genome-wide association study: \"{tr}\". Find the most appropriate EFO term for this trait from the list below. I do not expect an exact match, but getting something that is conceptually close will suffice:\n\n{efo}\n\nWhen you find an EFO term that is conceptually close, make sure to return the exact efo term. Return your answer in json format with the format {{\"trait\": \"{tr}\", \"efo\": \"<efo term>\", \"confidence\":<score>}}, where the \"confidence\" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match.")

    cmd <- glue("ollama run {model} '{prompt}'")
    res <- system(cmd, intern = TRUE)
    res <- grep("^\\{", res, value = TRUE) %>% jsonlite::fromJSON()
    return(res)
}


# ollama run deepseek-r1:1.5b 'This is a term used to describe a trait that was analysed in genome-wide association study: "coronary heart disease". Find the most appropriate EFO term for this trait from the list below. I do not expect an exact match, but getting something that is conceptually close will suffice:

# - coronary artery disease
# - coronary atherosclerosis
# - coronary thrombosis
# - renal artery disease
# - cardiovascular disease
# - congenital heart disease
# - congestive heart failure
# - Congestive heart failure
# - hypertensive heart disease
# - dilated cardiomyopathy
# - myocardial ischemia
# - heart disease

# When you find an EFO term that is conceptually close, make sure to return the exact efo term. Return your answer in json format with the format {"trait": "<original trait>", "efo": "<efo term>", "confidence":<score>}, where the "confidence" field represents on a scale of 1-5 how closely the trait matches, where 1 is very loose and 5 is a perfect match.'


traits <- unique(a$trait)

run_prompt(a, traits[1])

l <- list()
for(i in 1:length(traits)) {
    message(i)
    tr <- traits[i]
    l[[i]] <- try(run_prompt(a, tr, model="deepseek-r1:1.5b"))
    if(i %% 100 == 0) {
        saveRDS(l, here("manual-mapping", "bio-bert", paste0("deepseek-r1-7b_", i, ".rds")))
    }    
}

l <- a 
library(dplyr)
ld <- lapply(l, \(x) {
    tryCatch({
        as_tibble(x) %>% mutate(confidence = as.numeric(confidence))
    }, error = function(e) {
        return(NULL)
    })
}) %>% bind_rows()

ld 


