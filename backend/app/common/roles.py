"""
Central role definitions. All role-based access checks must reference these constants.
Never hardcode role strings in business logic — import from here.
"""

# Roles that can manage machines and dispatch operations
DISPATCHER_ROLES: tuple[str, ...] = ("dispatcher", "dev")

# Roles that receive operational notifications (task/machine events)
OPERATIONAL_NOTIFY_ROLES: tuple[str, ...] = ("dispatcher", "admin", "dev")

# Roles that can validate tasks
TASK_VALIDATOR_ROLES: tuple[str, ...] = ("dispatcher", "dev")

# Roles that can confirm task activation
TASK_ACTIVATION_ROLES: tuple[str, ...] = ("dispatcher", "dev")
