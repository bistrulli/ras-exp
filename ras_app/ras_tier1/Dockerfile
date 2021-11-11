FROM ubuntu:21.04 AS build

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

WORKDIR /ras-exp/ras_app/ras_tier1/target

EXPOSE 3000

#CMD ["java","-Xmx4G","-jar","tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar",\
#	"--cpuEmu","0","--jedisHost","monitor.3tier","--tier2Host","tier2.3tier"]



