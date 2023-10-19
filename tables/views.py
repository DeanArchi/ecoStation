from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.db import connection


def select_table(request):
    tables = ['MQTT_Server', 'Measured_Unit', 'Station',
              'Favorite', 'Optimal_Value', 'Measurement', 'MQTT_Unit']
    if request.method == 'POST':
        selected_table_name = request.POST.get('selected_table')
        with connection.cursor() as cursor:
            match selected_table_name:
                case 'MQTT_Server':
                    cursor.execute(f'SELECT * FROM {selected_table_name};')
                    data = cursor.fetchall()
                case 'Measured_Unit':
                    cursor.execute(f'SELECT * FROM {selected_table_name};')
                    data = cursor.fetchall()
                case 'Station':
                    cursor.execute(f'''
                        SELECT st.id_station as " ",
                               st.city as "City", 
                               st._name as "Station address", 
                               st.status as "Station status", 
                               ms.url as "Server url", 
                               st.id_saveecobot as "SaveEcoBot ID", 
                               st.coordinates as "Station coordinates"
                        FROM station as st
                        LEFT JOIN mqtt_server as ms ON st.id_server = ms.id_server
                    ''')
                    data = cursor.fetchall()
                case 'Favorite':
                    cursor.execute(f'''
                        select fv.user_name as "User",
                               st._name as "Station address"
                        from favorite as fv
                        join station as st on st.id_station = fv.id_station
                    ''')
                    data = cursor.fetchall()
                case 'Optimal_Value':
                    cursor.execute(f'''
                        select mu.title as "Title",
                               ct.designation as "Designation",
                               ov.bottom_border as "Bottom Border",
                               ov.upper_border as "Upper Border"
                        from optimal_value as ov
                        join category as ct on ov.id_category = ct.id_category
                        join measured_unit as mu on ov.id_measured_unit = mu.id_measured_unit 
                    ''')
                    data = cursor.fetchall()
                case 'Measurement':
                    cursor.execute(f'''
                        select me.id_measurment as " ",
                               me._time as "Measurement time",
                               me._value as "Measurement value",
                               st._name as "Station address",
                               mu.title as "Title"
                        from measurment as me
                        join station as st on st.id_station = me.id_station
                        join measured_unit as mu on me.id_measured_unit = mu.id_measured_unit 
                        LIMIT 100
                    ''')
                    data = cursor.fetchall()
                case 'MQTT_Unit':
                    cursor.execute(f'''
                        select st._name as "Station address",
                               mu.title as "Title",
                               mq._message as "Message",
                               mq._order as "Order"
                        from mqtt_unit as mq
                        join station as st on st.id_station = mq.id_station
                        join measured_unit as mu on mq.id_measured_unit = mu.id_measured_unit 
                    ''')
                    data = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        return render(request, 'select_table.html', {
            'data': data,
            'columns': columns,
            'tables': tables
        })
    else:
        return render(request, 'select_table.html', {'tables': tables})
