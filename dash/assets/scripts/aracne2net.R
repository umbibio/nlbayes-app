library(rjson)
library(org.Hs.eg.db)
library(aracne.networks)


# Term:	DNA-binding transcription factor activity
tf.act.ids <- select(org.Hs.eg.db, c("GO:0003700"), "ENTREZID",
                     keytype = "GOALL")$ENTREZID

# Term:	DNA binding
dna.bind.ids <- select(org.Hs.eg.db, c("GO:0003677"), "ENTREZID",
                       keytype = "GOALL")$ENTREZID

# Term:	transcription regulator activity
treg.act.ids <- select(org.Hs.eg.db, c("GO:0140110"), "ENTREZID",
                       keytype = "GOALL")$ENTREZID

# Term:	regulation of DNA-templated transcription
regoft.ids <- select(org.Hs.eg.db, c("GO:0006355"), "ENTREZID",
                     keytype = "GOALL")$ENTREZID


# For NLBayes, we restrict regulators in the networks to transcription
# factors only, leaving out cofactors and signaling pathway related genes.
# We follow a selection process based on that in (Alvarez, et al. 2016).

# Functional characterization of somatic mutations in cancer using
# network-based inference of protein activity
# M J Alvarez, Y Shen, F M Giorgi, A Lachmann, B B Ding, B H Ye and A Califano
# Nature Genetics volume 48, pages 838–847 (2016)
# https://doi.org/10.1038/ng.3593

tf.act.ids <- union(
  tf.act.ids,
  union(
    intersect(dna.bind.ids, treg.act.ids),
    intersect(dna.bind.ids, regoft.ids)
  )
)

filter.regulon.1 <- function(regulon) {
  regulon <- regulon[intersect(tf.act.ids, names(regulon))]

  regulon
}

filter.regulon.2 <- function(regulon) {

  for(reg.id in names(regulon)) {
    # keep only edges with high confidence
    mask <- regulon[[reg.id]][["likelihood"]] > 0.5
    regulon[[reg.id]][["tfmode"]] <- regulon[[reg.id]][["tfmode"]][mask]
    regulon[[reg.id]][["likelihood"]] <- regulon[[reg.id]][["likelihood"]][mask]

    # discretize mode of regulation. Remove sign for edges with low correlation
    mask <- abs(regulon[[reg.id]][["tfmode"]]) < 0.5
    regulon[[reg.id]][["tfmode"]][mask] <- 0
    regulon[[reg.id]][["tfmode"]] <- sign(regulon[[reg.id]][["tfmode"]])
  }

  regulon
}

regulon2network <- function(regulon, keep.zeros=FALSE) {

  # select TFs only
  regulon <- filter.regulon.1(regulon)

  # remove low confidence interaction edges
  regulon <- filter.regulon.2(regulon)

  # transform object structure
  net <- list()
  for(src in names(regulon)) {
    x <- sign(regulon[[src]]$tfmode)
    if(!keep.zeros) x <- x[x!=0]
    net[[src]] <- x
  }

  net
}

for (name in data(package="aracne.networks")$results[, "Item"]){

  # convert regulon
  net <- regulon2network(get(name), keep.zeros = TRUE)

  # save resulting network as a json file
  write(toJSON(net), paste0(name, ".json"))
}
