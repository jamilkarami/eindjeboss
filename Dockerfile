FROM python:3.10
ENV TZ="Europe/Amsterdam"

# UPDATE INDICES AND INSTALL REQUIRED PACKAGES
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt install -y libgl1-mesa-glx

# INITIALIZE EINDJEBOSS
WORKDIR /home/eindjeboss
COPY requirements.txt /home/eindjeboss/
RUN pip install -r requirements.txt
COPY . /home/eindjeboss
CMD python bot.py