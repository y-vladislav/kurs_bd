import tkinter as tk
from tkinter import ttk, simpledialog
import pymysql

# Подключение к базе данных
db_config = {
    'host': '172.17.0.2',
    'user': 'root',
    'password': '123456',
    'database': 'book',
}
sort_order = {}
current_sort = {"table_name": None, "column": None, "direction": None}

connection = pymysql.connect(**db_config)
cursor = connection.cursor()

# Создание главного окна
root = tk.Tk()
root.title("Таблицы в базе данных")

# Функция для вывода данных из таблицы
def display_table(table_name):
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [column[0] for column in cursor.fetchall()]

    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()

    # Создание подокна для отображения данных
    table_window = tk.Toplevel(root)
    table_window.title(f"Таблица: {table_name}")

    # Создание и настройка Treeview для отображения данных
    tree = ttk.Treeview(table_window, columns=columns, show="headings")
    for column in columns:
        tree.heading(column, text=column, command=lambda c=column: sort_table(tree, table_name, c))
        tree.column(column, width=190)

    # Заполнение Treeview данными
    data_sorted = sort_data(data, table_name)
    for row in data_sorted:
        tree.insert("", "end", values=row)

    tree.pack()

def sort_table(tree, table_name, column):
    
    global current_sort

    current_column = current_sort.get("column")
    current_direction = current_sort.get("direction")

    if current_column == column:
        # Изменение направления сортировки, если уже сортируется по этой колонке
        current_direction = "DESC" if current_direction == "ASC" else "ASC"
    else:
        # Новая сортировка по другой колонке
        current_column = column
        current_direction = "ASC"

    current_sort = {"table_name": table_name, "column": current_column, "direction": current_direction}

    cursor.execute(f"SELECT * FROM {table_name} ORDER BY {column} {current_direction}")
    data = cursor.fetchall()

    # Очистка Treeview и заполнение данными после сортировки
    tree.delete(*tree.get_children())
    for row in data:
        tree.insert("", "end", values=row)

def sort_data(data, table_name):
    current_order = sort_order.get(table_name, {})

    if not current_order:
        return data

    # Функция для сортировки данных в соответствии с порядком
    def sort_key(row):
        return [row[i] for i, _ in enumerate(row) if columns[i] in current_order]

    columns = [column[0] for column in cursor.description]
    return sorted(data, key=sort_key)

def delete_data():
    selected_items = table_list_tree.selection()

    # Проверка наличия выбранных элементов
    if selected_items:
        selected_item = selected_items[0]
        table_name = table_list_tree.item(selected_item, "values")[0]

        # Получение информации о таблице
        cursor.execute(f"DESCRIBE {table_name}")
        table_info = cursor.fetchall()

        # Нахождение первичного ключа
        primary_key = None
        for column_info in table_info:
            if "PRI" in column_info:
                primary_key = column_info[0]
                break

        # Если первичный ключ найден, выполнить удаление
        if primary_key:
            primary_key_value = simpledialog.askstring("Удаление данных", f"Введите значение первичного ключа для удаления из таблицы {table_name}:")
            
            # Выполнение запроса на удаление данных
            cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key} = %s", (primary_key_value,))
            connection.commit()

            # Закрытие всех дочерних окон
            for child in root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    child.destroy()

            # Обновление отображения таблицы
            display_table(table_name)
        else:
            print("Таблица не содержит первичного ключа.")
    else:
        print("Выберите элемент для удаления.")

# Функция для вставки данных
def insert_data():
    # Получение списка таблиц из базы данных
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    # Создание окна для вставки данных
    insert_window = tk.Toplevel(root)
    insert_window.title("Вставка данных")

    # Создание и настройка Combobox для выбора таблицы
    selected_table = ttk.Combobox(insert_window, values=tables)
    selected_table.set(tables[0])
    selected_table.pack()

    # Функция для вставки данных при нажатии на кнопку
    def insert_data_to_table():
        table_name = selected_table.get()

        cursor.execute(f"DESCRIBE {table_name}")
        columns = [column[0] for column in cursor.fetchall()]

        # Создание окна для ввода данных
        entry_window = tk.Toplevel(insert_window)
        entry_window.title(f"Вставка данных в таблицу: {table_name}")

        # Создание и настройка Entry для ввода данных
        entry_values = {}
        for column in columns:
            tk.Label(entry_window, text=column).pack()
            entry_values[column] = tk.Entry(entry_window)
            entry_values[column].pack()

        # Функция для вставки данных при нажатии на кнопку
        def insert_data_to_table():
            values = [entry_values[column].get() for column in columns]
            cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s']*len(columns))})", values)
            connection.commit()
            entry_window.destroy()
            insert_window.destroy()

        # Создание кнопки для вставки данных
        tk.Button(entry_window, text="Вставить", command=insert_data_to_table).pack()

    # Создание кнопки для продолжения после выбора таблицы
    tk.Button(insert_window, text="Выбрать", command=insert_data_to_table).pack()
def update_data():
    selected_items = table_list_tree.selection()

    if selected_items:
        selected_item = selected_items[0]
        table_name = table_list_tree.item(selected_item, "values")[0]

        cursor.execute(f"DESCRIBE {table_name}")
        table_info = cursor.fetchall()

        primary_key = None
        for column_info in table_info:
            if "PRI" in column_info:
                primary_key = column_info[0]
                break

        if primary_key:
            primary_key_value = simpledialog.askstring("Обновление данных", f"Введите значение первичного ключа для обновления в таблице {table_name}:")

            # Получение текущих значений полей
            cursor.execute(f"SELECT * FROM {table_name} WHERE {primary_key} = %s", (primary_key_value,))
            current_values = cursor.fetchone()

            # Вывод окна для ввода новых значений полей
            entry_window = tk.Toplevel(root)
            entry_window.title(f"Обновление данных в таблице: {table_name}")

            # Создание и настройка Entry для ввода новых значений
            entry_values = {}
            for i, column in enumerate(table_info):
                tk.Label(entry_window, text=column[0]).grid(row=i, column=0)
                entry_values[column[0]] = tk.Entry(entry_window)
                entry_values[column[0]].insert(0, str(current_values[i]))
                entry_values[column[0]].grid(row=i, column=1)

            # Функция для обновления данных при нажатии на кнопку
            def update_data_in_table():
                new_values = [entry_values[column[0]].get() for column in table_info]
                update_query = f"UPDATE {table_name} SET {', '.join([f'{column[0]}=%s' for column in table_info])} WHERE {primary_key} = %s"
                cursor.execute(update_query, (*new_values, primary_key_value))
                connection.commit()
                entry_window.destroy()
                for child in root.winfo_children():
                    if isinstance(child, tk.Toplevel):
                        child.destroy()

                display_table(table_name)

            # Создание кнопки для обновления данных
            tk.Button(entry_window, text="Обновить", command=update_data_in_table).grid(row=len(table_info), columnspan=2)
        else:
            print("Таблица не содержит первичного ключа.")
    else:
        print("Выберите элемент для обновления.")

# Кнопка для вставки данных
insert_button = tk.Button(root, text="Вставить данные", command=insert_data,width=25)
insert_button.pack()
delete_button = tk.Button(root, text="Удалить данные", command=delete_data,width=25)
delete_button.pack()
update_button = tk.Button(root, text="Обновить данные", command=update_data,width=25)
update_button.pack()

# Создание и настройка Treeview для отображения списка таблиц
table_list_tree = ttk.Treeview(root, columns=("Таблицы",), show="headings")
table_list_tree.heading("Таблицы", text="Таблицы")

# Заполнение Treeview данными о таблицах
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
for table in tables:
    table_list_tree.insert("", "end", values=table)

def on_table_select(event):
    selected_item = table_list_tree.selection()[0]
    table_name = table_list_tree.item(selected_item, "values")[0]
    display_table(table_name)
    update_button.config(state="normal")

# Привязка события выбора таблицы
table_list_tree.bind("<ButtonRelease-1>", on_table_select)

table_list_tree.pack()

root.mainloop()

# Закрытие соединения с базой данных
cursor.close()
connection.close()
