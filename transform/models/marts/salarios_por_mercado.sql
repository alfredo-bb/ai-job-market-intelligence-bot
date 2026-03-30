-- Mart: salarios por skill y mercado
WITH skills AS (
    SELECT * FROM {{ ref('stg_skills') }}
),
ofertas AS (
    SELECT * FROM {{ ref('stg_ofertas') }}
)
SELECT
    o.mercado,
    s.skill,
    s.categoria,
    o.salario,
    COUNT(*)        AS total_ofertas
FROM skills s
JOIN ofertas o ON s.oferta_id = o.id
WHERE o.salario IS NOT NULL
GROUP BY o.mercado, s.skill, s.categoria, o.salario
ORDER BY o.mercado, s.skill