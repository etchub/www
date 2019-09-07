FROM python:3.7-slim

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY . /www
RUN cd /www/files && \
    git config --global user.email "d@mien.ch" && \
    git config --global user.name "Damien Corpataux"
WORKDIR /

CMD ["python3", "-m", "www"]
