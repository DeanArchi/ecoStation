from django.shortcuts import render
from django.db import connection


def select_table(request):
    tables = ['MQTT_Server', 'Category', 'Measured_Unit', 'Station',
              'Favorite', 'Optimal_Value', 'Measurment', 'MQTT_Unit']
    if request.method == 'POST':
        selected_table_name = request.POST.get('selected_table')
        # Ви можете виконати SQL-запит, щоб отримати дані з вибраної таблиці
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {selected_table_name};')
            data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return render(request, 'select_table.html', {'data': data, 'columns': columns, 'tables': tables})
    else:
        return render(request, 'select_table.html', {'tables': tables})
