ARG PYVER
FROM python:${PYVER}-alpine

RUN apk update && \
    apk add --no-cache ca-certificates
RUN pip install --upgrade pip

WORKDIR /usr/src/app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The application itself
COPY . .
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
CMD [ "ruterstop", "--stop-id=6013" ]
