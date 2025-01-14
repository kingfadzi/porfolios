def build_filter_conditions(filters):
    """
    Build a dynamic SQL WHERE clause based on filter inputs.

    :param filters: (dict) Dictionary of filter fields and their selected values.
    :return: (str) SQL WHERE clause.
    """
    conditions = []
    for field, values in filters.items():
        if values:  # If there are selected values
            # Format values for SQL IN clause
            formatted_values = ",".join([f"'{value}'" for value in values])
            conditions.append(f"{field} IN ({formatted_values})")

    return " AND ".join(conditions) if conditions else None

def build_filter_conditions_with_alias(filters, alias):
    if not alias:
        raise ValueError("Alias must be specified for this method.")

    conditions = []
    for field, values in filters.items():
        if values:
            formatted_values = ",".join([f"'{value}'" for value in values])
            conditions.append(f"{alias}.{field} IN ({formatted_values})")
    return " AND ".join(conditions) if conditions else None
