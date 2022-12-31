import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pythoncom
from dateutil.tz import *
from numpy import array
from scipy.signal import argrelmax
from win32com.client import Dispatch

import general_functions
import sendRequest


def gather_ov_alarms(session, desktop, my_documents, system_information, update_bar):
    pythoncom.CoInitialize()
    local = tzlocal()  # This contains the local timezone
    utc = tzutc()  # This contains the utc timezone
    for a in range(0, len(system_information)):
        navigation = []
        indicator_ids = []
        MP_ID = []
        current_alarm = []
        current_warning = []
        nav_name = []
        offthreshold = []
        if a == 0:
            current_time = datetime.now().replace(tzinfo=local).astimezone(utc)
            end_time = format(current_time, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            start_time_OV = current_time - timedelta(days=7)
            start_time_OV = format(start_time_OV, '%Y-%m-%dT%H:%M:%S.%f+00:00')
            nav_name2 = []
            current_alarm2 = []
            current_warning2 = []
            nav_asset = []
            nav_ids = []
            nominal_levels = []
            offthreshold_set = []
            offthreshold_value = []
            sensor_id = []
            warnings = []
            alarms = []
        else:
            pass
        group_id = system_information['Id'][a]
        data_OV = general_functions.filtered_indicator_data(session, '', group_id)
        for i in range(0, len(data_OV['IndicatorSubsetModels'])):
            navigation.append(data_OV['IndicatorSubsetModels'][i]['NavigationFullName'])
            indicator_ids.append(data_OV['IndicatorSubsetModels'][i]['Id'])
            current_alarm.append(data_OV['IndicatorSubsetModels'][i]['AlarmDefinitionDto']['HighAlarmValue'])
            current_warning.append(data_OV['IndicatorSubsetModels'][i]['AlarmDefinitionDto']['HighWarnValue'])
            offthreshold.append(data_OV['IndicatorSubsetModels'][i]['AlarmDefinitionDto']['OffThresholdValue'])
            MP_ID.append(data_OV['IndicatorSubsetModels'][i]['MonitoringPointId'])
            if data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 21:
                nav_name.append('Y')
            elif data_OV['IndicatorSubsetModels'][i]['AssignedSensorRoleType'] == 20:
                nav_name.append('X')
            indicator_info = pd.DataFrame(data=[navigation, nav_name, current_warning, current_alarm, offthreshold,
                                                indicator_ids, MP_ID]).transpose()
            indicator_info.columns = ["navigation", "indicator name", "Current Warning", "Current Alarm", "Off Threshold",
                                      "ids", "MP id"]
        for i in range(0, len(indicator_info)):
            r_sensorId = sendRequest.get(session, api='/api2/groups/{}/node'.format(str(indicator_info['MP id'][i])))
            if r_sensorId.status_code == 204:
                nav_asset.append(indicator_info['navigation'][i])
                nav_ids.append(indicator_info['ids'][i])
                nav_name2.append(indicator_info['indicator name'][i])
                current_alarm2.append(indicator_info['Current Alarm'][i])
                current_warning2.append(indicator_info['Current Warning'][i])
                sensor_id.append('Not Set')
                nominal_levels.append(0)
                offthreshold_set.append('N/A')
                offthreshold_value.append('N/A')
                continue
            else:
                data_sensor = json.loads(r_sensorId.text)
            try:
                NodeId = data_sensor["NodeId"]
            except:
                nav_asset.append(indicator_info['navigation'][i])
                nav_ids.append(indicator_info['ids'][i])
                nav_name2.append(indicator_info['indicator name'][i])
                current_alarm2.append(indicator_info['Current Alarm'][i])
                current_warning2.append(indicator_info['Current Warning'][i])
                sensor_id.append('Sensor Not Set')
                nominal_levels.append('Sensor Not Set')
                offthreshold_set.append('Sensor Not Set')
                offthreshold_value.append('Sensor Not Set')
                continue
            if indicator_info['Off Threshold'][i] > 0:
                offthreshold_set.append('yes')
                offthreshold_value.append(indicator_info['Off Threshold'][i])
            else:
                offthreshold_set.append('no')
                offthreshold_value.append(indicator_info['Off Threshold'][i])
            UpdateInterval = int(int(sendRequest.get(session, api='/api2/nodes/{}/settings/UpdateInterval'.format(NodeId))
                                     .json()["CurrentValue"]) / 1000)
            MaxPoints = int((60 / UpdateInterval) * (7 * 24 * 60))
            payload = {'indicatorId': str(indicator_info['ids'][i]),
                       'begin': start_time_OV,
                       'end': end_time}
            r2 = sendRequest.get(session, api='/api2/indicator/{}/rawdata'.format(str(indicator_info['ids'][i])),
                                 params=payload)
            data_list = r2.json()['DataPoints']
            actual = int(len(r2.json()['DataPoints']))
            if actual < 0.08 * MaxPoints:  # change this to vary how much data you want before even setting alarms
                nav_asset.append(indicator_info['navigation'][i])
                nav_ids.append(indicator_info['ids'][i])
                nav_name2.append(indicator_info['indicator name'][i])
                current_alarm2.append(indicator_info['Current Alarm'][i])
                current_warning2.append(indicator_info['Current Warning'][i])
                nominal_levels.append('Not Enough Data')
                sensor_id.append(data_sensor['SerialNumber'])
                continue
            data_array = array([data_list[z]['y'] for z in range(0, len(data_list))])
            data_array = data_array.astype(np.float32, copy=False)
            # taking into account the off threshold
            try:
                data_array = data_array[data_array > indicator_info['Off Threshold'][i]]
            except TypeError:
                pass
            if len(data_array) > 0:
                pre_avg_data = np.nanmean(data_array)
            else:
                nav_asset.append(indicator_info['navigation'][i])
                nav_ids.append(indicator_info['ids'][i])
                nav_name2.append(indicator_info['indicator name'][i])
                current_alarm2.append(indicator_info['Current Alarm'][i])
                current_warning2.append(indicator_info['Current Warning'][i])
                nominal_levels.append('Not Enough Data')
                sensor_id.append(data_sensor['SerialNumber'])
                continue
            # We do not care about the bottom average because the alarms are set based on the peaks
            data_array = data_array[data_array > pre_avg_data]
            maxs = data_array[argrelmax(data_array, order=3)]
            if len(maxs) > 0:
                avg_maxs = np.nanmean(maxs)
            else:
                nav_asset.append(indicator_info['navigation'][i])
                nav_ids.append(indicator_info['ids'][i])
                nav_name2.append(indicator_info['indicator name'][i])
                current_alarm2.append(indicator_info['Current Alarm'][i])
                current_warning2.append(indicator_info['Current Warning'][i])
                nominal_levels.append('Not Enough Data')
                sensor_id.append(data_sensor['SerialNumber'])
                continue
            nav_asset.append(indicator_info['navigation'][i])
            nav_ids.append(indicator_info['ids'][i])
            nav_name2.append(indicator_info['indicator name'][i])
            current_alarm2.append(indicator_info['Current Alarm'][i])
            current_warning2.append(indicator_info['Current Warning'][i])
            nominal_levels.append(avg_maxs)
            sensor_id.append(data_sensor['SerialNumber'])
        if a == len(system_information) - 1:
            for i in nominal_levels:
                try:
                    i = float(i)
                    if i <= float(0.25):
                        warnings.append(i * float(1.6))
                        alarms.append(i * float(2))
                    else:
                        warnings.append(i + float(0.1))
                        alarms.append(i + float(0.2))
                except ValueError:
                    warnings.append('Not Enough Data')
                    alarms.append('Not Enough Data')
            for i in range(0, len(warnings)):
                try:
                    if warnings[i] >= float(0.8):
                        warnings[i] = float(0.8)
                    elif warnings[i] <= float(0.1):
                        warnings[i] = float(0.1)
                except TypeError:
                    pass
            for i in range(0, len(alarms)):
                try:
                    if alarms[i] >= float(1):
                        alarms[i] = float(1)
                    elif alarms[i] <= float(0.2):
                        alarms[i] = float(0.2)
                except TypeError:
                    pass
            alarm_data = pd.DataFrame(data=[nav_asset, nav_ids, nav_name2, sensor_id, current_warning2, current_alarm2,
                                            nominal_levels, warnings, alarms, offthreshold_set, offthreshold_value])
            alarm_data = alarm_data.transpose()
            alarm_data.columns = ['Navigation',
                                  'Indicator Id',
                                  'Indicator Name',
                                  'Sensor Serial Number',
                                  'Current Warning Levels',
                                  'Current Alarm Levels',
                                  'Nominal Levels',
                                  'Warning Levels',
                                  'Alarm Levels',
                                  'Off Threshold Set',
                                  'Off Threshold Value']
            alarm_data = alarm_data.reset_index(drop=True)
            alarm_data = alarm_data[(alarm_data['Nominal Levels'] != 'Not Enough Data') &
                                    (alarm_data['Nominal Levels'] != 'Sensor Not Set')]
            alarm_data_errors = alarm_data[(alarm_data['Nominal Levels'] == 'Not Enough Data') |
                                           (alarm_data['Nominal Levels'] == 'Sensor Not Set')]
            alarm_data_errors = alarm_data_errors.reset_index(drop=True)
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == 'Alarm Levels.xlsx':
                    wb.Close(False)
                elif wb.Name == 'Alarm Levels (Errors).xlsx':
                    wb.Close(False)
                else:
                    pass
            writer = pd.ExcelWriter(my_documents + '\\Smart Tools\\Alarm Levels.xlsx', engine='xlsxwriter')
            alarm_data.to_excel(writer, sheet_name='Results')
            writer.close()
            writer = pd.ExcelWriter(desktop + '\\Alarm Levels (Errors).xlsx', engine='xlsxwriter')
            alarm_data_errors.to_excel(writer, sheet_name='Results')
            writer.close()
            pythoncom.CoUninitialize()
            update_bar()
        else:
            update_bar()


def gather_temp_alarms():
    pass



