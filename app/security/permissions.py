def user_has_permission(user_role: str | None, required_role: str = "student") -> bool:
    roles = {"student", "admin", "moderator"}
    if user_role not in roles:
        return required_role == "student"
    if required_role == "admin":
        return user_role == "admin"
    return True
