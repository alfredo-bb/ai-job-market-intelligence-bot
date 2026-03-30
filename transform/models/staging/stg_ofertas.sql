-- Capa Staging: limpia los datos de la tabla raw de ofertas

WITH source AS (
    SELECT * FROM {{ ref('raw_ofertas')}}
)
SELECT
    id,
    fecha_extraccion,
    LOWER(TRIM(puesto))      AS puesto,  -- minúsculas y sin espacios
    LOWER(TRIM(fuente))      AS fuente,
    LOWER(TRIM(ciudad))      AS ciudad,      -- ciudad de la oferta
    LOWER(TRIM(pais))        AS pais,        -- país de la oferta
    LOWER(TRIM(mercado))        AS mercado,     -- españa o internacional
    descripcion,
    salario,
    CASE
        WHEN experiencia_anos < 0 THEN NULL   -- evita valores negativos
        ELSE experiencia_anos
    END                      AS experiencia_anos,
    remoto,
    url
FROM source
WHERE puesto IS NOT NULL     -- elimina filas sin puesto
