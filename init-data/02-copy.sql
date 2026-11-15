COPY statistics(id, date, respondent, sex, age, weight)
FROM '/docker-entrypoint-initdb.d/data.csv'
DELIMITER ';'
CSV HEADER;
