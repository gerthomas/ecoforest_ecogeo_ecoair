from datetime import timedelta

DOMAIN = "ecoforest_ecoair_rw"
MANUFACTURER = "Ecoforest"

# 30 seconds: the sensor reads are grouped into a few blocks, and controls refresh straight after a write
POLLING_INTERVAL = timedelta(seconds=30)

# Opt-in switch for the select/number control entities (default off)
CONF_ALLOW_CONTROL = "allow_control"
