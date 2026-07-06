"""
payroll/models/__init__.py

Django only discovers models that are imported here. Every model
file added to this package MUST be imported below, or it silently
doesn't exist as far as `makemigrations`/`migrate`/the admin/the ORM
are concerned — this was empty before, which is why none of these
models had ever been migrated.

Import order follows each model's dependency chain (a component
before anything that references it), but note this is only for
human readability — Django doesn't actually require it, since each
module does its own explicit relative imports.
"""

from .choices import (
    AdvanceStatus,
    AllowanceType,
    ApprovalLevel,
    ApprovalStatus,
    ComponentCalculation,
    ComponentCategory,
    ComponentNature,
    DeductionFrequency,
    DeductionType,
    PaymentBatchStatus,
    PaymentChannel,
    PaymentMethod,
    PaymentStatus,
    PayrollMonth,
    PayrollStatus,
    RequestStatus,
)

# ── Setup / configuration ──
from .salary_component import SalaryComponent
from .salary_structure import SalaryStructure, SalaryStructureItem
from .salary_assignment import SalaryAssignment, SalaryChangeReason
from .payroll_period import PayrollPeriod
from .bank import StaffBankAccount

# ── Per-staff variable pay inputs (read by the payroll engine) ──
from .deduction import StaffDeduction
from .allowance import StaffAllowance
from .bonus import Bonus
from .penalty import Penalty
from .advance import SalaryAdvance, AdvanceRepayment

# ── Payroll processing ──
from .payroll import Payroll
from .payroll_item import PayrollItem
from .payroll_approval import PayrollApproval
from .payroll_run import PayrollRun
from .payroll_journal import PayrollJournal
from .payslip import Payslip

# ── Payment & bank schedule ──
from .payroll_payment_batch import PayrollPaymentBatch
from .payroll_payment import PayrollPayment
from .bank_schedule import BankSchedule
from .bank_schedule_item import BankScheduleItem

__all__ = [
    "AdvanceStatus",
    "AllowanceType",
    "ApprovalLevel",
    "ApprovalStatus",
    "ComponentCalculation",
    "ComponentCategory",
    "ComponentNature",
    "DeductionFrequency",
    "DeductionType",
    "PaymentBatchStatus",
    "PaymentChannel",
    "PaymentMethod",
    "PaymentStatus",
    "PayrollMonth",
    "PayrollStatus",
    "RequestStatus",
    "SalaryComponent",
    "SalaryStructure",
    "SalaryStructureItem",
    "SalaryAssignment",
    "SalaryChangeReason",
    "PayrollPeriod",
    "StaffBankAccount",
    "StaffDeduction",
    "StaffAllowance",
    "Bonus",
    "Penalty",
    "SalaryAdvance",
    "AdvanceRepayment",
    "Payroll",
    "PayrollItem",
    "PayrollApproval",
    "PayrollRun",
    "PayrollJournal",
    "Payslip",
    "PayrollPaymentBatch",
    "PayrollPayment",
    "BankSchedule",
    "BankScheduleItem",
]
