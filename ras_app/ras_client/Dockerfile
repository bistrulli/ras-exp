FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y

#download code
RUN git clone https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone https://github.com/bistrulli/ras-exp.git

WORKDIR /AdaptiveHttpServer

RUN mvn package
RUN mvn install

WORKDIR /ras-exp/ras_app/

RUN mvn package

WORKDIR /ras-exp/ras_app/ras_client/target



