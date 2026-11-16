"""Константы приложения."""

# Колонки, доступные для фильтрации аудиторий.
ALLOWED_COLUMNS = {'age', 'sex'}

# Длина дробная части ответа
PERCENT_PLACES = 4

# Запрос на суммы avg_weight по обеим аудиториям
PERCENT_QUERY = """
    WITH audience1 AS (
        SELECT respondent, avg_weight FROM respondent_agg WHERE {filter1}
    ),
    audience2 AS (
        SELECT respondent, avg_weight FROM respondent_agg WHERE {filter2}
    )
    SELECT
        COALESCE(SUM(audience1.avg_weight), 0),
        COALESCE(SUM(audience1.avg_weight) FILTER (WHERE audience2.respondent IS NOT NULL), 0)
    FROM audience1
    LEFT JOIN audience2 USING (respondent)
"""
