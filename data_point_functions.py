import re
from calendar import monthrange
from datetime import datetime, timedelta

from dateutil.tz import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


######################################################
# Date Functions
def get_time_daily(manager, local):
    current_day = datetime.now().replace(tzinfo=local).day
    current_month = datetime.now().replace(tzinfo=local).month
    current_year = datetime.now().replace(tzinfo=local).year

    def start_date():
        def check_dates(entry1, entry2, entry3):
            # Checking Month
            if entry2 < 1 or entry2 > 12:
                correct_month = False
            else:
                correct_month = True
            # Checking for Future Date
            if (entry2 > current_month and entry3 == current_year) or entry3 > current_year:
                no_future_date = False
            else:
                no_future_date = True
            # Checking Day
            if entry1 is None:
                correct_day = True
            elif entry1 is not None:
                if entry1 < 1 or (entry1 > current_day and entry2 >= current_month):
                    correct_day = False
                else:
                    correct_day = True
            # Returning whether date is correct
            if correct_day and correct_month and no_future_date:
                return True, correct_month, no_future_date, correct_day
            else:
                return False, correct_month, no_future_date, correct_day

        def submit(entry1, entry2, entry3):
            checking = check_dates(int(entry1), int(entry2), int(entry3))
            if checking[0]:
                set_intervals(int(entry1), int(entry2), int(entry3))
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
                OkButton.bind(on_press=lambda a: start_date(), on_release=popup.dismiss)
                popup.open()

        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Enter the start date:\nday, month, and year',
                           size_hint=(1, 0.2))
        EnterButton = Button(text='Enter', size_hint=(1, 0.2))
        text_input_day = TextInput(hint_text='Start Day ex: 1', multiline=False, size_hint=(1, 0.2), font_size=20,
                                   halign='center', valign='middle', input_filter='int', write_tab=False)
        text_input_month = TextInput(hint_text='Start Month ex: 5 = May', multiline=False, size_hint=(1, 0.2),
                                     font_size=20, halign='center', valign='middle', input_filter='int',
                                     write_tab=False)
        text_input_year = TextInput(hint_text='Start Year ex: 2019', multiline=False, size_hint=(1, 0.2), font_size=20,
                                    halign='center', valign='middle', input_filter='int', write_tab=False)
        layout.add_widget(popupLabel)
        layout.add_widget(text_input_day)
        layout.add_widget(text_input_month)
        layout.add_widget(text_input_year)
        layout.add_widget(EnterButton)
        popup = Popup(title='Date Entry', content=layout, auto_dismiss=False, size_hint=(None, None),
                      size=(400, 400))
        EnterButton.bind(on_press=lambda a: submit(text_input_day.text, text_input_month.text,
                                                   text_input_year.text), on_release=popup.dismiss)
        popup.open()

    def set_intervals(day, month, year):
        def submit(entry1):
            if int(entry1) > 0 and int(entry1) < 8 and (day + int(entry1)) <= current_day:
                manager.ids.choosegroupmulti.specified_daily_interval = int(entry1)
                date_first = datetime.now().replace(year=year, month=month, day=day, hour=0, minute=0,
                                                    second=0, microsecond=0)
                # need this in datetime format so we can subtract them in later code
                manager.ids.choosegroupmulti.start_time = date_first
                if manager.ids.choosegroupmulti.specified_daily_interval != 0:
                    date_last = date_first + timedelta(
                        days=manager.ids.choosegroupmulti.specified_daily_interval - 1)
                else:
                    date_last = date_first + timedelta(
                        days=manager.ids.choosegroupmulti.specified_daily_interval)
                manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
                manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
                manager.current = 'ProgressScreen'
            else:
                popup = Popup(title='Error', auto_dismiss=False, size_hint=(None, None),
                              size=(400, 400))
                layout = GridLayout(cols=1, padding=10)
                popupLabel = Label(text="Please enter a day interval greater than 0 but less than "
                                        "what would cross today up to 7",
                                   text_size=popup.size,
                                   halign="center",
                                   valign="middle",
                                   padding_x=10)
                OkButton = Button(text='Ok', size_hint=(1, 0.25))
                layout.add_widget(popupLabel)
                layout.add_widget(OkButton)
                OkButton.bind(on_press=lambda a: set_intervals(day, month, year),
                              on_release=popup.dismiss)
                popup.content = layout
                popup.open()

        popup = Popup(title='Enter Interval Length', auto_dismiss=False, size_hint=(None, None),
                      size=(400, 400))
        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Enter the length of days (If you wanted today, you need to choose the hourly code).',
                           text_size=popup.size,
                           halign="center",
                           valign="middle",
                           padding_x=10
                           )
        EnterButton = Button(text='Enter', size_hint=(1, 0.25))
        text_input2 = TextInput(hint_text='Number of days (up to 7), Ex: 7', multiline=False, size_hint=(1, 0.25),
                                font_size=20, halign='center', valign='middle', input_filter='int')
        layout.add_widget(popupLabel)
        layout.add_widget(text_input2)
        layout.add_widget(EnterButton)
        EnterButton.bind(on_press=lambda a: submit(text_input2.text),
                         on_release=popup.dismiss)
        popup.content = layout
        popup.open()
    start_date()


def get_time_hourly(manager, local):
    current_day = datetime.now().replace(tzinfo=local).day
    current_month = datetime.now().replace(tzinfo=local).month
    current_year = datetime.now().replace(tzinfo=local).year

    def start_date():
        def check_dates(entry1, entry2, entry3):
            # Checking Month
            if entry2 < 1 or entry2 > 12:
                correct_month = False
            else:
                correct_month = True
            # Checking for Future Date
            if (entry2 > current_month and entry3 == current_year) or entry3 > current_year:
                no_future_date = False
            else:
                no_future_date = True
            # Checking Day
            if entry1 is None:
                correct_day = True
            elif entry1 is not None:
                if entry1 < 1 or (entry1 > current_day and entry2 >= current_month):
                    correct_day = False
                else:
                    correct_day = True
            # Returning whether date is correct
            if correct_day and correct_month and no_future_date:
                return True, correct_month, no_future_date, correct_day
            else:
                return False, correct_month, no_future_date, correct_day

        def submit(entry0, entry1, entry2, entry3):
            checking = check_dates(int(entry1), int(entry2), int(entry3))
            if checking[0]:
                manager.ids.choosegroupmulti.starting_hour = int(entry0)
                set_intervals(int(entry0), int(entry1), int(entry2), int(entry3))
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
                OkButton.bind(on_press=lambda a: start_date(), on_release=popup.dismiss)
                popup.open()

        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Enter the start date:\nhour (24-hour format), day, month, and year',
                           size_hint=(1, 0.2))
        EnterButton = Button(text='Enter', size_hint=(1, 0.2))
        text_input_hour = TextInput(hint_text='Start Hour ex: 14 = 2 PM', multiline=False, size_hint=(1, 0.2), font_size=20,
                                   halign='center', valign='middle', input_filter='int', write_tab=False)
        text_input_day = TextInput(hint_text='Start Day ex: 1', multiline=False, size_hint=(1, 0.2), font_size=20,
                                   halign='center', valign='middle', input_filter='int', write_tab=False)
        text_input_month = TextInput(hint_text='Start Month ex: 5 = May', multiline=False, size_hint=(1, 0.2), font_size=20,
                                     halign='center', valign='middle', input_filter='int', write_tab=False)
        text_input_year = TextInput(hint_text='Start Year ex: 2019', multiline=False, size_hint=(1, 0.2), font_size=20,
                                    halign='center', valign='middle', input_filter='int', write_tab=False)
        layout.add_widget(popupLabel)
        layout.add_widget(text_input_hour)
        layout.add_widget(text_input_day)
        layout.add_widget(text_input_month)
        layout.add_widget(text_input_year)
        layout.add_widget(EnterButton)
        popup = Popup(title='Date Entry', content=layout, auto_dismiss=False, size_hint=(None, None),
                      size=(400, 400))
        EnterButton.bind(on_press=lambda a: submit(text_input_hour.text, text_input_day.text, text_input_month.text,
                                                   text_input_year.text), on_release=popup.dismiss)
        popup.open()

    def set_intervals(start_hour, day, month, year):
        def submit(entry0, entry1):
            if int(entry0) > 0 and int(entry1) < 25:
                manager.ids.choosegroupmulti.specified_hourly_interval = int(entry0)
                if int(entry1) < 8:
                    manager.ids.choosegroupmulti.specified_daily_interval = int(entry1)
                    date_first = datetime.now().replace(year=year, month=month, day=day, hour=start_hour, minute=0,
                                                        second=0, microsecond=0)
                    # need this in datetime format so we can subtract them in later code
                    manager.ids.choosegroupmulti.start_time = date_first
                    if manager.ids.choosegroupmulti.specified_daily_interval != 0:
                        date_last = date_first + timedelta(
                            days=manager.ids.choosegroupmulti.specified_daily_interval - 1)
                    else:
                        date_last = date_first + timedelta(
                            days=manager.ids.choosegroupmulti.specified_daily_interval)
                    manager.ids.choosegroupmulti.date_excel1 = format(date_first, '%m-%d-%Y')
                    manager.ids.choosegroupmulti.date_excel2 = format(date_last, '%m-%d-%Y')
                    manager.current = 'ProgressScreen'
                else:
                    popup = Popup(title='Error', auto_dismiss=False, size_hint=(None, None),
                                  size=(400, 400))
                    layout = GridLayout(cols=1, padding=10)
                    popupLabel = Label(text="Please enter a day interval less than 7",
                                       text_size=popup.size,
                                       halign="center",
                                       valign="middle",
                                       padding_x=10)
                    OkButton = Button(text='Ok', size_hint=(1, 0.25))
                    layout.add_widget(popupLabel)
                    layout.add_widget(OkButton)
                    OkButton.bind(on_press=lambda a: set_intervals(start_hour, day, month, year), on_release=popup.dismiss)
                    popup.content = layout
                    popup.open()
            else:
                popup = Popup(title='Error', auto_dismiss=False, size_hint=(None, None),
                              size=(400, 400))
                layout = GridLayout(cols=1, padding=10)
                popupLabel = Label(text="Please enter an hourly interval equal to 24 or less and greater than 0",
                                   text_size=popup.size,
                                   halign="center",
                                   valign="middle",
                                   padding_x=10)
                OkButton = Button(text='Ok', size_hint=(1, 0.25))
                layout.add_widget(popupLabel)
                layout.add_widget(OkButton)
                OkButton.bind(on_press=lambda a: set_intervals(start_hour, day, month, year), on_release=popup.dismiss)
                popup.content = layout
                popup.open()

        popup = Popup(title='Enter Interval Length', auto_dismiss=False, size_hint=(None, None),
                      size=(400, 400))
        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Enter the length of hours and days (days=0 if you want just today).\n'
                                'The example below would be an 8 hour interval each day for 7 days',
                           text_size=popup.size,
                           halign="center",
                           valign="middle",
                           padding_x=10
                           )
        EnterButton = Button(text='Enter', size_hint=(1, 0.25))
        text_input1 = TextInput(hint_text='Number of hours (up to 24), Ex: 8', multiline=False, size_hint=(1, 0.25),
                                font_size=20, halign='center', valign='middle', input_filter='int', write_tab=False)
        text_input2 = TextInput(hint_text='Number of days (up to 7), Ex: 7', multiline=False, size_hint=(1, 0.25),
                                font_size=20, halign='center', valign='middle', input_filter='int', write_tab=False)
        layout.add_widget(popupLabel)
        layout.add_widget(text_input1)
        layout.add_widget(text_input2)
        layout.add_widget(EnterButton)
        EnterButton.bind(on_press=lambda a: submit(text_input1.text, text_input2.text),
                         on_release=popup.dismiss)
        popup.content = layout
        popup.open()
    start_date()
