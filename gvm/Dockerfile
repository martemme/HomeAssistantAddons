# Use official GVM image
FROM netizensoc/gvm-scanner:latest

LABEL io.hass.name="GVM Scanner"
LABEL io.hass.description="un a GVM (OpenVAS) scanner as a Home Assistant add-on."
LABEL io.hass.arch="amd64|aarch64"
LABEL io.hass.type="addon"
LABEL io.hass.version="0.0.2-beta"

# Set timezone
ENV TZ=Europe/Rome

# Install jq for parsing config
RUN apt-get update && apt-get install -y jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the entrypoint script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose default GVM Web UI port
EXPOSE 9392

# Optionally persist data
VOLUME [ "/data" ]

# Set entrypoint
CMD [ "/run.sh" ]
