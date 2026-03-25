-- Mart: ranking de skills más demandados
-- Responde: ¿qué skills piden más las empresas?
WITH skills AS (
    SELECT * FROM {{ ref('stg_skills') }}
),
ofertas AS (
    SELECT * FROM {{ ref('stg_ofertas') }}
)
SELECT
    s.skill,
    s.categoria,
    COUNT(*)                                    AS total_ofertas,
    -- Porcentaje sobre el total de ofertas
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ofertas), 2) AS porcentaje_ofertas
FROM skills s
JOIN ofertas o ON s.oferta_id = o.id
GROUP BY s.skill, s.categoria
ORDER BY total_ofertas DESC