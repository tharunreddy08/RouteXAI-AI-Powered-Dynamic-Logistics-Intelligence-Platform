import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    RIDER = "rider"


class OrderPriority(str, enum.Enum):
    NORMAL = "Normal"
    EXPRESS = "Express"
    EMERGENCY = "Emergency"


class OrderStatus(str, enum.Enum):
    UNASSIGNED = "Unassigned"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DELAYED = "Delayed"
    CANCELLED = "Cancelled"


class OrderSource(str, enum.Enum):
    CSV = "CSV"
    JSON = "JSON"
    MANUAL = "Manual"


class VehicleStatus(str, enum.Enum):
    IDLE = "Idle"
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    OFFLINE = "Offline"


class TrafficMode(str, enum.Enum):
    NORMAL = "Normal"
    HEAVY = "Heavy"
    ACCIDENT = "Accident"


class HardwareEventType(str, enum.Enum):
    BLOCK_DETECTED = "BLOCK_DETECTED"
    BLOCK_CLEARED = "BLOCK_CLEARED"


class HardwareEventStatus(str, enum.Enum):
    ACTIVE = "Active"
    RESOLVED = "Resolved"
