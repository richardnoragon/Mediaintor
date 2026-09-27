FROM ubuntu:26.04
ARG APP_UID=1000
ARG APP_GID=1000
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pyqt6 python3-pyqt6.sip qt6-qpa-plugins qt6-wayland calibre fonts-dejavu-core ca-certificates && rm -rf /var/lib/apt/lists/*
RUN (getent group ${APP_GID} || groupadd -g ${APP_GID} mediainator) && useradd -o -u ${APP_UID} -g ${APP_GID} -M -d /home/mediainator mediainator
COPY candidate.tar.gz /opt/mediainator/candidate.tar.gz
ARG PACKAGE_SHA256
RUN echo "${PACKAGE_SHA256}  /opt/mediainator/candidate.tar.gz" | sha256sum -c - && mkdir /opt/mediainator/installer && tar -xzf /opt/mediainator/candidate.tar.gz -C /opt/mediainator/installer package_install.py
COPY entrypoint.py verify.py /opt/mediainator/
ENV XDG_SESSION_TYPE=wayland HOME=/home/mediainator XDG_CONFIG_HOME=/home/mediainator/.config XDG_DATA_HOME=/home/mediainator/.local/share XDG_CACHE_HOME=/home/mediainator/.cache XDG_RUNTIME_DIR=/tmp/runtime WAYLAND_DISPLAY=wayland-0
USER ${APP_UID}:${APP_GID}
ENTRYPOINT ["/usr/bin/python3", "-I", "-B", "/opt/mediainator/entrypoint.py"]
CMD ["run"]
