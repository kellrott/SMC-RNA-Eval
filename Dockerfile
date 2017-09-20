FROM python:2.7

RUN pip install cwltool==1.0.20161007181528 schema-salad==1.18.20161005190847
RUN apt-get install -y curl
RUN curl -sSL https://get.docker.com/ | sh
