FROM ubuntu:latest

LABEL authors="seikacu"

FROM python:3.11 as base

#ENV PYTHONUNBUFFERED 1
#ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/src/app

COPY . ./

#COPY requirements.txt ./
RUN pip install -r requirements.txt
#RUN chmod +x /usr/src/app/main.py

#COPY . ./

ENV PATH=/root/.local:$PATH

CMD [ "python", "-u", "./main.py" ]

#ENTRYPOINT ["top", "-b"]