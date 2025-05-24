ARG VERSION=3.13
FROM python:$VERSION

ENV TZ="Europe/Amsterdam"

ARG BOTFOLDER

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends libgl1-mesa-glx curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR $BOTFOLDER

COPY pyproject.toml poetry.lock* $BOTFOLDER/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

COPY . .

CMD ["poetry", "run", "python", "bot.py"]