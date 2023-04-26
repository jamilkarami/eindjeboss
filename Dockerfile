FROM python:3.11

# UPDATE INDICES AND INSTALL REQUIRED PACKAGES
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install tesseract-ocr

# PREPARE DEFAULT FILES
WORKDIR /bot
COPY default_files/* /eindjeboss_files

# INITIALIZE EINDJEBOSS
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python bot.py