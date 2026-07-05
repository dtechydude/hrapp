from django.contrib import admin


class ActiveListFilter(admin.SimpleListFilter):
    title = "Active"
    parameter_name = "is_active"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Active"),
            ("no", "Inactive"),
        )

    def queryset(self, request, queryset):

        if self.value() == "yes":
            return queryset.filter(is_active=True)

        if self.value() == "no":
            return queryset.filter(is_active=False)

        return queryset


class PaymentStatusFilter(admin.SimpleListFilter):
    title = "Payment Status"
    parameter_name = "payment_status"

    def lookups(self, request, model_admin):

        return (
            ("Pending", "Pending"),
            ("Paid", "Paid"),
            ("Cancelled", "Cancelled"),
        )

    def queryset(self, request, queryset):

        if self.value():
            return queryset.filter(payment_status=self.value())

        return queryset