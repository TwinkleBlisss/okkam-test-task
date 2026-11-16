# Колонки, доступные для фильтрации аудиторий.
ALLOWED_COLUMNS = {'age', 'sex'}

# Длина дробная части ответа
PERCENT_PLACES = 4

# Запрос на суммы avg_weight по обеим аудиториям
PERCENT_QUERY = """
    SELECT
        COALESCE(SUM(avg_weight) FILTER (WHERE ({filter1})), 0),
        COALESCE(SUM(avg_weight) FILTER (WHERE ({filter1}) AND ({filter2})), 0)
    FROM respondent_agg
"""
