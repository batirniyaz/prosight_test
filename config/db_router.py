

class RnacentralRouter:
    app_label = "loci"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return "rnacentral"
        return None

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_migrate(self, db, app_label, **hints):
        if app_label == self.app_label:
            return db == "rnacentral"
        return db == "default"