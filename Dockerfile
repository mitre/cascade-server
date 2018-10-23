FROM python:2

RUN mkdir -p /opt/cascade-server
WORKDIR /opt/cascade-server
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
COPY docker_defaults.yml conf/defaults.yml

CMD /bin/bash docker_start.sh
