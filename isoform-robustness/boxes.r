#install.package("ggplot")

d = read.csv("correlations-sampled-with-replacement-17.txt", header=TRUE, sep="\t")

#x = d[d$K == 5]

#box_plot <- ggplot(data, aes_string(x=x, y=y, fill=colorby)) + geom_boxplot(alpha=0.7)
boxplot(correlation~entry,data=d, main="Isoform robustness", 
  	xlab="Entry + Sample", ylab="Correlation")
