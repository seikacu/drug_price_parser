FROM ubuntu:latest
LABEL authors="seikacu"

ENTRYPOINT ["top", "-b"]