FROM python:3.8-alpine

WORKDIR /usr/src/app

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1
CMD [ "sh", "-c", "python -m unittest tests/test_*.py" ]
