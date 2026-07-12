"""Constants for the Enea Outages integration."""

from zoneinfo import ZoneInfo

DOMAIN = "enea_outages"
PLATFORMS = ["sensor", "binary_sensor"]

# Enea Operator always publishes outage times as naive local Poland time, regardless of
# where Home Assistant (or the machine it runs on) is configured. Use this to interpret
# "now" when comparing against Outage.start_time/end_time, instead of HA's or the OS's
# configured time zone.
ENEA_TIME_ZONE = ZoneInfo("Europe/Warsaw")

CONF_REGION = "region"
CONF_STREET = "street"

DEFAULT_REGION = "Poznań"
DEFAULT_PLANNED_SCAN_INTERVAL = 3600  # 1 hour
DEFAULT_UNPLANNED_SCAN_INTERVAL = 600  # 10 minutes

ATTR_OUTAGE_TYPE = "outage_type"
ATTR_DESCRIPTION = "description"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
