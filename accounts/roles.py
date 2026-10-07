

ADMIN, NORMAL, LIMITED = "admin", "normal", "limited"
LIMITED_REGION_IDS = [86118093, 86696489, 88186467]

def get_role(user):
    return user.groups.values_list("name", flat=True).first()