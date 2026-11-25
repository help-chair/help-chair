# Jenkins de Help Chair (issue #85). Configuración como código: plugins.txt + casc.yaml.
FROM jenkins/jenkins:2.580.2-lts-jdk21

# Herramientas que necesitan los Jenkinsfile de los servicios (make lint test)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends make \
 && rm -rf /var/lib/apt/lists/*
# uv instala el Python 3.12 que exigen los servicios (.python-version / uv.lock)
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /usr/local/bin/
USER jenkins

# Sin asistente web inicial: todo se configura desde casc.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false" \
    CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /usr/share/jenkins/casc.yaml
