
library("gplots")
z <- read.table(file = 'data/generated/fusion-viz-sim.tsv', sep = '\t', header=TRUE, row.names=1, check.names=FALSE)
n <- as.matrix(z)
#heatmap.2(n, trace="none", dendrogram="none", col=c("white", "gray", "blue"))

#legend("topleft", legend = c("TP", "FP"), col = c("blue", "gray"), lty= 1, lwd = 1)

#heatmap.2(n, trace="none", dendrogram="none", col=c("white", "gray", "blue"), key.xlab=NA, key.ylab=NA, keysize=0.5, key.ytickfun=NA, key.xtickfun=NA, xlab="entries", ylab="fusions", labRow=NA, labCol=colnames(n), srtCol=45)

heatmap.2(n,
  trace="none",
  dendrogram="none",
  col=c("white", "gray", "blue"),
  key.xlab=NA,
  key.ylab=NA,
  keysize=0.5,
  key.ytickfun=NA,
  xlab="entries",
  ylab="fusions",
  labRow=NA,
  labCol=colnames(z),
  srtCol=60,
  main="Fusions by entries",
  ColSideColors=c(rep("red", ncol(n))),
  key=FALSE,
  Colv=FALSE)
