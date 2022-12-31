import time
from time import gmtime, strftime

import pandas as pd
import pythoncom
from win32com.client import Dispatch

import general_functions
import sendRequest
import system_builder_functions


def sensor_assignment(desktop, session, account_id, system_id, full_history, asset_info, automotive_template, update_bar):
    pythoncom.CoInitialize()
    # Initializing loop
    node_info = general_functions.gather_account_nodes(session, account_id)
    system_builder_functions.delete_old_templates(session, account_id)
    template_info = system_builder_functions.upload_templates(session, account_id)
    sensor_errors_asset_group = []
    sensor_errors_asset_sub_group = []
    sensor_errors_asset_name = []
    sensor_errors_MP = []
    sensor_errors_id = []
    sensor_errors_type = []
    # Samping Freq Values
    samp_freq_values = {'8192': '0',
                        '4096': '2',
                        '2048': '4',
                        '1024': '8',
                        '512': '16',
                        '256': '32',
                        '128': '64',
                        '64': '128'
                        }
    for i in range(0, len(asset_info)):
        group_name = str(asset_info['Asset Group'][i]).replace("/", "-")
        sub_group_name = str(asset_info['Asset Sub-Group'][i]).replace("/", "-")
        asset_name = str(asset_info['Asset Name'][i]).replace("/", "-")
        MP_name = str(asset_info['MP'][i]).replace("/", "-")
        x_axis_name = str(asset_info['X-Axis'][i])
        y_axis_name = str(asset_info['Y-Axis'][i])
        # These two lines are for sampling frequency
        if str(asset_info['Sampling Frequency'][i]) != 'nan':
            samp_freq = str(asset_info['Sampling Frequency'][i])
            sf_value = samp_freq_values[samp_freq]
        else:
            sf_value = 'nan'
        # next line is for update interval
        if str(asset_info['Update Interval'][i]) != 'nan':
            update_interval = str(int(asset_info['Update Interval'][i]) * 60 * 1000)
        else:
            update_interval = 'nan'
        # next line is to assign sensor nickname
        if str(asset_info['Sensor Nickname'][i]) != 'nan':
            nickname = str(asset_info['Sensor Nickname'][i])
        else:
            nickname = 'nan'
        if str(asset_info['Sensor #'][i]) == 'nan':
            sensor_id = 'not set'
        elif str(asset_info['Sensor #'][i]) == 'not set':
            sensor_id = 'not set'
        else:
            sensor_id = str(asset_info['Sensor #'][i])
        # Adding group folder
        if group_name == 'nan':
            id1 = system_id
        elif group_name != 'nan':
            checkLevel = system_builder_functions.search_level(session, group_name, system_id)
            if not checkLevel:
                if i > 0 and str(asset_info['Asset Group'][i]) != str(
                        asset_info['Asset Group'][i - 1]):  # this checks to ensure no repeats
                    payload = {'groupId': system_id, 'Name': group_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 1}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(system_id), data=payload)
                elif i == 0:  # this checks to ensure that the code adds the first item without skipping
                    payload = {'groupId': system_id, 'Name': group_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 1}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(system_id), data=payload)
                else:
                    pass
                group_id = system_builder_functions.find_level(session, group_name, system_id)
                id1 = group_id
            else:
                group_id = checkLevel
                id1 = group_id
        # Adding sub-group folder
        if sub_group_name == 'nan' and group_name == 'nan':
            id2 = system_id
        elif sub_group_name == 'nan' and group_name != 'nan':
            id2 = group_id
        elif sub_group_name != 'nan':
            checkLevel = system_builder_functions.search_level(session, sub_group_name, id1)
            if not checkLevel:
                if i > 0 and str(asset_info['Asset Sub-Group'][i]) != str(
                        asset_info['Asset Sub-Group'][i - 1]):  # this checks to ensure no repeats
                    payload = {'groupId': id1, 'Name': sub_group_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 1}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id1), data=payload)
                elif i > 0 and str(asset_info['Asset Sub-Group'][i]) == str(asset_info['Asset Sub-Group'][i - 1]) \
                        and str(asset_info['Asset Group'][i]) != str(
                    asset_info['Asset Group'][i - 1]):  # this checks to ensure no repeats
                    payload = {'groupId': id1, 'Name': asset_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 2}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id1), data=payload)
                elif i == 0:  # this checks to ensure that the code adds the first item without skipping
                    payload = {'groupId': id1, 'Name': sub_group_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 1}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id1), data=payload)
                else:
                    pass
                sub_group_id = system_builder_functions.find_level(session, sub_group_name, id1)
                id2 = sub_group_id
            else:
                sub_group_id = checkLevel
                id2 = sub_group_id
        # Adding asset folder
        if asset_name == 'nan' and group_name == 'nan' and sub_group_name == 'nan':
            id3 = system_id
        elif asset_name == 'nan' and group_name != 'nan' and sub_group_name == 'nan':
            id3 = group_id
        elif asset_name == 'nan' and group_name == 'nan' and sub_group_name != 'nan':
            id3 = sub_group_id
        elif asset_name != 'nan':
            checkLevel = system_builder_functions.search_level(session, asset_name, id2)
            if not checkLevel:
                if i > 0 and str(asset_info['Asset Name'][i]) != str(
                        asset_info['Asset Name'][i - 1]):  # this checks to ensure no repeats
                    payload = {'groupId': id2, 'Name': asset_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 2}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id2), data=payload)
                elif i > 0 and str(asset_info['Asset Name'][i]) == str(asset_info['Asset Name'][i - 1]) \
                        and str(asset_info['Asset Sub-Group'][i]) != str(
                    asset_info['Asset Sub-Group'][i - 1]):  # this checks to ensure no repeats
                    payload = {'groupId': id2, 'Name': asset_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 2}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id2), data=payload)
                elif i == 0:  # this checks to ensure that the code adds the first item without skipping
                    payload = {'groupId': id2, 'Name': asset_name, 'GroupCreationCount': '1', 'TemplateId': '-1',
                               'Type': 2}
                    sendRequest.post(session, api='/api2/groups/{}/children'.format(id2), data=payload)
                else:
                    pass
                asset_id = system_builder_functions.find_level(session, asset_name, id2)
                id3 = asset_id
            else:
                asset_id = checkLevel
                id3 = asset_id
        # Adding Monitoring point
        if automotive_template:
            template_id = template_info[template_info['name'] == 'STANDARD Automotive Monitoring Point Template 6-6-19'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'A' and y_axis_name == 'R':
            template_id = template_info[template_info['name'] == 'Code-MP-XA-YR'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'R' and y_axis_name == 'A':
            template_id = template_info[template_info['name'] == 'Code-MP-XR-YA'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'A' and y_axis_name == 'H':
            template_id = template_info[template_info['name'] == 'Code-MP-XA-YH'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'A' and y_axis_name == 'V':
            template_id = template_info[template_info['name'] == 'Code-MP-XA-YV'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'H' and y_axis_name == 'A':
            template_id = template_info[template_info['name'] == 'Code-MP-XH-YA'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'V' and y_axis_name == 'A':
            template_id = template_info[template_info['name'] == 'Code-MP-XV-YA'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'V' and y_axis_name == 'H':
            template_id = template_info[template_info['name'] == 'Code-MP-XV-YH'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'H' and y_axis_name == 'V':
            template_id = template_info[template_info['name'] == 'Code-MP-XH-YV'].reset_index(drop=True)['Id'][0]
        elif x_axis_name == 'nan' and y_axis_name == 'nan':
            template_id = template_info[template_info['name'] == 'Code-MP'].reset_index(drop=True)['Id'][0]
        else:
            template_id = template_info[template_info['name'] == 'Code-MP'].reset_index(drop=True)['Id'][0]
        payload = {'Name': MP_name,
                   'GroupCreationCount': '1',
                   'TemplateId': str(template_id),
                   'Type': '3',  # hard coded as vibration
                   'MonitoringPointType': '2'}
        sendRequest.post(session, api='/api2/groups/{}/children'.format(id3), data=payload)
        # Finding monitoring point ID
        MP_id = system_builder_functions.find_level(session, MP_name, id3)
        if sensor_id != 'not set':
            try:
                node_id = int(node_info[node_info['SerialNumber'] == sensor_id]['NodeId'].reset_index(drop=True)[0])
                # assigning sensor
                payload = {'Selection': full_history, 'Time': strftime("%Y-%m-%dT%H:%M:%S+00:00", gmtime()),
                           'NodeId': node_id,
                           'GroupId': MP_id}
                sendRequest.post(session, api='/api2/groups/{}/node'.format(MP_id), data=payload)
                time.sleep(2)
                # assigning update interval
                if update_interval == 'nan':
                    # defaulting to 10 min interval because sometimes the update interval gets set to empty
                    payload = {'value': str(10*60*1000)}
                    sendRequest.post(session, api='/api2/nodes/{}/settings/UpdateInterval'.format(node_id),
                                     data=payload)
                    time.sleep(2)
                else:
                    payload = {'value': update_interval}
                    sendRequest.post(session, api='/api2/nodes/{}/settings/UpdateInterval'.format(node_id), data=payload)
                    time.sleep(2)
                # assigning sampling freq
                if sf_value == 'nan':
                    pass
                else:
                    try:
                        r_samp = sendRequest.get(session, api='/api2/nodes/{}/settings/DecimationFactor'.format(node_id))
                        current_value = r_samp.json()['CurrentValue']
                        pending_value = r_samp.json()['PendingValue']
                        if sf_value == current_value or sf_value == pending_value:
                            pass
                        else:
                            sendRequest.post(session, api='/api2/nodes/{}/settings/DecimationFactor'.format(node_id),
                                             data={'value': sf_value})
                            time.sleep(2)
                    except KeyError:
                        sensor_errors_asset_group.append(group_name)
                        sensor_errors_asset_sub_group.append(sub_group_name)
                        sensor_errors_asset_name.append(asset_name)
                        sensor_errors_MP.append(MP_name)
                        sensor_errors_id.append(sensor_id)
                        sensor_errors_type.append('Error assigning Sampling Frequency')
                # assigning nicknames
                if nickname == 'nan':
                    pass
                else:
                    sendRequest.put(session, api='/api2/nodes/%s/nickname'.format(node_id), data=nickname)
            except IndexError:
                sensor_errors_asset_group.append(group_name)
                sensor_errors_asset_sub_group.append(sub_group_name)
                sensor_errors_asset_name.append(asset_name)
                sensor_errors_MP.append(MP_name)
                sensor_errors_id.append(sensor_id)
                sensor_errors_type.append('Sensor not found')
        else:
            pass
        if i == len(asset_info) - 1:
            xl = Dispatch('Excel.Application')
            for wb in xl.Workbooks:
                if wb.Name == 'System Builder Errors.xlsx':
                    wb.Close(False)
                else:
                    pass
            # Creating error list
            error_list = pd.DataFrame(
                data=[sensor_errors_asset_group, sensor_errors_asset_sub_group, sensor_errors_asset_name,
                      sensor_errors_MP, sensor_errors_id, sensor_errors_type])
            error_list = error_list.transpose()
            error_list.columns = ['Asset Group', 'Asset Sub-Group', 'Asset Name', 'MP', 'Sensor Serial Number', 'Error Type']
            error_list = error_list.reset_index(drop=True)
            # Creating error list
            writer = pd.ExcelWriter(desktop + '\\System Builder Errors.xlsx', engine='xlsxwriter')
            error_list.to_excel(writer, sheet_name='Results')
            writer.close()
            # Deleting templates
            system_builder_functions.delete_templates(session, template_info['Id'])
            pythoncom.CoUninitialize()
            update_bar()
        else:
            time.sleep(5)
            update_bar()
