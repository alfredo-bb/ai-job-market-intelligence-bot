-- Mart: ranking de skills por mercado (españa vs internacional)
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
    COUNT(*)                                        AS total_ofertas,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY o.mercado), 2) AS porcentaje_mercado
FROM skills s
JOIN ofertas o ON s.oferta_id = o.id
GROUP BY o.mercado, s.skill, s.categoria
ORDER BY o.mercado, total_ofertas DESC