from enum import Enum

LOGIN_PAGE = "/accounts/login"


class UserRole(str, Enum):
    USER = "user"
    EXTRANET_ADMIN = "extranet_admin"
    SYSTEM_ADMIN = "system_admin"


class PaymentStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
