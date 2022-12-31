import json
from datetime import datetime, timedelta

import pandas as pd
import pythoncom
from dateutil.tz import *
from win32com.client import Dispatch

import general_functions
import sendRequest


def heat_map(session, desktop, account_id, system_information, avg_days, update_bar):
    pythoncom.CoInitialize()  # must call this for win32 dispatch to work!!!
    local = tzlocal()  # This contains the local timezone
    utc = tzutc()  # This contains the utc timezone
    current_time = datetime.now().replace(tzinfo=local).astimezone(utc)
    end_time = format(current_time, '%Y-%m-%dT%H:%M:%S.0000+00:00')
    start_time_SS = current_time - timedelta(days=avg_days)
    start_time_SS = format(start_time_SS, '%Y-%m-%dT%H:%M:%S.%f+00:00')
    Location_names = []
    BV_indicator_asset_names = []
    BV_sensorIds = []
    BV_values = []
    BV_last_update = []
    SS_indicator_asset_names_WE = []
    SS_indicator_asset_names_PSR = []
    SS_WE_values = []
    SS_PSR_values = []
    for a in range(0, len(system_information)):
        system_id = system_information['Id'][a]
        system_name = system_information['Name'][a]
        # Battery Voltage
        data_BV = general_functions.filtered_indicator_data(session, '', system_id)
        for ii in range(0, len(data_BV['IndicatorSubsetModels'])):
            Location_names.append(system_name)
            indicator_id = data_BV['IndicatorSubsetModels'][ii]['Id']
            MP_id = data_BV['IndicatorSubsetModels'][ii]['MonitoringPointId']
            r_sensorId = sendRequest.get(session, api='/api2/groups/{}/node'.format(MP_id))
            if r_sensorId.status_code == 204:
                BV_values.append(0)
                BV_last_update.append('never')
                BV_sensorIds.append('not set')
                BV_indicator_asset_names.append(data_BV['IndicatorSubsetModels'][ii]['NavigationFullName'])
                continue
            else:
                end_time_noformat = datetime.now().replace(tzinfo=local).astimezone(utc)
                end_time_BV = format(end_time_noformat, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                start_time_noformat = end_time_noformat - timedelta(weeks=1)
                start_time_BV = format(start_time_noformat, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                data_sensor = json.loads(r_sensorId.text)
                BV_sensorIds.append(data_sensor['SerialNumber'])
                BV_indicator_asset_names.append(data_BV['IndicatorSubsetModels'][ii]['NavigationFullName'])
                payload = {'indicatorId': indicator_id,
                           'begin': start_time_BV,
                           'end': end_time_BV}
                r2 = sendRequest.get(session, api='/api2/indicator/{}/rawdata'.format(indicator_id), data=payload)
                if len(r2.json()['DataPoints']) != 0:
                    converted_date = datetime.fromtimestamp(r2.json()['DataPoints'][-1]['x']/(1e3))\
                                                .strftime('%m-%d-%Y %H:%M:%S')
                    BV_last_update.append(converted_date)
                    BV_values.append(r2.json()['DataPoints'][-1]['y'])
                    continue
                elif len(r2.json()['DataPoints']) == 0:
                    count = 0
                    while 1:
                        if count == 28:
                            BV_last_update.append('never')
                            BV_values.append(0)
                            break
                        else:
                            pass
                        start_time_noformat = start_time_noformat - timedelta(weeks=1)
                        start_time_BV = format(start_time_noformat, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                        end_time_noformat = end_time_noformat - timedelta(weeks=1)
                        end_time_BV = format(end_time_noformat, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                        payload = {'indicatorId': indicator_id,
                                   'begin': start_time_BV,
                                   'end': end_time_BV}
                        r2 = sendRequest.get(session, api='/api2/indicator/{}/rawdata'.format(indicator_id), data=payload)
                        if len(r2.json()['DataPoints']) != 0:
                            converted_date = datetime.fromtimestamp(r2.json()['DataPoints'][-1]['x'] / (1e3)) \
                                .strftime('%m-%d-%Y %H:%M:%S')
                            BV_last_update.append(converted_date)
                            BV_values.append(r2.json()['DataPoints'][-1]['y'])
                            break
                        elif len(r2.json()['DataPoints']) == 0:
                            count = count + 1
                            continue
        # Signal Strength
        r_filters = sendRequest.get(session, api='/api2/accounts/{}/filters?groupId={}'.format(account_id, system_id))
        filter_list = json.loads(r_filters.text)
        for n in range(0, len(filter_list)):
            if 'Signal Strength' == filter_list[n]['Name'] \
                    or '1 Signal Strength' == filter_list[n]['Name']\
                    or 'Signal Strength - Packet Success Rate' == filter_list[n]['Name']:
                filter_id2 = filter_list[n]['Id']
                break
            else:
                pass
        data_SS = general_functions.filtered_indicator_data(session, filter_id2, system_id)
        for ii in range(0, len(data_SS['IndicatorSubsetModels'])):
            indicator_id = data_SS['IndicatorSubsetModels'][ii]['Id']
            MP_id = data_SS['IndicatorSubsetModels'][ii]['MonitoringPointId']
            url_sensorId = '/api2/groups/{}/node'.format(MP_id)
            r_sensorId = sendRequest.get(session, api=url_sensorId)
            if r_sensorId.status_code == 204:
                SS_WE_values.append(0)
                SS_PSR_values.append(0)
                SS_indicator_asset_names_WE.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
                SS_indicator_asset_names_PSR.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
                continue
            else:
                url_indicator_value = '/api2/groups/{}/alerts/indicators/values'.format(system_id)
                payload = {'StartDate': start_time_SS, 'EndDate': end_time, 'Type': '2',
                           'IndicatorIds': indicator_id, 'StartIndex': 0, 'PageSize': 25}
                r_indicator_value = sendRequest.post(session, api=url_indicator_value, data=payload)
                data_value = json.loads(r_indicator_value.text)
                if 'Wireless' in data_SS['IndicatorSubsetModels'][ii]['Name'] and \
                        data_value['RowValues'][0]['Value'] == "--":
                    SS_WE_values.append(0)
                    SS_indicator_asset_names_WE.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
                elif 'Packet' in data_SS['IndicatorSubsetModels'][ii]['Name'] and \
                        data_value['RowValues'][0]['Value'] == "--":
                    SS_PSR_values.append(0)
                    SS_indicator_asset_names_PSR.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
                elif 'Packet' in data_SS['IndicatorSubsetModels'][ii]['Name'] and \
                        data_value['RowValues'][0]['Value'] != "--":
                    SS_PSR_values.append(float(data_value['RowValues'][0]['Value']))
                    SS_indicator_asset_names_PSR.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
                elif 'Wireless' in data_SS['IndicatorSubsetModels'][ii]['Name'] and \
                        data_value['RowValues'][0]['Value'] != "--":
                    SS_WE_values.append(float(data_value['RowValues'][0]['Value']))
                    SS_indicator_asset_names_WE.append(data_SS['IndicatorSubsetModels'][ii]['NavigationFullName'])
        
        if a == len(system_information) - 1:
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == 'Heat Map Data.xlsx':
                    wb.Close(False)
                else:
                    pass
            WE_sheet = pd.DataFrame(data=[SS_indicator_asset_names_WE, SS_WE_values])
            WE_sheet = WE_sheet.transpose()
            WE_sheet.columns = ['Asset Name', 'Value']
            WE_sheet = WE_sheet.reset_index(drop=True)
            PSR_sheet = pd.DataFrame(data=[SS_indicator_asset_names_PSR, SS_PSR_values])
            PSR_sheet = PSR_sheet.transpose()
            PSR_sheet.columns = ['Asset Name', 'Value']
            PSR_sheet = PSR_sheet.reset_index(drop=True)
            master_sheet = pd.DataFrame(
                data=[Location_names, BV_indicator_asset_names, BV_sensorIds, BV_values, [], [], BV_last_update])
            master_sheet = master_sheet.transpose()
            master_sheet.columns = ['Location Names', 'Asset Name', 'Serial Number', 'Battery Voltage',
                                    'Wireless Efficiency', 'Packet Success Rate', 'Last Measurement Time (BV)']
            master_sheet = master_sheet.reset_index(drop=True)
            for i in range(0, len(WE_sheet)):
                for j in range(0, len(master_sheet)):
                    if WE_sheet['Asset Name'][i] == master_sheet['Asset Name'][j]:
                        master_sheet['Wireless Efficiency'][j] = WE_sheet['Value'][i]

            for i in range(0, len(PSR_sheet)):
                for j in range(0, len(master_sheet)):
                    if PSR_sheet['Asset Name'][i] == master_sheet['Asset Name'][j]:
                        master_sheet['Packet Success Rate'][j] = PSR_sheet['Value'][i]
            # Saving sheet to root
            writer = pd.ExcelWriter(desktop + '\\Heat Map Data.xlsx', engine='xlsxwriter')
            master_sheet.to_excel(writer, sheet_name='Results')
            writer.close()
            pythoncom.CoUninitialize()
            update_bar()
        else:
            update_bar()
