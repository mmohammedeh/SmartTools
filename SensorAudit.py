import json
import pythoncom
import pandas as pd
from win32com.client import Dispatch
import general_functions
import sendRequest


def sensor_audit(session, desktop, chosen_account, system_information, update_bar):
    pythoncom.CoInitialize() # must call this for win32 dispatch to work!!!
    sensor_id = []
    nav_name = []
    nav_subsystem = []
    for a in range(0, len(system_information)):
        system_id = system_information['Id'][a]
        system_name = system_information['Name'][a]
        # Battery Voltage
        data_BV = general_functions.filtered_indicator_data(session, '7a05279e-aea9-4540-b111-d728ed0501aa', system_id)
        for ii in range(0, len(data_BV['IndicatorSubsetModels'])):
            MP_id = data_BV['IndicatorSubsetModels'][ii]['MonitoringPointId']
            r_sensorId = sendRequest.get(session, api='/api2/groups/{}/node'.format(MP_id))
            if r_sensorId.status_code == 204:
                sensor_id.append('not set')
                nav_subsystem.append(system_name)
                nav_name.append(data_BV['IndicatorSubsetModels'][ii]['NavigationFullName'])
                continue
            else:
                data_sensor = json.loads(r_sensorId.text)
                sensor_id.append(data_sensor['SerialNumber'])
                nav_subsystem.append(system_name)
                nav_name.append(data_BV['IndicatorSubsetModels'][ii]['NavigationFullName'])
        if a == len(system_information) - 1:
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == 'Sensor and Navigation List.xlsx':
                    wb.Close(False)
                else:
                    pass
            sheet2 = pd.DataFrame(data=[sensor_id, nav_subsystem, nav_name])
            sheet2 = sheet2.transpose()
            sheet2.columns = ['Sensor Serial Number', 'Plant', 'Navigation']
            sheet2.reset_index(drop=True)
            writer = pd.ExcelWriter(desktop + '\\' + chosen_account + ' Sensor and Navigation List.xlsx',
                                    engine='xlsxwriter')
            sheet2.to_excel(writer, sheet_name='Data')
            writer.close()
            pythoncom.CoUninitialize()
            update_bar()
        else:
            update_bar()
