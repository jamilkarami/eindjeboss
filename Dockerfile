ARG VERSION=3.10
FROM python:$VERSION

ENV TZ="Europe/Amsterdam"

ARG BOTFOLDER

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR $BOTFOLDER

COPY requirements.txt $BOTFOLDER/
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]