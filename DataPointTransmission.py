import os
import time
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import pythoncom
from dateutil.tz import *
from win32com.client import Dispatch

import general_functions
import sendRequest


# This is the code for hour-by-hour
def data_point_hourly(session, desktop, start_time, date_excel1, date_excel2, starting_hour,
                      system_information, chosen_account, date_list, date_hourly_list, update_bar):
    pythoncom.CoInitialize()  # must call this for win32 dispatch to work!!!
    system_names = system_information['Name'].drop_duplicates(keep='first', inplace=False).reset_index(drop=True).tolist()
    data_dict = {}
    nan = 'nan'
    writer = pd.ExcelWriter(desktop + '\\' + chosen_account + ' Data Point Comparisons (Hourly) ' + date_excel1 +
                            " to " + date_excel2 + '.xlsx', engine='xlsxwriter')
    end_row = 0
    start_time_unformatted = start_time.replace(hour=starting_hour)
    for days in range(0, len(date_list)):
        start = time.time()
        date_first = date_list[days]
        actual_points_array = pd.DataFrame()
        for h in range(0, len(date_hourly_list)): ## Change this back to date_hourly_list
            system_nav = []
            navigation = []
            nav_name = []
            update_interval = []
            sensorIds = []
            max_points = []
            actual_points = []
            date_first_hourly = date_hourly_list[h]
            start_time_formatted = format(start_time_unformatted, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            date_last = start_time_unformatted + timedelta(hours=1)
            end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            # fetching overall vibration data using known OV filter id
            for a in range(0, len(system_information)):
                system_id = system_information['Id'][a]
                system_name = system_information['Name'][a]
                data_OV = general_functions.filtered_indicator_data(session, '', system_id)
                for i in range(0, len(data_OV['IndicatorSubsetModels'])):
                    # this loop accesses each OV indicator from the call and appends information
                    # Appending descriptive information
                    system_nav.append(system_name)
                    navigation.append(data_OV['IndicatorSubsetModels'][i]['NavigationFullName'])
                    if data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 21:
                        nav_name.append('Y')
                    elif data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 20:
                        nav_name.append('X')
                    # Grab indicator id so we can use it to grab the data points later
                    indicator_id_OV = data_OV['IndicatorSubsetModels'][i]['Id']
                    # We need to check the MP to see if there is even a sensor assigned
                    MP_ID = data_OV['IndicatorSubsetModels'][i][
                        'MonitoringPointId']  # for sensor assignment check and PSR indicator
                    r_sensorId = sendRequest.get(session, api='/api2/groups/{}/node'.format(str(MP_ID)))
                    if r_sensorId.status_code == 204:  # checks if sensor is assigned to MP
                        max_points.append(nan)
                        actual_points.append(nan)
                        update_interval.append(nan)
                        sensorIds.append('not set')
                    elif r_sensorId.status_code == 200:
                        # Fetching sensor id
                        data_sensor = r_sensorId.json()
                        sensorIds.append(data_sensor['SerialNumber'])
                        NodeId = data_sensor["NodeId"]
                        UpdateInterval = int(int(sendRequest.get(session, api='/api2/nodes/{}/settings/UpdateInterval'
                                                                 .format(NodeId)).json()["CurrentValue"]) / 60000)
                        if UpdateInterval > 0:
                            MaxPoints = (24 * 60) / UpdateInterval
                            update_interval.append(UpdateInterval)
                            max_points.append((MaxPoints))
                            payload = {'indicatorId': indicator_id_OV,
                                       'begin': start_time_formatted,
                                       'end': end_time}
                            r2 = sendRequest.get(session, api='/api2/indicator/{}/rawdata'.format(indicator_id_OV),
                                                 data=payload)
                            actual = int(len(r2.json()['DataPoints']))
                            actual_points.append(actual)
                        else:
                            max_points.append(nan)
                            actual_points.append(nan)
                            update_interval.append('error in retrieving')
                            continue
            # Formatting column of hourly points
            hour_df = pd.DataFrame(data=[actual_points])
            hour_df = hour_df.transpose()
            hour_df.columns = ['Actual Points' + ' - ' + date_first_hourly]
            # Appending the columns together one by one
            actual_points_array = pd.concat([actual_points_array, hour_df], axis=1)
            start_time_unformatted = start_time_unformatted + timedelta(hours=1)
        data_point_sheet = pd.DataFrame(data=[system_nav, navigation, nav_name, sensorIds, update_interval, max_points])
        data_point_sheet = data_point_sheet.transpose()
        data_point_sheet.columns = ['System',
                                    'Navigation',
                                    'Indicator Axis',
                                    'Sensor Serial Number',
                                    'Update Interval (Minutes)',
                                    'Max Points']
        data_point_sheet = pd.concat([data_point_sheet, actual_points_array], axis=1)
        data_point_sheet = data_point_sheet[data_point_sheet['Update Interval (Minutes)'] > 0].reset_index(drop=True)
        data_dict[date_first] = data_point_sheet
        if len(date_hourly_list) < 24:
            start_time_unformatted = (start_time_unformatted + timedelta(days=1)).replace(hour=starting_hour)
        else:
            pass
        if days == len(date_list) - 1:
            # system hourly percentage calculation
            date_hourly_list.append("Day's Overall Asset Percentage")
            for system in system_names:
                # we need to start per system since we will create a table for each system
                system_table = pd.DataFrame(columns=date_hourly_list)
                # we also need the day-by-day date so we can calculate the percentage per hour per day
                for d in range(0, len(date_list)):
                    dict_rows_hourly = []
                    successful_list = [] # resets per day
                    day = date_list[d]
                    system_data = data_dict[day][data_dict[day]['System'] == system].reset_index(drop=True)
                    for column in range(0, len(date_hourly_list) - 1):
                        # Going by each column as each hour, we will calculate how many assets successfully connected
                        # more than 50% of the time each day
                        successful_hour = [] # resets per hour
                        for row in range(0, len(system_data)):
                            if system_data['Actual Points' + ' - ' + date_hourly_list[column]].iloc[row] == 'nan':
                                pass
                            elif system_data['Actual Points' + ' - ' + date_hourly_list[column]].iloc[row] > \
                                    system_data['Max Points'].iloc[row] / 2:
                                # successful_hour is for the hour percentage, resets per hour
                                successful_hour.append(1)
                                # successful_list is for the overall asset percentage, it resets per day,
                                successful_list.append(1)
                            else:
                                successful_hour.append(0)
                                successful_list.append(0)
                        dict_rows_hourly.append(round((sum(successful_hour) / len(successful_hour)) * 100, 2))
                    # Constructing the table for each system
                    # average_hourly will be the overall asset percentage per day per system
                    # (makes more sense when you see the table)
                    average_hourly = round(np.sum(successful_list) / len(successful_list) * 100, 2)
                    # Now we need to append this value to the rest of the hourly percentages so it appears at the very
                    # end of the table
                    dict_rows_hourly.append(average_hourly)
                    day_hourly_df = pd.DataFrame(data=[dict_rows_hourly],
                                                 columns=date_hourly_list,
                                                 index=[day])
                    system_table = pd.concat([system_table, day_hourly_df], axis=0)
                system_table.index.name = system
                system_table.to_excel(writer, sheet_name='Percentages', startrow=end_row, startcol=0)
                # We will separate the tables with an empty row to make it easier to read
                # We need "end_row" because it is used for the proceeding arguments as we
                # continue looping through systems
                end_row = end_row + len(system_table) + 1
                row_seperate_df = pd.DataFrame(data=[''], columns=[''], index=[''])
                row_seperate_df.to_excel(writer, sheet_name='Percentages', startrow=end_row, startcol=0)
                end_row = end_row + 1
            # Close any window with the same name in order to save
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == chosen_account + ' Data Point Comparisons (Hourly) ' + date_excel1 + ' to ' + date_excel2 + '.xlsx':
                    wb.Close(False)
                else:
                    pass
            for a in date_list:
                data_dict[a].to_excel(writer, sheet_name=a)
            writer.close()
            pythoncom.CoUninitialize()
            # end = time.time()
            # print(end - start)
            update_bar()
        else:
            update_bar()


# This is the code for day-by-day
def data_point_daily(session, desktop, start_time, date_excel1, date_excel2, system_information,
                     chosen_account, date_list, update_bar):
    pythoncom.CoInitialize()  # must call this for win32 dispatch to work!!!
    system_names = system_information['Name'].drop_duplicates(keep='first', inplace=False).reset_index(drop=True).tolist()
    data_dict = {}
    nan = 'nan'
    start_time_unformatted = start_time
    for days in range(0, len(date_list)):
        system_nav = []
        navigation = []
        nav_name = []
        update_interval = []
        sensorIds = []
        max_points = []
        actual_points = []
        successful_list = []
        dict_rows = []
        date_first = date_list[days]
        start_time_formatted = format(start_time_unformatted, '%Y-%m-%dT%H:%M:%S.0000+00:00')
        date_last = start_time_unformatted + timedelta(days=1)
        end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
        # fetching overall vibration data using known OV filter id
        for a in range(0, len(system_information)):
            system_id = system_information['Id'][a]
            system_name = system_information['Name'][a]
            data_OV = general_functions.filtered_indicator_data(session, '', system_id)
            for i in range(0, len(data_OV['IndicatorSubsetModels'])):
                # this loop accesses each OV indicator from the call and appends information
                # Appending descriptive information
                system_nav.append(system_name)
                navigation.append(data_OV['IndicatorSubsetModels'][i]['NavigationFullName'])
                if data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 21:
                    nav_name.append('Y')
                elif data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 20:
                    nav_name.append('X')
                # Grab indicator id so we can use it to grab the data points later
                indicator_id_OV = data_OV['IndicatorSubsetModels'][i]['Id']
                # We need to check the MP to see if there is even a sensor assigned
                MP_ID = data_OV['IndicatorSubsetModels'][i][
                    'MonitoringPointId']  # for sensor assignment check and PSR indicator
                r_sensorId = sendRequest.get(session, api='/api2/groups/{}/node'.format(str(MP_ID)))
                if r_sensorId.status_code == 204:  # checks if sensor is assigned to MP
                    max_points.append(nan)
                    actual_points.append(nan)
                    update_interval.append(nan)
                    sensorIds.append('not set')
                elif r_sensorId.status_code == 200:
                    # Fetching sensor id
                    data_sensor = r_sensorId.json()
                    sensorIds.append(data_sensor['SerialNumber'])
                    NodeId = data_sensor["NodeId"]
                    UpdateInterval = int(int(sendRequest.get(session, api='/api2/nodes/{}/settings/UpdateInterval'
                                                             .format(NodeId)).json()["CurrentValue"]) / 60000)
                    if UpdateInterval > 0:
                        MaxPoints = (24 * 60)/UpdateInterval
                        update_interval.append(UpdateInterval)
                        max_points.append((MaxPoints))
                        payload = {'indicatorId': indicator_id_OV,
                                   'begin': start_time_formatted,
                                   'end': end_time}
                        r2 = sendRequest.get(session, api='/api2/indicator/{}/rawdata'.format(indicator_id_OV),
                                             data=payload)
                        actual = int(len(r2.json()['DataPoints']))
                        actual_points.append(actual)
                    else:
                        max_points.append(nan)
                        actual_points.append(nan)
                        update_interval.append('error in retrieving')
                        continue
        data_point_sheet = pd.DataFrame(data=[system_nav, navigation, nav_name, sensorIds, update_interval, max_points,
                                        actual_points])
        data_point_sheet = data_point_sheet.transpose()
        data_point_sheet.columns = ['System',
                                    'Navigation',
                                    'Indicator Axis',
                                    'Sensor Serial Number',
                                    'Update Interval (Minutes)',
                                    'Max Points',
                                    'Actual Points']
        data_point_sheet = data_point_sheet.reset_index(drop=True)
        data_dict[date_first] = data_point_sheet
        # system specific percentage calculation
        for system in range(0, len(system_names)):
            successful_list_system = []
            system_data = data_point_sheet[data_point_sheet['System'] == system_names[system]].reset_index(drop=True)
            for row in range(0, len(system_data)):
                if system_data['Actual Points'].iloc[row] == 'nan':
                    pass
                elif system_data['Actual Points'].iloc[row] > system_data['Max Points'].iloc[row]/2:
                    successful_list_system.append(1)
                else:
                    successful_list_system.append(0)
            dict_rows.append(round((np.sum(successful_list_system)/len(successful_list_system)) * 100, 2))
        # overall percentage calculation
        for row in range(0, len(data_point_sheet)):
            if data_point_sheet['Actual Points'][row] == 'nan':
                pass
            elif data_point_sheet['Actual Points'][row] > data_point_sheet['Max Points'][row] / 2:
                successful_list.append(1)
            else:
                successful_list.append(0)
        dict_rows.append(round(np.sum(successful_list) / len(successful_list) * 100, 2))
        day_df = pd.DataFrame(data=[dict_rows])
        day_df = day_df.transpose()
        day_df.columns = [date_first]
        # Appending the columns together one by one
        try:
            main_percentage_df = pd.concat([main_percentage_df, day_df], axis=1)
        except UnboundLocalError:
            main_percentage_df = day_df
        if days == len(date_list) - 1:
            # Close any window with the same name in order to save
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == chosen_account + ' Data Point Comparisons (Daily) ' + date_excel1 + ' to ' + date_excel2 + '.xlsx':
                    wb.Close(False)
                else:
                    pass
            system_names.append("Day's Overall Asset Percentage")
            main_percentage_df.index = system_names
            writer = pd.ExcelWriter(desktop + '\\' + chosen_account + ' Data Point Comparisons (Daily) ' + date_excel1 +
                                    " to " + date_excel2 + '.xlsx', engine='xlsxwriter')
            main_percentage_df.to_excel(writer, sheet_name='Percentages')
            for a in date_list:
                data_dict[a].to_excel(writer, sheet_name=a)
            writer.close()
            pythoncom.CoUninitialize()
            update_bar()
        else:
            start_time_unformatted = start_time_unformatted + timedelta(days=1)
            update_bar()
