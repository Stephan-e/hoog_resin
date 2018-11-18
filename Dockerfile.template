#Get the latest armv7 base image from
#https://registry.hub.docker.com/u/resin/armv7hf-debian/

# base image
#============
# for deployment to RPi2 via Resin.io
# FROM resin/armv7hf-debian:latest	


FROM resin/%%RESIN_MACHINE_NAME%%-debian

ENV INITSYSTEM on

ENV READTHEDOCS True

# install python3
#================
RUN apt-get update && apt-get install -yq --no-install-recommends \
		python3 \
		python3-dev \
		python3-dbus \
		build-essential \
		libssl-dev \
		libffi-dev\
		curl \
		redis-server \
		nano \
		git \
		python3-pip \
		fswebcam \
		cron 

	# && apt-get clean \
    # && rm -rf /var/lib/apt/lists/*
	# && rm -rf /var/lib/apt/lists/* \
	# cd /tmp/ && git clone https://github.com/adafruit/Adafruit_Python_DHT.git && \
    # cd Adafruit_Python_DHT && python3 setup.py install && \
	# apt-get install git-core build-essential python3-dev python3-pip && \
	# apt-get -y autoremove && apt-get clean && rm -rf /tmp/*

# create venv
#===================================
# --without-pip and curl necessary because somee Debian/Ubuntu versions
# run broken versions of Python - http://askubuntu.com/questions/488529/
RUN python3 -m venv --without-pip venv \
  && curl --insecure https://bootstrap.pypa.io/get-pip.py | /venv/bin/python

# copy our python source into container
#======================================
COPY src/ /app

# RUN apt-get update && apt-get upgrade
# RUN apt-get install python3-pip
# RUN python3 -m pip install --upgrade pip setuptools wheel
# RUN apt-get install git

# install dependencies
#===================
RUN /venv/bin/pip install -r /app/requirements.txt 


# WORKDIR /app

# RUN curl https://api.github.com/repos/resin-io/resin-wifi-connect/releases/latest -s \
#    | grep -hoP 'browser_download_url": "\K.*%%RESIN_ARCH%%\.tar\.gz' \
#    | xargs -n1 curl -Ls \
#    | tar -xvz -C /app

# COPY scripts/start.sh .

# CMD ["bash", "start.sh"]


#run the app when the container starts
#======================================s
CMD ["/venv/bin/honcho", "-f", "/app/Procfile", "start"]

EXPOSE 80
