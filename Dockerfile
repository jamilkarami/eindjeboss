FROM python:3.8

# UPDATE INDICES AND INSTALL REQUIRED PACKAGES
RUN apt-get -y update
RUN apt-get -y upgrade

# INITIALIZE EINDJEBOSS
WORKDIR /home/eindjeboss
COPY requirements.txt /home/eindjeboss/
RUN pip install -r requirements.txt
COPY . /home/eindjeboss
CMD python bot.py