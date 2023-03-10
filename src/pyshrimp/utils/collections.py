
def first_not_null(*values, default=None):
    for v in values:
        if v is not None:
            return v

    return default
