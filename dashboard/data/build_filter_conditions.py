# build_filter_conditions.py

def build_filter_conditions(filters, alias=None):

    if not filters:
        return None, {}

    text_search_fields = {"app_id", "all_languages"}
    conditions = []
    param_dict = {}
    placeholder_counter = 1

    for field, values in filters.items():
        if not values:
            continue

        col = f"{alias}.{field}" if alias else field

        # For text-search fields -> LIKE '%value%'
        if field in text_search_fields:
            or_clauses = []
            for val in values:
                placeholder = f"p{placeholder_counter}"
                placeholder_counter += 1
                param_dict[placeholder] = f"%{val}%"
                or_clauses.append(f"{col} LIKE :{placeholder}")
            if or_clauses:
                conditions.append("(" + " OR ".join(or_clauses) + ")")
        else:
            # For other fields -> IN (:pX, :pY, ...)
            placeholders = []
            for val in values:
                placeholder = f"p{placeholder_counter}"
                placeholder_counter += 1
                param_dict[placeholder] = val
                placeholders.append(f":{placeholder}")
            if placeholders:
                conditions.append(f"{col} IN ({', '.join(placeholders)})")

    if not conditions:
        return None, {}

    condition_string = " AND ".join(conditions)
    return condition_string, param_dict



def build_filter_conditions_with_alias(filters, alias):
    if not alias:
        raise ValueError("Alias must be specified for this method.")

    conditions = []
    for field, values in filters.items():
        if values:
            formatted_values = ",".join([f"'{value}'" for value in values])
            conditions.append(f"{alias}.{field} IN ({formatted_values})")
    return " AND ".join(conditions) if conditions else None

def build_filter_conditions_with_wildcards(filters, alias=None):

    wildcard_fields = ["app_id", "name"]  # Add other fields as needed

    if alias is None:
        alias = ""  # Default to no alias
    else:
        alias += "."  # Add alias with a dot for table.field formatting

    conditions = []
    for field, values in filters.items():
        if values:
            if field in wildcard_fields:
                # Create wildcard conditions using LIKE
                like_conditions = [f"{alias}{field} LIKE '%{value}%'" for value in values]
                conditions.append(f"({' OR '.join(like_conditions)})")
            else:
                # Create standard IN conditions
                formatted_values = ",".join([f"'{value}'" for value in values])
                conditions.append(f"{alias}{field} IN ({formatted_values})")

    return " AND ".join(conditions) if conditions else None
