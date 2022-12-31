import os
from datetime import datetime

import pandas as pd
import pythoncom
from dateutil.tz import *

import general_functions
import sendRequest


def da_calculation(manager, session, desktop, start_time, end_time, date_excel1, date_excel2, system_list,
                   system_information, asset_class_info, chosen_account, update_bar):
    pythoncom.CoInitialize()
    local = tzlocal()  # This contains the local timezone
    current_time = datetime.now().replace(tzinfo=local)
    current_time = format(current_time, '%m-%d %I.%M %p')
    dirname = desktop + '\\' + chosen_account + ' ' + current_time + '\\'
    os.mkdir(dirname)
    # Getting filters so we can use them for setting the asset class filter in the system
    for a in range(0, len(system_list)):
        overall_average = []
        asset_class = []
        no_zero = []
        contains_zero = []
        last_measurement = []
        DA_ids_nav = []
        asset_class_per_value = []
        data_avg_values = []
        system_name = system_list[a]
        system_ids = system_information[system_information['Name'] == system_name]['Id'].reset_index(drop=True)
        for i in range(0, len(asset_class_info)):
            avg_values = []
            filter_id = asset_class_info['Filter Id'][i]
            asset_class.append(asset_class_info['Asset Class'][i])
            for ii in range(0, len(system_ids)):
                system_id = system_ids[ii]
                DA_list = general_functions.filtered_indicator_data(session, filter_id, system_id)
                for nn in range(0, len(DA_list['IndicatorSubsetModels'])):
                    DA_id = DA_list['IndicatorSubsetModels'][nn]['Id']
                    DA_ids_nav.append(DA_list['IndicatorSubsetModels'][nn]['NavigationFullName'])
                    asset_class_per_value.append(asset_class_info['Asset Class'][i])
                    payload = {'StartDate': start_time, 'EndDate': end_time, 'Type': '2',
                               'IndicatorIds': DA_id, 'StartIndex': 0, 'PageSize': 1}
                    r_indicator_value = sendRequest.post(session,
                                                         api='/api2/groups/{}/alerts/indicators/values'.format(system_id),
                                                         data=payload)
                    data_value = r_indicator_value.json()
                    try:
                        last_measurement.append(data_value['RowValues'][0]['LastMeasurementTime'][:19].replace('T', ' '))
                    except KeyError:
                        last_measurement.append('NA')
                    if data_value['RowValues'][0]['Value'] == '--' or data_value['RowValues'][0]['Value'] == '0':
                        no_zero.append(False)
                        avg_values.append(0)
                        data_avg_values.append(0)
                    else:
                        no_zero.append(True)
                        avg_values.append(float(data_value['RowValues'][0]['Value']))
                        data_avg_values.append(float(data_value['RowValues'][0]['Value']))
            if False in no_zero:
                contains_zero.append('yes')
            else:
                contains_zero.append('no')
            nonzero_averages = [a for a in avg_values if a > 0]
            try:
                overall_average.append(round(sum(nonzero_averages) / len(nonzero_averages), 2))
            except ZeroDivisionError:
                overall_average.append(0)
        # Sheet
        sheet1 = pd.DataFrame(data=[asset_class, overall_average, contains_zero])
        sheet1 = sheet1.transpose()
        sheet1.columns = ['Asset Class', 'Average Damage Accumulation', 'Has at least one empty data point/zero']
        sheet1.reset_index(drop=True)
        sheet2 = pd.DataFrame(data=[asset_class_per_value, DA_ids_nav, data_avg_values, last_measurement])
        sheet2 = sheet2.transpose()
        sheet2.columns = ['Asset Class', 'Navigation', 'Average Value For Month', 'Last Measurement Time']
        sheet2.reset_index(drop=True)
        if '/' in system_name:
            system_name = system_name.replace('/', '-')
        if '\\' in system_name:
            system_name = system_name.replace('\\', '-')
        if ':' in system_name:
            system_name = system_name.replace(':', '-')
        writer = pd.ExcelWriter(dirname + system_name + ' ' + date_excel1 + ' to ' +
                                date_excel2 + '.xlsx', engine='xlsxwriter')
        sheet1.to_excel(writer, sheet_name='Results')
        sheet2.to_excel(writer, sheet_name='Data')
        writer.close()
        update_bar()
