"""
payroll/services/salary_calculator.py

Calculates one staff member's base salary breakdown from their
SalaryStructure template. Does NOT save anything to the database —
it only returns calculated values. PayrollEngine (payroll_engine.py)
is responsible for turning this into Payroll + PayrollItem rows, and
for layering StaffDeduction/StaffAllowance/Bonus/Penalty/SalaryAdvance
on top of what this returns.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, TypedDict

from django.core.exceptions import ValidationError

from payroll.models.choices import ComponentCalculation, ComponentNature
from payroll.models.salary_assignment import SalaryAssignment
from payroll.models.salary_structure import SalaryStructureItem

from .formula_evaluator import FormulaError, evaluate_formula

TWO_PLACES = Decimal("0.01")


class CalculatedItem(TypedDict):
    component: object  # SalaryComponent instance
    description: str
    quantity: Decimal
    rate: Decimal
    amount: Decimal


class SalaryCalculationResult(TypedDict):
    staff: object
    salary_assignment: object
    salary_structure: object
    gross_salary: Decimal
    total_earnings: Decimal
    total_deductions: Decimal
    net_salary: Decimal
    items: List[CalculatedItem]


class SalaryCalculator:
    """Calculates the base-structure salary for a single employee."""

    def __init__(self, staff):
        self.staff = staff
        self.assignment: Optional[SalaryAssignment] = None
        self.structure = None
        self.structure_items = None

    def calculate(self) -> SalaryCalculationResult:
        self._load_salary_structure()

        # Running totals of already-calculated amounts, keyed by
        # component code, so later components can reference earlier
        # ones (percentage-of, or a formula like "BASIC * 0.08").
        resolved: Dict[str, Decimal] = {}
        payroll_items: List[CalculatedItem] = []
        earnings = Decimal("0.00")
        deductions = Decimal("0.00")
        gross_so_far = Decimal("0.00")

        for structure_item in self.structure_items:
            component = structure_item.component

            amount = self._calculate_component(structure_item, resolved, gross_so_far)
            amount = amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            resolved[component.code] = amount

            if component.affects_gross:
                gross_so_far += amount

            payroll_items.append(
                CalculatedItem(
                    component=component,
                    description=component.name,
                    quantity=Decimal("1.00"),
                    rate=amount,
                    amount=amount,
                )
            )

            if component.nature == ComponentNature.EARNING:
                earnings += amount
            else:
                deductions += amount

        gross_salary = earnings
        net_salary = gross_salary - deductions

        return SalaryCalculationResult(
            staff=self.staff,
            salary_assignment=self.assignment,
            salary_structure=self.structure,
            gross_salary=gross_salary,
            total_earnings=earnings,
            total_deductions=deductions,
            net_salary=net_salary,
            items=payroll_items,
        )

    def _load_salary_structure(self):
        try:
            self.assignment = (
                SalaryAssignment.objects.select_related("salary_structure")
                .get(staff=self.staff, is_current=True)
            )
        except SalaryAssignment.DoesNotExist as exc:
            raise ValidationError(
                f"{self.staff.full_name} has no current salary assignment — "
                f"cannot run payroll for this staff member."
            ) from exc

        self.structure = self.assignment.salary_structure

        self.structure_items = (
            SalaryStructureItem.objects.select_related("component")
            .filter(salary_structure=self.structure, is_active=True)
            .order_by("component__display_order")
        )

    def _calculate_component(
        self,
        structure_item: SalaryStructureItem,
        resolved: Dict[str, Decimal],
        gross_so_far: Decimal,
    ) -> Decimal:
        component = structure_item.component
        method = component.calculation_method

        if method == ComponentCalculation.FIXED:
            return structure_item.amount or component.default_amount

        if method == ComponentCalculation.PERCENTAGE:
            percentage = structure_item.percentage or component.percentage
            if component.percentage_of_id:
                base_code = component.percentage_of.code
                if base_code not in resolved:
                    raise ValidationError(
                        f"{component.name} is a percentage of "
                        f"{component.percentage_of.name}, which must appear "
                        f"earlier in display order."
                    )
                base = resolved[base_code]
            elif component.apply_on_gross:
                base = gross_so_far
            else:
                raise ValidationError(
                    f"{component.name} is Percentage-based but has no "
                    f"percentage_of component and apply_on_gross is off."
                )
            return base * (percentage / Decimal("100"))

        if method == ComponentCalculation.FORMULA:
            formula = structure_item.formula_override or component.formula
            if not formula:
                raise ValidationError(f"{component.name} has no formula configured.")
            try:
                return evaluate_formula(formula, resolved)
            except FormulaError as exc:
                raise ValidationError(f"{component.name}: {exc}") from exc

        if method == ComponentCalculation.MANUAL:
            # Manual components default to the structure amount; a
            # payroll officer is expected to review/adjust this on the
            # payroll run screen before approval.
            return structure_item.amount or component.default_amount

        if method == ComponentCalculation.SYSTEM:
            # Reserved for statutory calculators (PAYE tax bands, etc.)
            # registered separately — see services/statutory.py.
            return structure_item.amount or component.default_amount

        raise ValidationError(f"Unknown calculation method for {component.name}: {method}")
