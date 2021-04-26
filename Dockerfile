FROM python:3.6-slim-buster
RUN apt-get -y update && apt-get install -y sqlite3 libsqlite3-dev
COPY ./requirements.txt /app/requirements.txt
COPY ./4.py /app/4.py
COPY ./templates /app/templates

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN python -m spacy download en_core_web_sm
CMD ["python", "4.py"]
