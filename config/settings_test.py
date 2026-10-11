from .settings import *  # noqa: F401,F403

# The real RNAcentral DB is read-only, so Django can't create a test database there.
# Tests use an in-memory SQLite instead; tables are created by the custom runner.
DATABASES["rnacentral"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}

# Treat `loci` as an app without migrations, so its tables are created from the models.
MIGRATION_MODULES = {"loci": None}

TEST_RUNNER = "config.test_runner.UnmanagedModelTestRunner"
