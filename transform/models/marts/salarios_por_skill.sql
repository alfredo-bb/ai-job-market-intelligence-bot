-- Mart: salarios por skill
-- Responde: ¿qué skills están asociados a ofertas con mejor salario?
WITH skills AS (
    SELECT * FROM {{ ref('stg_skills') }}
),
ofertas AS (
    SELECT * FROM {{ ref('stg_ofertas') }}
)
SELECT
    s.skill,
    s.categoria,
    o.salario,
    COUNT(*)        AS total_ofertas
FROM skills s
JOIN ofertas o ON s.oferta_id = o.id
WHERE o.salario IS NOT NULL  -- solo ofertas que mencionan salario
GROUP BY s.skill, s.categoria, o.salario
ORDER BY s.skill