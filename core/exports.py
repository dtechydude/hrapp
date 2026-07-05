"""
core/exports.py

Generic CSV export used across the project (organizations, staff,
deployments today; payroll registers, loan schedules, leave reports
later). Keeping this in one place means every "download list" button
in HRPAMS behaves identically and gets security/perf fixes once.

CSV was chosen over an Excel library (openpyxl/xlsxwriter) for now:
it needs zero extra dependencies, opens fine in Excel/Sheets/Numbers,
and works unmodified on PythonAnywhere's free tier and shared cPanel
hosting. A `export_queryset_as_xlsx()` sibling can be added later
without touching any of the call sites below, since they only deal
with (label, accessor) pairs, not the output format.
"""
from __future__ import annotations

import csv
from typing import Callable, Iterable, Sequence, Union

from django.http import HttpResponse

FieldAccessor = Union[str, Callable[[object], object]]
FieldSpec = Sequence[tuple[str, FieldAccessor]]


def export_queryset_as_csv(
    queryset: Iterable,
    fields: FieldSpec,
    filename: str,
) -> HttpResponse:
    """
    Streams `queryset` to the browser as a CSV attachment.

    `fields` is a list of (header_label, accessor) tuples, where
    accessor is either an attribute name (string) or a
    callable(obj) -> value — use a callable for anything that spans
    a relationship (e.g. `lambda d: d.staff.full_name`) so the caller
    doesn't need a template-only property.

    Callers are responsible for passing an already-filtered,
    select_related()'d queryset — this function doesn't add any
    filtering of its own so it stays reusable across very different
    models.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([label for label, _ in fields])

    for obj in queryset:
        row = []
        for _, accessor in fields:
            value = accessor(obj) if callable(accessor) else getattr(obj, accessor, "")
            row.append("" if value is None else value)
        writer.writerow(row)

    return response