FROM python:3.10

RUN mkdir -p /home/telegram-bot
WORKDIR /home/telegram-bot

RUN apt-get update \
    && apt-get install -y postgresql postgresql-contrib gcc python3-dev musl-dev

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./entrypoint.sh .

COPY . .

ENTRYPOINT ["/home/telegram-bot/entrypoint.sh"]