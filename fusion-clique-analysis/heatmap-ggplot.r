
library("ggplot2")
library("reshape")

z <- read.table(file = 'data/generated/fusion-viz-sim.tsv', sep = '\t', header=TRUE, row.names=1, check.names=FALSE)

y <- melt(t(z))

ggplot(t, aes(y=reorder(fusion, weight), x=entry)) + geom_tile(aes(fill=factor(value))) + theme(axis.title=element_blank(), axis.ticks=element_blank(), axis.text.y=element_blank(), axis.text.x=element_text(angle=60,hjust=0.5,vjust=0.5)) + scale_fill_manual(values=c("white", "gray", "blue"), labels=c("", "False Positive", "True Positive"), name="Legend")

ggplot(jj,
  aes(
    y=reorder(fusion, count),
    x=reorder(entry.method, method.id)
  )
) + 
geom_tile(aes(fill=factor(value))) + 
theme(
  axis.title=element_blank(),
  axis.ticks=element_blank(),
  axis.text.y=element_blank(),
  axis.text.x=element_text(angle=90,hjust=1,vjust=0.5)
) + 
scale_fill_manual(
  values=c("white", "gray", "blue"),
  labels=c("", "False Positive", "True Positive"),
  name=""
)
