from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.db import connection


@login_required
def select_table(request):
    tables = ['Information about the stations', 'Station measurements', 'Air quality parameters']
    if request.method == 'POST':
        selected_table_name = request.POST.get('selected_table')
        with connection.cursor() as cursor:
            match selected_table_name:
                case 'Information about the stations':
                    cursor.execute(f'''
                        SELECT st._name as "Station address", 
                               st.city as "City", 
                               st.status as "Station status", 
                               st.id_saveecobot as "SaveEcoBot ID", 
                               st.coordinates as "Station coordinates"
                        FROM station as st
                        LEFT JOIN mqtt_server as ms ON st.id_server = ms.id_server
                    ''')
                    data = cursor.fetchall()
                case 'Station measurements':
                    cursor.execute(f'''
                        SELECT st._name as "Station address",
                               me._time as "Time",
                               mu.title as "Title",
                               me._value as "Value",
--                             COALESCE is used to select the "designation" value from the subquery or "Unknown" if the 
--                             "designation" value is missing
                               COALESCE(ct.designation, 'Unknown') as "Designation"
                        FROM measurment as me
                        JOIN station as st ON st.id_station = me.id_station
                        JOIN measured_unit as mu ON me.id_measured_unit = mu.id_measured_unit
                        LEFT JOIN (
                            SELECT
                                ov.id_measured_unit,
                                ct.designation,
                                ov.bottom_border,
                                ov.upper_border
                            FROM category ct
                            JOIN optimal_value ov ON ov.id_category = ct.id_category
                        ) AS ct ON ct.id_measured_unit = me.id_measured_unit 
                        AND me._value >= ct.bottom_border
                        AND (me._value < ct.upper_border OR ct.upper_border IS NULL)
                        ORDER BY st._name
                        LIMIT 100;
                    ''')
                    data = cursor.fetchall()
                case 'Air quality parameters':
                    cursor.execute(f'''
                        SELECT mu.title as "Title",
                               ct.designation as "Designation",
                               mu.unit as "Unit",
                               ov.bottom_border as "Bottom Border",
                               ov.upper_border as "Upper border"
                        FROM optimal_value as ov
                        JOIN measured_unit as mu ON ov.id_measured_unit = mu.id_measured_unit
                        JOIN category as ct ON ov.id_category = ct.id_category
                    ''')
                    data = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        return render(request, 'account/select_table.html', {
            'data': data,
            'columns': columns,
            'tables': tables
        })
    else:
        return render(request, 'account/select_table.html', {'tables': tables})
