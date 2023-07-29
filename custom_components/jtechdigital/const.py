"""Constants for J-Tech Digital HDMI Matrix integration."""

from typing import Final

ATTR_MANUFACTURER: Final = "J-Tech Digital"

DOMAIN: Final = "jtechdigital"

CONF_HDMI_STREAM_TOGGLE = "hdmi_stream_toggle"
CONF_CAT_STREAM_TOGGLE = "cat_stream_toggle"
CONF_CEC_SOURCE_TOGGLE = "cec_source_toggle"
CONF_CEC_OUTPUT_TOGGLE = "cec_output_toggle"
CONF_CEC_DELAY_POWER = "cec_delay_power"
CONF_CEC_DELAY_SOURCE = "cec_delay_source"
CONF_CEC_VOLUME_CONTROL = "cec_volume_control"

ERROR_CONNECT_FAILED = "Failed to connect"
ERROR_FETCH_DATA_FAILED = "Failed to fetch data"
ERROR_AUTH_FAILED = "Authentication failed"
ERROR_UNKNOWN = "Unknown error occurred"