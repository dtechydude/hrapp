from django.db import models


class PayrollStatus(models.TextChoices):
    DRAFT = "Draft", "Draft"
    PROCESSING = "Processing", "Processing"
    APPROVED = "Approved", "Approved"
    PAID = "Paid", "Paid"
    LOCKED = "Locked", "Locked"
    CANCELLED = "Cancelled", "Cancelled"


class PayrollMonth(models.IntegerChoices):
    JANUARY = 1, "January"
    FEBRUARY = 2, "February"
    MARCH = 3, "March"
    APRIL = 4, "April"
    MAY = 5, "May"
    JUNE = 6, "June"
    JULY = 7, "July"
    AUGUST = 8, "August"
    SEPTEMBER = 9, "September"
    OCTOBER = 10, "October"
    NOVEMBER = 11, "November"
    DECEMBER = 12, "December"


class ComponentNature(models.TextChoices):
    """
    The one thing that actually matters for gross/net arithmetic:
    does this component ADD to pay or SUBTRACT from it. Kept
    separate from ComponentCategory (below) because "what kind of
    thing is this" (Housing vs. PAYE vs. Loan) and "does it add or
    subtract" are two different questions — collapsing them into one
    enum is what caused the original ComponentType/ComponentCategory
    duplication and the undefined `.EARNING` bug.
    """

    EARNING = "Earning", "Earning"
    DEDUCTION = "Deduction", "Deduction"


class ComponentCategory(models.TextChoices):
    """
    The single, consolidated classification for a salary component.
    Replaces the old ComponentType + ComponentCategory pair, which
    listed almost the same values twice under two different names.
    """

    BASIC = "Basic", "Basic Salary"
    ALLOWANCE = "Allowance", "Allowance"
    BONUS = "Bonus", "Bonus"
    OVERTIME = "Overtime", "Overtime"
    REIMBURSEMENT = "Reimbursement", "Reimbursement"

    TAX = "Tax", "Tax"
    PENSION = "Pension", "Pension"
    NHF = "NHF", "National Housing Fund"
    LOAN = "Loan", "Loan Repayment"
    ADVANCE = "Advance", "Salary Advance"
    PENALTY = "Penalty", "Penalty"
    DEDUCTION = "Deduction", "Other Deduction"

    OTHER = "Other", "Other"


class ComponentCalculation(models.TextChoices):
    FIXED = "Fixed", "Fixed Amount"
    PERCENTAGE = "Percentage", "Percentage"
    FORMULA = "Formula", "Formula"
    MANUAL = "Manual", "Manual Entry"
    SYSTEM = "System", "Calculated by System"


class DeductionType(models.TextChoices):
    PAYE = "PAYE", "PAYE Tax"
    PENSION = "Pension", "Pension"
    NHF = "NHF", "National Housing Fund"
    NSITF = "NSITF", "NSITF"
    ITF = "ITF", "Industrial Training Fund"
    LOAN = "Loan", "Loan Repayment"
    ADVANCE = "Advance", "Salary Advance"
    PENALTY = "Penalty", "Penalty"
    COOPERATIVE = "Cooperative", "Cooperative"
    UNION = "Union", "Union Dues"
    OTHER = "Other", "Other"


class AllowanceType(models.TextChoices):
    HOUSING = "Housing", "Housing"
    TRANSPORT = "Transport", "Transport"
    MEDICAL = "Medical", "Medical"
    MEAL = "Meal", "Meal"
    UTILITY = "Utility", "Utility"
    COMMUNICATION = "Communication", "Communication"
    OVERTIME = "Overtime", "Overtime"
    LEAVE = "Leave", "Leave Allowance"
    BONUS = "Bonus", "Bonus"
    SHIFT = "Shift", "Shift Allowance"
    HAZARD = "Hazard", "Hazard Allowance"
    OTHER = "Other", "Other"


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    CASH = "CASH", "Cash"
    CHEQUE = "CHEQUE", "Cheque"
    MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
    POS = "POS", "POS"
    OTHER = "OTHER", "Other"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    PAID = "PAID", "Paid"
    FAILED = "FAILED", "Failed"
    REVERSED = "REVERSED", "Reversed"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentChannel(models.TextChoices):
    MANUAL = "MANUAL", "Manual Payment"
    BANK_API = "BANK_API", "Bank API"
    BULK_UPLOAD = "BULK_UPLOAD", "Bulk Upload"
    IMPORT = "IMPORT", "Imported"


class PaymentBatchStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class ApprovalLevel(models.TextChoices):
    PAYROLL_OFFICER = "PAYROLL_OFFICER", "Payroll Officer"
    HR_MANAGER = "HR_MANAGER", "HR Manager"
    FINANCE_MANAGER = "FINANCE_MANAGER", "Finance Manager"
    MANAGING_DIRECTOR = "MANAGING_DIRECTOR", "Managing Director"


class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class DeductionFrequency(models.TextChoices):
    RECURRING = "Recurring", "Recurring (every payroll)"
    ONE_TIME = "One-Time", "One-Time"


class RequestStatus(models.TextChoices):
    PENDING = "Pending", "Pending Approval"
    APPROVED = "Approved", "Approved"
    REJECTED = "Rejected", "Rejected"
    CANCELLED = "Cancelled", "Cancelled"


class AdvanceStatus(models.TextChoices):
    PENDING = "Pending", "Pending Approval"
    APPROVED = "Approved", "Approved"
    ACTIVE = "Active", "Being Repaid"
    SETTLED = "Settled", "Fully Repaid"
    REJECTED = "Rejected", "Rejected"
    CANCELLED = "Cancelled", "Cancelled"
