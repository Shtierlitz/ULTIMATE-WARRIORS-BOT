FROM python:3.10
ENV PYTHONDONTWRITEBITECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y postgresql gcc python3-dev musl-dev
RUN apt-get install -y vim

RUN pip install --upgrade pip

WORKDIR /app
COPY requirements.txt requirements.txt

RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

RUN chmod 755 .
COPY . /app
