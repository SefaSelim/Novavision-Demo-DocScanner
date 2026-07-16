
def resolve_option_name(value):
    """
        request.get_param() on a dependentDropdownlist/dropdownlist node may
        return either the raw discriminator string or the full nested option
        object depending on how deep the lookup resolves. This normalizes
        both shapes down to the option's name so callers can branch on it
        without worrying about which shape came back.
    """
    if isinstance(value, dict):
        return value.get("name") or value.get("value")
    return value
