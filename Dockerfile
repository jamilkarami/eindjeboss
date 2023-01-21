FROM python:3.10

# UPDATE INDICES AND INSTALL REQUIRED PACKAGES
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install tesseract-ocr

# INITIALIZE EINDJEBOSS
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python bot.py