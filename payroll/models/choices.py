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


class ComponentType(models.TextChoices):

    BASIC = "Basic", "Basic Salary"

    ALLOWANCE = "Allowance", "Allowance"

    DEDUCTION = "Deduction", "Deduction"

    TAX = "Tax", "Tax"

    PENSION = "Pension", "Pension"

    BONUS = "Bonus", "Bonus"

    OVERTIME = "Overtime", "Overtime"

    LOAN = "Loan", "Loan"

    ADVANCE = "Advance", "Salary Advance"

    PENALTY = "Penalty", "Penalty"

    REIMBURSEMENT = "Reimbursement", "Reimbursement"

    OTHER = "Other", "Other"


class ComponentCalculation(models.TextChoices):

    FIXED = "Fixed", "Fixed Amount"

    PERCENTAGE = "Percentage", "Percentage"

    FORMULA = "Formula", "Formula"

    MANUAL = "Manual", "Manual Entry"

    SYSTEM = "System", "Calculated by System"
    

class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = "Bank Transfer", "Bank Transfer"
    CASH = "Cash", "Cash"
    CHEQUE = "Cheque", "Cheque"
    MOBILE_MONEY = "Mobile Money", "Mobile Money"


class PaymentStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    PROCESSING = "Processing", "Processing"
    SUCCESSFUL = "Successful", "Successful"
    FAILED = "Failed", "Failed"
    REVERSED = "Reversed", "Reversed"


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