WITH source AS (
    SELECT * FROM {{ ref('raw_skills') }}
)
SELECT
    id,
    oferta_id,
    LOWER(TRIM(skill))          AS skill,
    LOWER(TRIM(categoria))      AS categoria
FROM source
WHERE skill IS NOT NULL