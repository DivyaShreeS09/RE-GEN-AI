"""
Device control simulation for action execution (prompt 2.4).

All executions are simulated — no real hardware is connected.
Mode is always "mock"; "live" is never claimed without a real external call.
"""

from datetime import datetime, timezone

_KNOWN_ACTIONS = {
    "W1": {"name": "Install pressure-reduction valve", "device_type": "valve_control"},
    "W2": {"name": "Inspect night-flow pipes", "device_type": "sensor_query"},
    "E1": {"name": "Schedule HVAC/lighting shutdown", "device_type": "building_automation"},
    "E2": {"name": "Smart occupancy-based auto-shutoff", "device_type": "occupancy_sensor"},
}


def execute_action(action_id: str) -> dict:
    """
    Simulate executing a device control action.
    Always returns mode='mock'; no real hardware is contacted.
    """
    action_meta = _KNOWN_ACTIONS.get(action_id)
    if action_meta is None:
        return {
            "action_id": action_id,
            "mode": "mock",
            "status": "unknown_action",
            "message": f"Action '{action_id}' is not registered in the device control registry.",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "simulation_note": "All executions are simulated. No real hardware was contacted.",
        }
    return {
        "action_id": action_id,
        "action_name": action_meta["name"],
        "device_type": action_meta["device_type"],
        "mode": "mock",
        "status": "executed",
        "message": (
            f"[MOCK MODE] Command dispatched to {action_meta['device_type']} "
            f"for action '{action_meta['name']}'."
        ),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "simulation_note": "All executions are simulated. No real hardware was contacted.",
    }
