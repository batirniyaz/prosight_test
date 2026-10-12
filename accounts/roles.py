

ADMIN, NORMAL, LIMITED = "admin", "normal", "limited"
ROLES = (ADMIN, NORMAL, LIMITED)
LIMITED_REGION_IDS = [86118093, 86696489, 88186467]

def get_role(user):
    if not hasattr(user, "_role"):
        user._role = user.groups.filter(name__in=ROLES).values_list("name", flat=True).first()
    return user._role
