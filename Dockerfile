FROM ubuntu:latest

FROM python:3.11 as base

WORKDIR /usr/src/app

COPY . ./

RUN pip install -r ./requirements.txt

CMD ["python", "./main.py"]