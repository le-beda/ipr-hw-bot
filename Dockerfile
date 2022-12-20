FROM python:3.7.5-slim

EXPOSE 8888

COPY ./ /ipr-bot
WORKDIR /ipr-bot
RUN pip install -r ./requirements.txt
ENV PYTHONPATH .

CMD ["python3","./bot/bot.py"]