SELECT
    SCHEMA_NAME(o.schema_id) AS [SchemaName],
    o.name AS [ViewName],
    c.column_id AS [ColumnID],
    c.name AS [ColumnName],
    t.name AS [DataType],
    c.max_length AS [MaxLength],
    c.precision AS [Precision],
    c.scale AS [Scale],
    c.is_nullable AS [IsNullable]
FROM
    sys.objects AS o
    INNER JOIN sys.columns AS c ON o.object_id = c.object_id
    INNER JOIN sys.types AS t ON c.user_type_id = t.user_type_id
WHERE
    o.type = 'V'  -- 'V' indicates a View
ORDER BY
    [SchemaName],
    [ViewName],
    c.column_id;
