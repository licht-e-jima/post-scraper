FROM python:3.9-slim as builder
WORKDIR /usr/src/app
RUN pip install poetry==1.1.4
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt

FROM python:3.9-alpine
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/requirements.txt .
RUN apk add --no-cache build-base libxml2-dev libxslt-dev\
    && pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt \
    && apk del build-base
COPY scraper .
CMD python main.py
