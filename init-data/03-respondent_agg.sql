-- Предвычисленная таблица аудиторий.
--
-- age и sex в данных константны на респондента (проверено: ни у одного
-- респондента они не меняются по строкам), поэтому любой валидный фильтр
-- аудиторий — это пер-человек фильтр, и расчёт можно вести по этой
-- компактной таблице (один avg_weight на респондента), а не по сырым
-- строкам statistics.
CREATE TABLE respondent_agg AS
SELECT
    respondent,
    MIN(age)    AS age,
    MIN(sex)    AS sex,
    AVG(weight) AS avg_weight
FROM statistics
GROUP BY respondent;

CREATE INDEX respondent_agg_age_idx ON respondent_agg (age);
CREATE INDEX respondent_agg_sex_idx ON respondent_agg (sex);
