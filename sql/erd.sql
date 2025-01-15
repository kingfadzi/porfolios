SELECT
    o.name AS ViewName,
    c.name AS ColumnName,
    t.name AS DataType,
    c.max_length AS MaxLength,
    c.precision AS [Precision],
    c.scale AS [Scale],
    c.is_nullable AS IsNullable
FROM sys.objects o
    INNER JOIN sys.columns c ON o.object_id = c.object_id
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE o.type = 'V'
  AND o.name LIKE '%mything%'
ORDER BY o.name, c.column_id;
