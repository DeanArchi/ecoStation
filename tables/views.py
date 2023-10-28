from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db import connection


@login_required
def select_data(request):
    tables = ['Information about the stations', 'Station measurements', 'Air quality parameters']
    reports = ['List of connected stations', 'Station measurement results for the time period']
    with connection.cursor() as cursor:
        cursor.execute('SELECT DISTINCT _Name FROM Station;')
        stations = [row[0] for row in cursor.fetchall()]

    selected_table_name = request.POST.get('selected_table')
    selected_report_name = request.POST.get('selected_report')

    if request.method == 'POST':
        station_address = request.POST.get("station_address")
        show_filter_form = False
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
            match selected_report_name:
                case 'List of connected stations':
                    show_filter_form = True
                    cursor.execute('''
                        SELECT st._Name AS "Station address",
                               (
                                   SELECT MIN(me._Time)
                                   FROM Measurment AS me
                                   WHERE me.ID_Station = st.ID_Station
                               ) AS "Connected from",
                               (
                                   SELECT ARRAY_AGG(DISTINCT  mu.Title)
                                   FROM Measurment AS me
                                   JOIN Measured_Unit AS mu ON me.ID_Measured_Unit = mu.ID_Measured_Unit
                                   WHERE me.ID_Station = st.ID_Station
                               ) AS "Air parameters"
                        FROM Station AS st
                        WHERE st._Name = %s
                    ''', [station_address])
                    data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return render(request, 'account/select_table.html', {
            'data': data,
            'columns': columns,
            'tables': tables,
            'reports': reports,
            'stations': stations,
            'show_filter_form': show_filter_form
        })
    else:
        return render(request, 'account/select_table.html', {
            'tables': tables,
            'reports': reports,
            'stations': stations,
        })
