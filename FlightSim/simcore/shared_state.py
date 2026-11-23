"""
This is the shared state of the sim. Used to pass between files. 

"""

from threading import Lock
import math

# user controls going INTO physics
controls = {
    "roll_cmd": 0.0,            #rad
    "pitch_cmd": 0.0,           #rad
    "yaw_rate_cmd": 0.0,
    "heave_cmd": 0.001  
}
controls_lock = Lock()

# physics state coming OUT to the UI
latest_state = {}
state_lock = Lock()
# ACRON: Store selected speed, heading, altitude, and F/D enable state together.
mcp_targets = {
    "speed_kt": 60.0,
    "heading_deg": 120.0,
    "altitude_ft": 1500.0,
    "fd_enabled": False,
}
mcp_targets_lock = Lock()

# One encoder detent (or on-screen +/- click) changes a target by this amount.
MCP_STEPS = {"speed_kt": 1.0, "heading_deg": 1.0, "altitude_ft": 100.0}

def _normalise_mcp_target(key, value):
    if key not in MCP_STEPS:
        raise KeyError(key)
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("MCP targets must be finite")
    return value % 360.0 if key == "heading_deg" else max(0.0, value)

def set_mcp_target(key, value):
    """Select a value, or sync to the corresponding current aircraft value."""
    value = _normalise_mcp_target(key, value)
    with mcp_targets_lock:
        mcp_targets[key] = value
    return value

def adjust_mcp_target(key, clicks):
    """Apply signed encoder detents: clockwise positive, counter-clockwise negative."""
    if key not in MCP_STEPS:
        raise KeyError(key)
    if not math.isfinite(float(clicks)) or int(clicks) != clicks:
        raise ValueError("Encoder clicks must be whole numbers")
    with mcp_targets_lock:
        value = _normalise_mcp_target(
            key, mcp_targets[key] + int(clicks) * MCP_STEPS[key]
        )
        mcp_targets[key] = value
    return value

def toggle_mcp_fd():
    """Toggle the shared F/D state from a physical button or the UI."""
    with mcp_targets_lock:
        mcp_targets["fd_enabled"] = not mcp_targets["fd_enabled"]
        return mcp_targets["fd_enabled"]
