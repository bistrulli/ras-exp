FROM ubuntu:21.04 AS build
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#install all dependecy
RUN apt-get update -y
RUN apt-get install openjdk-15-jdk -y
RUN apt-get install maven -y
RUN apt-get install git -y
RUN apt-get install python -y
RUN apt-get install pip -y
RUN apt-get install sudo -y
RUN apt-get install openssh-server -y
RUN apt-get install libevent-dev -y

RUN pip install numpy scipy matplotlib tqdm cgroupspy docker pymemcache psutil

#download memcached
RUN wget https://memcached.org/files/memcached-1.6.12.tar.gz
RUN tar -xvf memcached-1.6.12.tar.gz

WORKDIR /memcached-1.6.12

RUN ./configure
RUN make
RUN make install

WORKDIR /

#download code
RUN git clone --branch poli https://github.com/bistrulli/AdaptiveHttpServer.git
RUN git clone https://github.com/bistrulli/ras-exp.git

WORKDIR /AdaptiveHttpServer

RUN mvn clean install

WORKDIR /ras-exp/ras_app/

RUN mvn clean package

WORKDIR /ras-exp/ras_app/controller

CMD ["/bin/bash"]
