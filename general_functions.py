# This is a group of functions responsible for finding ids to add information to using the API
import os
from calendar import monthrange
from datetime import datetime, timedelta
from dateutil.tz import *
import pandas as pd
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import sendRequest


########################################################################################################################
# Commonly used functions
def get_accounts(session):
    # Organizing account info
    r_accounts = sendRequest.get(session, api='/api2/accounts')
    accounts_info = r_accounts.json()
    account = [str(accounts_info[i]['CorporationName']) for i in range(0, len(accounts_info))]
    account_name = [str(accounts_info[i]['Name']) for i in range(0, len(accounts_info))]
    account_Id = [str(accounts_info[i]['Id']) for i in range(0, len(accounts_info))]
    account_active = [str(accounts_info[i]['Active']) for i in range(0, len(accounts_info))]
    account_data = pd.DataFrame(data=[account, account_name, account_Id, account_active])
    account_data = account_data.transpose()
    account_data.columns = ['Account Name', 'Name', 'Id', 'Active']
    account_data = account_data[account_data['Active'] == 'True']
    choices = account_data['Account Name'] + ' - ' + account_data['Name']
    return account_data, choices


def get_sub_accounts(session, account_id):
    # Retrieving sub-system tree
    r_subsystem = sendRequest.get(session, api='/api2/accounts/{}/children'.format(account_id))
    account_group = r_subsystem.json()
    # Organizing sub-system info
    system_data_name = [str(account_group[i]['Name']) for i in range(0, len(account_group))]
    system_data_Id = [str(account_group[i]['Id']) for i in range(0, len(account_group))]
    system_data = pd.DataFrame(data=[system_data_name, system_data_Id])
    system_data = system_data.transpose()
    system_data.columns = ['Name', 'Id']
    choices = system_data['Name']
    return system_data, choices

def get_system_group_ids(session, system_id):
    r_group = sendRequest.get(session, api='/api2/groups/{}/children'.format(system_id))
    group = r_group.json()
    group_name = []
    group_Id = []
    for i in range(0, len(group)):
        group_name.append(str(group[i]['Name']))
        group_Id.append(str(group[i]['Id']))
    group_data = pd.DataFrame(data=[group_name, group_Id])
    group_data = group_data.transpose()
    group_data.columns = ['Name', 'Id']
    choices = group_data['Name']
    return group_data, choices

def gather_group_nodes(session, system_id):
    # find node ids to assign sensor
    payload = {'groupIds': system_id,
               'start': 0,
               'count': 99999}
    session, all_ind = sendRequest.post(session, api='/api2/groups/sensors', data=payload)
    all_ind = all_ind.json()
    # Organizing node info
    sensor_serials = [str(all_ind['Result'][i]['SerialNumber']) for i in range(0, len(all_ind['Result']))]
    node_ids = [str(all_ind['Result'][i]['NodeId']) for i in range(0, len(all_ind['Result']))]
    node_info = pd.DataFrame(data=[sensor_serials, node_ids]).transpose()
    node_info.columns = ['SerialNumber', 'NodeId']
    return node_info


def gather_account_nodes(session, account_id):
    # find node ids to assign sensor
    payload = {'accountId': account_id,
               'Page': 0,
               'PageLimit': 99999}
    r_all_ind = sendRequest.get(session, api='/api2/accounts/{}/sensors'.format(account_id), data=payload)
    dest_ids = r_all_ind.json()['Result']
    sensor_serials = [str(dest_ids[i]['SerialNumber']) for i in range(0, len(dest_ids))]
    node_ids = [str(dest_ids[i]['NodeId']) for i in range(0, len(dest_ids))]
    node_info = pd.DataFrame(data=[sensor_serials, node_ids])
    node_info = node_info.transpose()
    node_info.columns = ['SerialNumber', 'NodeId']
    return node_info


def id_filter(raw_data, filter_name):
    names = [str(raw_data[i]['Name']) for i in range(0, len(raw_data))]
    ids = [str(raw_data[i]['Id']) for i in range(0, len(raw_data))]
    info = pd.DataFrame(data=[names, ids])
    info = info.transpose()
    info.columns = ['Name', 'Id']
    filtered_id = info[info['Name'] == filter_name]['Id'].reset_index(drop=True)[0]
    return filtered_id


def filtered_indicator_data(session, filter_id, system_id):
    payload = {'GroupIds': system_id,
               'FilterIds': filter_id,
               'PageLimit': 1,
               'Page': 0,
               'SystemId': system_id}
    r = sendRequest.post(session, api='/api2/groups/filteredIndicators/filterId', data=payload)
    list1 = r.json()
    payload = {'GroupIds': system_id,
               'FilterIds': filter_id,
               'PageLimit': list1['SetTotal'],
               'Page': 0,
               'SystemId': system_id}
    r = sendRequest.post(session, api='/api2/groups/filteredIndicators/filterId', data=payload)
    list1 = r.json()
    return list1


######################################################
# Date Functions
def get_time_range(manager):
    local = tzlocal()  # This contains the local timezone
    utc = tzutc()  # This contains the utc timezone
    current_day = datetime.now().replace(tzinfo=local).day
    current_month = datetime.now().replace(tzinfo=local).month
    current_year = datetime.now().replace(tzinfo=local).year
    specified_interval = 0
    diff_month_question = False

    def yes():
        get_time_range.diff_month_question = True
        set_interval()

    def no():
        get_time_range.diff_month_question = False
        set_interval()

    def set_interval():
        def month():
            month_interval()

        def specify():

            def submit(entry):
                if entry.isdigit() and(int(entry) > 0 and int(entry) < 8):
                    entry = int(entry)
                    get_time_range.specified_interval = entry
                    daily_interval()
                else:
                    popup = Popup(title='Error', auto_dismiss=False, size_hint=(None, None),
                                  size=(400, 400))
                    layout = GridLayout(cols=1, padding=10)
                    popupLabel = Label(text="Please enter a NUMBER equal to 7 or less and greater than 0",
                                       text_size=popup.size,
                                       halign="center",
                                       valign="middle",
                                       padding_x=10)
                    OkButton = Button(text='Ok', size_hint=(1, 0.25))
                    layout.add_widget(popupLabel)
                    layout.add_widget(OkButton)
                    OkButton.bind(on_press=lambda a: specify(), on_release=popup.dismiss)
                    popup.content = layout
                    popup.open()

            popup = Popup(title='Enter Interval Length', auto_dismiss=False, size_hint=(None, None),
                          size=(400, 400))
            layout = BoxLayout(orientation='vertical', padding=10)
            popupLabel = Label(text='Enter an interval of up to 7 days?.\n'
                                    'If you choose a specific date, the interval will be added to it.\n'
                                    'If you do not specify a date, today will be the END date and the interval '
                                    'will be subtracted.',
                               text_size=popup.size,
                               halign="center",
                               valign="middle",
                               padding_x=10
                               )
            EnterButton = Button(text='Enter', size_hint=(1, 0.25))
            text_input = TextInput(hint_text='Number of days (up to 7)', multiline=False, size_hint=(1, 0.25), font_size=20,
                                   halign='center', valign='middle', input_filter='int')
            layout.add_widget(popupLabel)
            layout.add_widget(text_input)
            layout.add_widget(EnterButton)
            EnterButton.bind(on_press=lambda a: submit(text_input.text), on_release=popup.dismiss)
            popup.content = layout
            popup.open()

        popup = Popup(title='Interval', auto_dismiss=False, size_hint=(None, None), size=(400, 400))
        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Do you want to proceed with a 1 month interval or specify an interval of up to 7 days?',
                           text_size=popup.size,
                           halign="center",
                           valign="middle",
                           padding_x=10)
        MonthButton = Button(text='One Month Interval', size_hint=(1, 0.25))
        SpecifyButton = Button(text='Specify an Interval', size_hint=(1, 0.25))
        layout.add_widget(popupLabel)
        layout.add_widget(MonthButton)
        layout.add_widget(SpecifyButton)
        MonthButton.bind(on_press=lambda a: month(), on_release=popup.dismiss)
        SpecifyButton.bind(on_press=lambda a: specify(), on_release=popup.dismiss)
        popup.content = layout
        popup.open()

    layout = BoxLayout(orientation='vertical', padding=10)
    popupLabel = Label(text='Do you wish to specify a specific date?', size_hint=(1, 0.5))
    YesButton = Button(text='Yes', size_hint=(1, 0.25))
    NoButton = Button(text='No', size_hint=(1, 0.25))
    layout.add_widget(popupLabel)
    layout.add_widget(YesButton)
    layout.add_widget(NoButton)
    popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    YesButton.bind(on_press=lambda a: yes(), on_release=popup.dismiss)
    NoButton.bind(on_press=lambda a: no(), on_release=popup.dismiss)
    popup.open()

    def month_interval():
        def submit(entry1, entry2):
            if entry1.isdigit() and entry2.isdigit():
                entry1 = int(entry1)
                entry2 = int(entry2)
                checking = check_dates(entry1, entry2, None)
                if checking[0]:
                    if entry1 == 12:
                        year2 = entry2 + 1
                        next_month = 1
                    else:
                        year2 = entry2
                        next_month = entry1 + 1
                    date_first = datetime.now().replace(year=entry2, month=entry1, day=1, hour=0, minute=0, second=0,
                                                        microsecond=0).replace(tzinfo=local)
                    date_first = date_first.astimezone(utc)
                    date_last = datetime.now().replace(year=year2, month=next_month, day=1, hour=0, minute=0, second=0,
                                                       microsecond=0).replace(tzinfo=local)
                    date_last = date_last.astimezone(utc)
                    manager.ids.choosegroupmulti.start_time = format(date_first, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                    manager.ids.choosegroupmulti.end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                    manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
                    manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
                    manager.current = 'ProgressScreen'
                else:
                    if not checking[1]:
                        incorrect_month = 'Incorrect month entered'
                    else:
                        incorrect_month = ''
                    if not checking[2]:
                        future_date = 'Future date entered'
                    else:
                        future_date = ''
                    if not checking[3]:
                        incorrect_year = 'Incorrect year entered'
                    else:
                        incorrect_year = ''
                    layout = GridLayout(cols=1, padding=10)
                    popupLabel = Label(text="You entered an incorrect:\n{}\n{}\n{}".format(incorrect_month, future_date,
                                                                                           incorrect_year))
                    OkButton = Button(text='Ok', size_hint=(1, 0.25))
                    layout.add_widget(popupLabel)
                    layout.add_widget(OkButton)
                    popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                                  size=(400, 400))
                    OkButton.bind(on_press=lambda a: month_interval(), on_release=popup.dismiss)
                    popup.open()
            else:
                layout = GridLayout(cols=1, padding=10)
                popupLabel = Label(text="Please enter the dates in the correct formats.")
                OkButton = Button(text='Ok', size_hint=(1, 0.25))
                layout.add_widget(popupLabel)
                layout.add_widget(OkButton)
                popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                              size=(400, 400))
                OkButton.bind(on_press=lambda a: month_interval(), on_release=popup.dismiss)
                popup.open()

        if get_time_range.diff_month_question:
            layout = BoxLayout(orientation='vertical', padding=10)
            popupLabel = Label(text='Enter the month and year you want as the start date.', size_hint=(1, 0.25))
            EnterButton = Button(text='Enter', size_hint=(1, 0.25))
            text_input_month = TextInput(hint_text='ex: 7', multiline=False, size_hint=(1, 0.25), font_size=20,
                                         halign='center', valign='middle', input_filter='int')
            text_input_year = TextInput(hint_text='ex: 2019', multiline=False, size_hint=(1, 0.25), font_size=20,
                                        halign='center', valign='middle', input_filter='int')
            layout.add_widget(popupLabel)
            layout.add_widget(text_input_month)
            layout.add_widget(text_input_year)
            layout.add_widget(EnterButton)
            popup = Popup(title='Date Entry', content=layout, auto_dismiss=False, size_hint=(None, None),
                          size=(400, 400))
            EnterButton.bind(on_press=lambda a: submit(text_input_month.text, text_input_year.text), on_release=popup.dismiss)
            popup.open()
        else:
            last_month = current_month - 1 if current_month > 1 else 12
            if last_month == 12:
                year1 = current_year - 1
                year2 = current_year
            else:
                year1 = current_year
                year2 = year1
            date_first = datetime.now().replace(year=year1, month=last_month, day=1, hour=0, minute=0, second=0,
                                                microsecond=0).replace(tzinfo=local)
            date_first = date_first.astimezone(utc)
            date_last = datetime.now().replace(year=year2, month=current_month, day=1, hour=0, minute=0,
                                               second=0, microsecond=0).replace(tzinfo=local)
            date_last = date_last.astimezone(utc)
            manager.ids.choosegroupmulti.start_time = format(date_first, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            manager.ids.choosegroupmulti.end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
            manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
            manager.current = 'ProgressScreen'

    def daily_interval():
        def submit(entry1, entry2, entry3):
            if entry1.isdigit() and entry1.isdigit() and entry1.isdigit():
                entry1 = int(entry1)
                entry2 = int(entry2)
                entry3 = int(entry3)
                checking = check_dates(int(entry1), int(entry2), int(entry3))
                if checking[0]:
                    date_first = datetime.now().replace(year=entry2, month=entry1, day=entry3, hour=0, minute=0,
                                                        second=0, microsecond=0)
                    date_last = date_first + timedelta(days=get_time_range.specified_interval)
                    date_first = date_first.replace(tzinfo=local).astimezone(utc)
                    date_last = date_last.replace(tzinfo=local).astimezone(utc)
                    manager.ids.choosegroupmulti.start_time = format(date_first, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                    manager.ids.choosegroupmulti.end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
                    manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
                    manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
                    manager.current = 'ProgressScreen'
                else:
                    if not checking[1]:
                        incorrect_month = 'Incorrect month entered'
                    else:
                        incorrect_month = ''
                    if not checking[2]:
                        future_date = 'Future date entered'
                    else:
                        future_date = ''
                    if not checking[3]:
                        incorrect_year = 'Incorrect year entered'
                    else:
                        incorrect_year = ''
                    layout = GridLayout(cols=1, padding=10)
                    popupLabel = Label(text="You entered an incorrect:\n{}\n{}\n{}".format(incorrect_month, future_date,
                                                                                           incorrect_year))
                    OkButton = Button(text='Ok', size_hint=(1, 0.25))
                    layout.add_widget(popupLabel)
                    layout.add_widget(OkButton)
                    popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                                  size=(400, 400))
                    OkButton.bind(on_press=lambda a: daily_interval(), on_release=popup.dismiss)
                    popup.open()
            else:
                layout = GridLayout(cols=1, padding=10)
                popupLabel = Label(text="Please enter the dates in the correct formats.")
                OkButton = Button(text='Ok', size_hint=(1, 0.25))
                layout.add_widget(popupLabel)
                layout.add_widget(OkButton)
                popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                              size=(400, 400))
                OkButton.bind(on_press=lambda a: daily_interval(), on_release=popup.dismiss)
                popup.open()

        if get_time_range.diff_month_question:
            layout = BoxLayout(orientation='vertical', padding=10)
            popupLabel = Label(text='Enter the day, month, and year of the start date',
                               size_hint=(1, 0.2))
            EnterButton = Button(text='Enter', size_hint=(1, 0.2))
            text_input_day = TextInput(hint_text='ex: 1', multiline=False, size_hint=(1, 0.2), font_size=20,
                                       halign='center', valign='middle', input_filter='int')
            text_input_month = TextInput(hint_text='ex: 5', multiline=False, size_hint=(1, 0.2), font_size=20,
                                         halign='center', valign='middle', input_filter='int')
            text_input_year = TextInput(hint_text='ex: 2019', multiline=False, size_hint=(1, 0.2), font_size=20,
                                        halign='center', valign='middle', input_filter='int')
            layout.add_widget(popupLabel)
            layout.add_widget(text_input_day)
            layout.add_widget(text_input_month)
            layout.add_widget(text_input_year)
            layout.add_widget(EnterButton)
            popup = Popup(title='Date Entry', content=layout, auto_dismiss=False, size_hint=(None, None),
                          size=(400, 400))
            EnterButton.bind(on_press=lambda a: submit(text_input_month.text, text_input_year.text,
                                                       text_input_day.text), on_release=popup.dismiss)
            popup.open()
        else:
            date_last = datetime.now().replace(year=current_year, month=current_month, day=current_day, hour=0,
                                               minute=0, second=0,
                                               microsecond=0).replace(tzinfo=local)
            date_first = date_last - timedelta(days=get_time_range.specified_interval)
            date_first = date_first.astimezone(utc)
            date_last = date_last.astimezone(utc)
            manager.ids.choosegroupmulti.start_time = format(date_first, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            manager.ids.choosegroupmulti.end_time = format(date_last, '%Y-%m-%dT%H:%M:%S.0000+00:00')
            manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
            manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
            manager.current = 'ProgressScreen'

    def check_dates(entry1, entry2, entry3):

        # Checking Month
        if entry1 < 1 or entry1 > 12:
            correct_month = False
        else:
            correct_month = True

        # Checking for Future Date
        if (entry1 > current_month and entry2 == current_year) or entry2 > current_year:
            no_future_date = False
        else:
            no_future_date = True

        # Checking Day
        if entry3 is None:
            correct_day = True
        elif entry3 is not None:
            number_days = monthrange(entry2, entry1)[1]
            if entry3 < 1 or (entry3 >= current_day and entry1 >= current_month):
                correct_day = False
            else:
                correct_day = True

        # Returning whether date is correct
        if correct_day and correct_month and no_future_date:
            return True, correct_month, no_future_date, correct_day
        else:
            return False, correct_month, no_future_date, correct_day


########################################################################################################################
# Kivy reusable functions

def ok_popup(title, message, response):
    popup = Popup(title=title, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    popupLabel = Label(text=message,
                       text_size=popup.size,
                       halign="center",
                       valign="middle",
                       padding_x=10)
    OkButton = Button(text='Ok', size_hint=(1, 0.25))
    OkButton.bind(on_press=popup.dismiss, on_release=response)
    layout = BoxLayout(orientation='vertical', padding=10)
    layout.add_widget(popupLabel)
    layout.add_widget(OkButton)
    popup.content = layout
    popup.open()


def entry_popup(title, message, hint, input_filter, manager):

    def submit(entry):
        if manager.ids.mainmenu.desired_script == 2:
            if entry.isdigit() and int(entry) > 0:
                manager.ids.choosegroupmulti.avg_days = int(entry)
                manager.current = 'ProgressScreen'
            else:
                ok_popup(title='Error',
                         message="Please enter a NUMBER greater than 0",
                         response=lambda a: entry_popup(title='Enter Average Length',
                                                        message='Enter the number of days you want the '
                                                                'signal strength data averaged over.',
                                                        hint='Number of days',
                                                        input_filter='int',
                                                        manager=manager))
    popup = Popup(title=title, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    popupLabel = Label(text=message,
                       text_size=popup.size,
                       halign="center",
                       valign="middle",
                       padding_x=10)
    EnterButton = Button(text='Enter', size_hint=(1, 0.25))
    text_input = TextInput(hint_text=hint,
                           multiline=False,
                           size_hint=(1, 0.25), 
                           font_size=20,
                           halign='center',
                           valign='middle',
                           input_filter=input_filter)
    # text_input.bind(on_text_validate=process_entry(popup.content))
    layout = BoxLayout(orientation='vertical', padding=10)
    layout.add_widget(popupLabel)
    layout.add_widget(text_input)
    layout.add_widget(EnterButton)
    popup.content = layout
    EnterButton.bind(on_press=popup.dismiss, on_release=lambda a: submit(text_input.text))
    popup.open()


def yn_popup(manager, title, message):
    def yes():
        manager.ids.choosesystemsingle.full_history = '3'
        manager.current = 'ProgressScreen'

    def no():
        manager.ids.choosesystemsingle.full_history = '1'
        manager.current = 'ProgressScreen'

    popup = Popup(title=title, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    popupLabel = Label(text=message,
                       text_size=popup.size,
                       halign="center",
                       valign="middle",
                       padding_x=10)
    YesButton = Button(text='Yes', size_hint=(1, 0.25))
    NoButton = Button(text='No', size_hint=(1, 0.25))
    YesButton.bind(on_press=popup.dismiss, on_release=lambda a: yes())
    NoButton.bind(on_press=popup.dismiss, on_release=lambda a: no())
    layout = BoxLayout(orientation='vertical', padding=10)
    layout.add_widget(popupLabel)
    layout.add_widget(YesButton)
    layout.add_widget(NoButton)
    popup.content = layout
    popup.open()


def multientry_popup(title, message, response, **args):
    popup = Popup(title=title, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    popupLabel = Label(text=message,
                       text_size=popup.size,
                       halign="center",
                       valign="middle",
                       padding_x=10)
    EnterButton = Button(text='Enter', size_hint=(1, 0.25))
    EnterButton.bind(on_press=popup.dismiss, on_release=response)
    layout = BoxLayout(orientation='vertical', padding=10)
    for template in args:
        text_input = TextInput(hint_text=template[0],
                               multiline=False,
                               size_hint=(1, 0.25),
                               font_size=20,
                               halign='center',
                               valign='middle',
                               input_filter=template[1])
        layout.add_widget(text_input)
    layout.add_widget(popupLabel)
    layout.add_widget(EnterButton)
    popup.content = layout
    popup.open()


def complete_popup(App, manager):
    def app_exit():
        App.get_running_app().stop()

    def mainmenu():
        # Clear out variables so we can start over with a different script.
        manager.ids.chooseaccount.default_system_data = []
        manager.ids.chooseaccount.chosen_account = ''
        manager.ids.chooseaccount.account_id = ''
        manager.ids.chooseaccount.ids.search_box1.text = ''
        manager.ids.chooseaccount.ids.rv_chooseaccount.layout_manager.selected_nodes = []
        manager.ids.chooseaccount.ids.rv_chooseaccount.refresh_from_data()
        manager.ids.choosesystemsingle.system_id = []
        manager.ids.choosesystemsingle.full_history = []
        manager.ids.choosesystemsingle.ids.rv_choosesystem.data = []
        manager.ids.choosesystemsingle.ids.rv_choosesystem.layout_manager.selected_nodes = []
        manager.ids.choosesystemsingle.ids.rv_choosesystem.refresh_from_data()
        manager.ids.choosesystemmulti.system_names = []
        manager.ids.choosesystemmulti.system_ids = []
        manager.ids.choosesystemmulti.ids.rv_choosesystem.data = []
        manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
        manager.ids.choosegroupmulti.ids.rv_choosegroup.data = []
        manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        manager.ids.choosesystemmulti.system_names = []
        manager.ids.choosesystemmulti.system_ids = []
        manager.ids.choosegroupmulti.current_system_name = []
        manager.ids.choosegroupmulti.current_system_number = 0
        manager.ids.choosegroupmulti.group_ids = []
        manager.ids.choosegroupmulti.group_data = []
        manager.ids.choosegroupmulti.group_system_names = []
        manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()
        manager.ids.progress.ids.pb.value = 0
        manager.ids.progress2.ids.pb.value = 0
        manager.ids.progress.current_thread = None
        manager.ids.progress2.current_thread = None
        manager.current = 'MainMenu'

    popup = Popup(title='Done', auto_dismiss=False, size_hint=(None, None), size=(400, 400))
    popupLabel = Label(text="Process Completed Successfully")
    ExitButton = Button(text='Exit', size_hint=(1, 0.25))
    MainMenuButton = Button(text='Main Menu', size_hint=(1, 0.25))
    ExitButton.bind(on_press=popup.dismiss, on_release=lambda a: app_exit())
    MainMenuButton.bind(on_press=popup.dismiss, on_release=lambda a: mainmenu())
    layout = BoxLayout(orientation='vertical', padding=10)
    layout.add_widget(popupLabel)
    layout.add_widget(ExitButton)
    layout.add_widget(MainMenuButton)
    popup.content = layout
    popup.open()
