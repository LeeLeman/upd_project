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


class CancellationPolicy(str, Enum):
    FREE_CANCELLATION = "free_cancellation"
    NO_CANCELLATION = "no_cancellation"


class MealPolicy(str, Enum):
    NO_MEAL = "no_meal"
    BREAKFAST = "breakfast"
    FULLBOARD = "fullboard"
