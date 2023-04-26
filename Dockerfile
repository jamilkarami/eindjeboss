FROM python:3.11

# UPDATE INDICES AND INSTALL REQUIRED PACKAGES
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install tesseract-ocr

# PREPARE DEFAULT FILES
WORKDIR /home/eindjeboss
COPY default_files/* /eindjeboss_files

# INITIALIZE EINDJEBOSS
WORKDIR /home/eindjeboss
COPY requirements.txt /home/eindjeboss/
RUN pip install -r requirements.txt
COPY . /home/eindjeboss
CMD python bot.py