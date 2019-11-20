ARG PYVER
FROM python:${PYVER}-alpine

RUN apk update && \
    apk add --no-cache ca-certificates

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    .

ENV PYTHONUNBUFFERED=1
CMD [ "ruterstop", "--stop-id=6013" ]
