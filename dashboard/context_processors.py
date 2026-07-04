"""
dashboard/context_processors.py
──────────────────────────────────────────────────────────────────────────────
Corporate Identity Context Processor

PURPOSE
-------
Makes the company's branding available in every template as:

    corporate_info

This is used throughout HRPAMS for:

• ID Cards
• Payslips
• Appointment Letters
• Promotion Letters
• Suspension Letters
• Leave Letters
• Reports
• PDF Documents
• Dashboard Footer
• Email Templates

IDENTITY RESOLUTION
-------------------

The application supports only ONE Corporate Identity.

Resolution order:

    1. Default Corporate Identity
    2. First Corporate Identity
    3. None

Usage in templates:

    {{ corporate_info.name }}
    {{ corporate_info.phone }}
    {{ corporate_info.email }}
    {{ corporate_info.website }}
    {{ corporate_info.full_address }}

    {% if corporate_info.has_logo %}
        <img src="{{ corporate_info.logo.url }}">
    {% endif %}

    {% if corporate_info.has_signature %}
        <img src="{{ corporate_info.signature.url }}">
    {% endif %}

Register in settings.py

TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "dashboard.context_processors.corporate_identity",
            ],
        },
    },
]
──────────────────────────────────────────────────────────────────────────────
"""

import logging

from .models import CorporateIdentity

logger = logging.getLogger(__name__)


def corporate_identity(request):
    """
    Inject the active Corporate Identity into every template.

    Never raises an exception.
    """

    try:
        identity = CorporateIdentity.get_default()

    except Exception as exc:
        logger.warning(
            "Unable to load Corporate Identity: %s",
            exc,
        )
        identity = None

    return {
        "corporate_info": identity,
    }