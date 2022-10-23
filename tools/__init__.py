def get_full_name(first_name: str = None, last_name: str = None):
    """Concat first and last name"""
    return " ".join(filter(None, [first_name, last_name])).strip()
