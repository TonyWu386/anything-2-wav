FROM centos:7
WORKDIR /staging
RUN yum -y install centos-release-scl && yum -y install file git rh-python36
RUN /opt/rh/rh-python36/root/usr/bin/pip3.6 install wave pycryptodome
RUN git clone "https://github.com/TonyWu386/anything-2-wav.git"
RUN (echo "#! /opt/rh/rh-python36/root/bin/python3.6"; cat /staging/anything-2-wav/src/anything2wav.py) > /usr/bin/anything2wav
RUN chmod 555 /usr/bin/anything2wav
RUN rm -r /staging/anything-2-wav
