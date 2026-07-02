from decimal import Decimal

from django.core.exceptions import ValidationError

from payroll.models.salary_structure import SalaryStructure, SalaryStructureItem

from payroll.choices import ComponentType


class SalaryCalculator:
    """
    Calculates salary for a single employee.

    This service does NOT save anything to the database.

    It only returns calculated values.

    PayrollEngine will later create Payroll
    and PayrollItems from the returned data.
    """

    def __init__(self, staff):

        self.staff = staff

        self.assignment = None

        self.structure = None

        self.items = None

    # ---------------------------------------------------
    # public method
    # ---------------------------------------------------

    def calculate(self):

        self.load_salary_structure()

        earnings = Decimal("0.00")
        deductions = Decimal("0.00")

        payroll_items = []

        for item in self.items:

            amount = self.calculate_component(item)

            payroll_items.append({

                "component": item.salary_component,

                "description": item.description,

                "quantity": Decimal("1.00"),

                "rate": amount,

                "amount": amount,

            })

            if (
                item.salary_component.component_type
                == ComponentType.EARNING
            ):

                earnings += amount

            else:

                deductions += amount

        gross_salary = earnings

        net_salary = gross_salary - deductions

        return {

            "staff": self.staff,

            "salary_structure": self.structure,

            "gross_salary": gross_salary,

            "total_allowances": earnings,

            "total_deductions": deductions,

            "net_salary": net_salary,

            "items": payroll_items,

        }

    # ---------------------------------------------------
    # load structure
    # ---------------------------------------------------

    def load_salary_structure(self):

        self.assignment = (
            SalaryStructure.objects
            .select_related(
                "salary_structure"
            )
            .get(
                staff=self.staff,
                is_active=True
            )
        )

        self.structure = self.assignment.salary_structure

        self.items = (

            SalaryStructureItem.objects

            .select_related(
                "salary_component"
            )

            .filter(
                salary_structure=self.structure,
                is_active=True,
            )

            .order_by(
                "salary_component__display_order"
            )

        )

    # ---------------------------------------------------
    # calculate one component
    # ---------------------------------------------------

    def calculate_component(self, structure_item):

        component = structure_item.salary_component

        if structure_item.amount:

            return structure_item.amount

        return component.default_amount