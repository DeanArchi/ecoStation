from urllib.parse import quote_plus, unquote_plus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.db import connection
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from weasyprint import HTML


@login_required
def select_data(request):
    tables = ['Information about the stations', 'Station measurements', 'Air quality parameters']
    reports = ['List of connected stations', 'Station measurement results for the time period']
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT _Name 
            FROM Station
            WHERE status = 'enabled'
        ''')
        stations = [row[0] for row in cursor.fetchall()]

    selected_table_name = request.POST.get('selected_table')
    selected_report_name = request.POST.get('selected_report')

    if request.method == 'POST':
        station_address = request.POST.get("station_address")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        report_1 = False
        report_2 = False
        if not isinstance(station_address, str):
            station_address = str(station_address)
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
                    report_1 = True
                    url = reverse('generate_pdf', kwargs={
                        'station_address': station_address,
                        'start_date': '0',
                        'end_date': '0',
                        'report': 1
                    })
                    cursor.execute('''
                        SELECT st._Name AS "Station address",
                               (
                                   SELECT MIN(me._Time)
                                   FROM Measurment AS me
                                   WHERE me.ID_Station = st.ID_Station
                               ) AS "Connected from",
                               (
                                   SELECT STRING_AGG(DISTINCT mu.Title, ', ')
                                   FROM Measurment AS me
                                   JOIN Measured_Unit AS mu ON me.ID_Measured_Unit = mu.ID_Measured_Unit
                                   WHERE me.ID_Station = st.ID_Station
                               ) AS "Air parameters"
                        FROM Station AS st
                        WHERE st.status = 'enabled'
                    ''')
                    data = cursor.fetchall()
                case 'Station measurement results for the time period':
                    report_2 = True
                    url = reverse('generate_pdf', kwargs={
                        'station_address': station_address,
                        'start_date': start_date,
                        'end_date': end_date,
                        'report': 2
                    })
                    cursor.execute(f'''
                        SELECT st._Name AS "Station address",
                               mu.Title AS "Air parameter",
                               MIN(me._Value) AS "Minimal value",
                               MAX(me._Value) AS "Maximal value",
                               ROUND(AVG(me._Value), 2) AS "Average value"
                        FROM Measurment AS me
                        JOIN Measured_Unit AS mu ON me.ID_Measured_Unit = mu.ID_Measured_Unit
                        JOIN Station AS st ON me.ID_Station = st.ID_Station
                        WHERE st._Name = %s
                        AND me._Time >= %s
                        AND me._Time <= %s
                        GROUP BY st._Name, mu.Title
                    ''', [station_address, start_date, end_date])
                    data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return render(request, 'account/select_table.html', {
            'data': data,
            'columns': columns,
            'tables': tables,
            'reports': reports,
            'stations': stations,
            'report_1': report_1,
            'report_2': report_2,
            'station_address': quote_plus(station_address),
            'start_date': start_date,
            'end_date': end_date,
            'pdf_url': url,
        })
    else:
        return render(request, 'account/select_table.html', {
            'tables': tables,
            'reports': reports,
        })


@login_required
def generate_pdf(request, station_address='', start_date='', end_date='', report=0):
    current_time = timezone.now()
    formatted_date = current_time.strftime('%Y-%m-%d')
    station_address = unquote_plus(station_address)

    with connection.cursor() as cursor:
        match report:
            case 1:
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
                    WHERE st.status = 'enabled'
                ''')
                data = cursor.fetchall()
                template = get_template('pdf/connected_stations.html')
                context = {
                    'data': data,
                    'station_address': station_address,
                    'current_time': current_time,
                }
                filename = f'report_list_of_connected_stations_{formatted_date}.pdf'
            case 2:
                cursor.execute(f'''
                    SELECT st._Name as "Station address",
                           mu.Title AS "Air parameter",
                           MIN(me._Value) AS "Minimal value",
                           MAX(me._Value) AS "Maximal value",
                           ROUND(AVG(me._Value), 2) AS "Average value"
                    FROM Measurment AS me
                    JOIN Measured_Unit AS mu ON me.ID_Measured_Unit = mu.ID_Measured_Unit
                    JOIN Station AS st ON me.ID_Station = st.ID_Station
                    WHERE st._Name = %s
                    AND me._Time >= %s
                    AND me._Time <= %s
                    GROUP BY st._Name, mu.Title
                ''', [station_address, start_date, end_date])
                data = cursor.fetchall()
                template = get_template('pdf/measurement_results.html')
                context = {
                    'data': data,
                    'station_address': station_address,
                    'current_time': current_time,
                    'start_date': start_date,
                    'end_date': end_date
                }
                filename = f'report_measurements_results_{formatted_date}.pdf'

    html = template.render(context)
    pdf = HTML(string=html).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="{filename}"'
    print(f'====="start_date": {start_date}=====')
    print(f'====="end_date": {end_date}=====')
    return response
