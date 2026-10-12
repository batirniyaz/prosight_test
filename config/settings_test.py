from .settings import *  # noqa: F401,F403

SECRET_KEY = "test-only-secret-key-not-for-production-use"

DATABASES["rnacentral"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}

MIGRATION_MODULES = {"loci": None}

TEST_RUNNER = "config.test_runner.UnmanagedModelTestRunner"
