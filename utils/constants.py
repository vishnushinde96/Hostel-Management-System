ROOM_CAPACITY = 4
VALID_BED_NUMBERS = (1, 2, 3, 4)


class UserRole:
    ADMIN = "admin"
    WARDEN = "warden"
    STUDENT = "student"
    CHOICES = (ADMIN, WARDEN, STUDENT)


class StudentStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    CHOICES = (ACTIVE, INACTIVE, GRADUATED)


class RoomStatus:
    AVAILABLE = "available"
    FULL = "full"
    CHOICES = (AVAILABLE, FULL)


class AllocationStatus:
    ACTIVE = "active"
    VACATED = "vacated"
    CHOICES = (ACTIVE, VACATED)


class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    CHOICES = (PENDING, PAID)


class AttendanceStatus:
    PRESENT = "present"
    ABSENT = "absent"
    LEAVE = "leave"
    CHOICES = (PRESENT, ABSENT, LEAVE)


class ComplaintStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CHOICES = (PENDING, IN_PROGRESS, RESOLVED, REJECTED)


class ComplaintPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CHOICES = (LOW, MEDIUM, HIGH, URGENT)
