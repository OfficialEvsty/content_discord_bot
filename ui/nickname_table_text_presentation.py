


def create_nicknames_table(names_flat: []):
    text = f"**Распознанные никнеймы - {len(names_flat)}**\n\n\n"

    tables = create_nickname_tables(names_flat)
    # Вставка text в начало первой таблицы

    return text + f"```{tables}```"


def create_table(names, num_rows=5, num_columns=5):
    # Преобразуем одномерный список имен в двумерный список (таблицу) num_rows x num_columns
    table = [names[i * num_columns:(i + 1) * num_columns] for i in range(num_rows)]

    # Вычисляем максимальную ширину для каждого столбца
    column_widths = [0] * num_columns
    for row in table:
        for i in range(num_columns):
            if i < len(row):
                column_widths[i] = max(column_widths[i], len(row[i]))

    # Формируем строку таблицы
    table_lines = []
    for row in table:
        line = " | ".join(f"{name.ljust(column_widths[i])}" for i, name in enumerate(row))
        table_lines.append(line)
        table_lines.append("-" * (sum(column_widths) + 4 * num_columns - 1))

    return "\n".join(table_lines).strip()


def create_nickname_tables(names):
    num_rows = 5
    num_columns = 5
    table_size = num_rows * num_columns

    # Разделяем имена на блоки по 25 элементов
    tables = [names[i:i + table_size] for i in range(0, len(names), table_size)]

    # Формируем каждую таблицу и объединяем их
    result = []
    for table in tables:
        result.append(create_table(table, num_rows, num_columns))

    return "\n".join(result)