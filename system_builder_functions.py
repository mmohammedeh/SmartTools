import json
import os
import time

import pandas as pd
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import general_functions
import sendRequest


###############################
# System Builder Functions

# Deleting previous templates in case they are out of date
def delete_old_templates(session, account_id):
    r_templates = sendRequest.get(session, api='/api2/accounts/{}/groupTemplates'.format(account_id))
    template_list = r_templates.json()['Templates']
    for filename in os.listdir('SD Templates'):
        for i in template_list:
            if i['Name'] == filename.split('.sdt')[0]:
                sendRequest.delete(session, api='/api2/grouptemplates/{}'.format(i['Id']))
            else:
                pass


def delete_templates(session, template_ids):
    # Deleting templates
    for template_id in template_ids:
        sendRequest.delete(session, api='/api2/grouptemplates/{}'.format(template_id))


# Uploading current templates
def upload_templates(session, account_id):
    # monitoring point templates should be in a folder on your desktop
    template_names = []
    template_ids = []
    for filename in os.listdir('SD Templates'):
        with open('SD Templates/' + filename, 'rb') as f:
            r_upload = sendRequest.post(session, api='/api2/accounts/{}/groupTemplates'.format(account_id), files={filename: f})
            template_names.append(filename.split('.sdt')[0])
            template_ids.append(r_upload.json()['Id'])
    template_info = pd.DataFrame(data=[template_names, template_ids])
    template_info = template_info.transpose()
    template_info.columns = ['name', 'Id']
    return template_info


# Finding the children ID to add folders/monitoring point onto
def find_level(session, name, id):
    attempt = 0
    while attempt < 30:
        try:
            payload = {'groupId': id}
            groups = sendRequest.get(session, api='/api2/groups/{}/children'.format(id), data=payload)
            group_id = general_functions.id_filter(groups.json(), name)
            return group_id
        except (IndexError, TypeError, json.decoder.JSONDecodeError):
            attempt = attempt + 1
            time.sleep(attempt*(attempt/2))
            pass
    layout = GridLayout(cols=1, padding=10)
    popupLabel = Label(text='Failed to add {}! Please check the excel sheet \n'
                            'and make sure the first four columns are sorted \n'
                            'alphabetically using custom sort!'.format(name))
    OkButton = Button(text='Ok', size_hint=(1, 0.25))
    layout.add_widget(popupLabel)
    layout.add_widget(OkButton)
    popup = Popup(title='Error while trying to find the software id of {}'.format(name),
                  content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    OkButton.bind(on_press=popup.dismiss)
    popup.open()


# Finding the parent ID to add folders/monitoring point onto
def search_level(session, name, id):
    attempt = 0
    payload = {'groupId': id,
               'searchTerm': name,
               'pageLimit': 999,
               'page': 1}
    while attempt < 30:
        try:
            raw_data = sendRequest.get(session, api='/api2/groups/{}/searchGroups'.format(id), data=payload)
            raw_data = raw_data.json()
            if raw_data["Total"] == 0:
                return False
            else:
                for bb in range(0, raw_data["Total"]):
                    if name == raw_data["Result"][bb]["name"]:
                        return raw_data["Result"][bb]["id"]
                    else:
                        continue
            return False
        except (IndexError, TypeError, json.decoder.JSONDecodeError):
            attempt = attempt + 1
            time.sleep(attempt*(attempt/2))
            pass
    layout = GridLayout(cols=1, padding=10)
    popupLabel = Label(text='Failed to add {}! Please check the excel sheet \n'
                            'and make sure the first four columns are sorted \n'
                            'alphabetically using custom sort!'.format(name))
    OkButton = Button(text='Ok', size_hint=(1, 0.25))
    layout.add_widget(popupLabel)
    layout.add_widget(OkButton)
    popup = Popup(title='Error while trying to find the software id of {}'.format(name),
                  content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    OkButton.bind(on_press=popup.dismiss)
    popup.open()
