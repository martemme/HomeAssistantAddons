# Use Alpine as the base image
FROM alpine:3.18

LABEL io.hass.name="SonarQube"
LABEL io.hass.description="SonarQube Server helps you comply with common code security standards, such as the NIST SSDF, OWASP, CWE, STIG, and CASA."
LABEL io.hass.arch="amd64|aarch64"
LABEL io.hass.type="addon"
LABEL io.hass.version="0.0.4-beta"

# Build parameters
ARG SONARQUBE_VERSION=9.9.6.92038
ENV SONARQUBE_VERSION=${SONARQUBE_VERSION} \
    SONARQUBE_HOME=/opt/sonarqube \
    SONARQUBE_BIN=/opt/sonarqube/bin/linux-x86-64

# Install runtime dependencies (Java 17)
RUN apk add --no-cache \
      openjdk17-jre \
      curl \
      unzip \
      su-exec \
      tzdata

# Create a user with uid/gid 1000
RUN addgroup -S sonarqube -g 1000 \
 && adduser  -S sonarqube -u 1000 -G sonarqube

# Download and extract SonarQube
RUN curl -L "https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-${SONARQUBE_VERSION}.zip" -o /tmp/sonarqube.zip \
 && unzip /tmp/sonarqube.zip -d /opt \
 && mv /opt/sonarqube-${SONARQUBE_VERSION} "${SONARQUBE_HOME}" \
 && rm /tmp/sonarqube.zip \
 && chown -R sonarqube:sonarqube "${SONARQUBE_HOME}"

# Copy the startup script
COPY run.sh /usr/local/bin/run.sh
RUN chmod +x /usr/local/bin/run.sh

# Expose the internal port
EXPOSE 9000

# All setup runs as root; run.sh poi farà su-exec a sonarqube
ENTRYPOINT ["/usr/local/bin/run.sh"]
