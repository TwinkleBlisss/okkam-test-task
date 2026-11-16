CREATE TABLE respondent_agg AS
SELECT
    respondent,
    MIN(age)    AS age,
    MIN(sex)    AS sex,
    AVG(weight) AS avg_weight
FROM statistics
GROUP BY respondent;