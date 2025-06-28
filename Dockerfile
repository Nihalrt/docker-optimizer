FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y wget
RUN apt-get install -y python3 python3-pip
RUN pip3 install flask

ADD https://example.com/files/big-file.tar.gz /tmp/
ADD . /app

ENV DB_HOST=localhost


USER root

RUN apt-get install -y build-essential
RUN pip3 install pytest

COPY large-file.bin /data/

CMD ["python3", "app.py"]