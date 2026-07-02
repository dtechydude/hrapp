from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

class StaffManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure only staff users can access HR functions."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser