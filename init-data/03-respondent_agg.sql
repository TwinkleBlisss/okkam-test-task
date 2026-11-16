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
