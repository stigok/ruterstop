ARG PYVER
FROM alpine:3.10 AS timezone
RUN apk update && \
    apk add --no-cache tzdata

FROM python:${PYVER}-alpine3.10

RUN apk update && \
    apk add --no-cache ca-certificates
RUN pip install --upgrade pip

# Set timezone to make tests show correct times
COPY --from=timezone /usr/share/zoneinfo/Europe/Brussels /etc/localtime
RUN echo "Europe/Brussels" > /etc/timezone

WORKDIR /usr/src/app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The application itself
COPY . .
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
CMD [ "ruterstop", "--stop-id=6013" ]
