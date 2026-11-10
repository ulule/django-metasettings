from django.conf.urls import url  # type: ignore[attr-defined]

from .views import dashboard


urlpatterns = [
    url(
        r"^dashboard/(?:(?P<status>(language|currency)+)/)?$",
        dashboard,
        name="metasettings_dashboard",
    )
]
