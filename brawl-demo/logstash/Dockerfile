FROM docker.elastic.co/logstash/logstash:5.6.10

USER root
RUN yum install -y unzip

RUN mkdir -p /tmp/data
ADD  https://github.com/mitre/brawl-public-game-001/raw/master/brawl-public-game-001.zip /tmp/data/
WORKDIR /tmp/data
RUN unzip brawl-public-game-001.zip
RUN chmod -R 755 data/
RUN ls -la /tmp/data

RUN rm -f /usr/share/logstash/pipeline/logstash.conf
ADD pipeline/logstash.conf /usr/share/logstash/pipeline/logstash.conf
RUN mkdir -p /usr/share/logstash/templates
ADD pipeline/sysmon.mapping.json /usr/share/logstash/templates/sysmon.mapping.json

WORKDIR /usr/share/logstash
USER logstash

