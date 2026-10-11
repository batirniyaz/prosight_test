from django.apps import apps
from django.test.runner import DiscoverRunner


class UnmanagedModelTestRunner(DiscoverRunner):
    """Makes unmanaged models managed for the test run, so their tables get created.

    Works together with MIGRATION_MODULES = {"loci": None} in settings_test:
    for apps without migrations Django creates tables from the current model
    state (syncdb), which is now managed=True.
    """

    def setup_databases(self, **kwargs):
        for model in apps.get_models():
            if not model._meta.managed:
                model._meta.managed = True
        return super().setup_databases(**kwargs)
