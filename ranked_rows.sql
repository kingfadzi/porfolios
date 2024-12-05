WITH RankedRows AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY lob ORDER BY commit_count DESC) AS rn
    FROM table
)
SELECT *
FROM RankedRows
WHERE rn = 1;
