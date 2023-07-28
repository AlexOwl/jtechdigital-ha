from dataclasses import dataclass

@dataclass
class JtechOutputInfo:
    """Dataclass representing information about a J-Tech Digital HDMI Matrix output."""
    source: int
    name: str
    cat_name: str
    connected: bool
    cat_connected: bool
    enabled: bool
    cat_enabled: bool
    scaler: int
    cec_selected: bool

@dataclass
class JtechSourceInfo:
    """Dataclass representing information about a J-Tech Digital HDMI Matrix input source."""
    outputs: list[int]
    name: str
    active: bool
    edid_index: int
    cec_selected: bool