from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

import sendRequest


def time_in_alarm(manager):
    # This function will get the time in alarm and then continue to the actual function that determines alarm settings
    # that function activates once the screen changes to the first progress screen
    def submit(entry, popup):
        if entry.isdigit():
            popup.dismiss()
            manager.current = 'ProgressScreen'
            return entry
        else:
            layout = GridLayout(cols=1, padding=10)
            popupLabel = Label(text="Please enter a NUMBER greater than 0")
            OkButton = Button(text='Ok', size_hint=(1, 0.25))
            layout.add_widget(popupLabel)
            layout.add_widget(OkButton)
            popup2 = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                          size=(400, 400))
            OkButton.bind(on_press=lambda a: time_in_alarm(manager))
            popup2.open()
    layout = GridLayout(cols=1, padding=10)
    popupLabel = Label(text='Enter number of minutes for time in alarm.')
    EnterButton = Button(text='Enter', size_hint=(1, 0.25))
    text_input = TextInput(hint_text='ex: 15', multiline=False, size_hint=(0.25, 0.25), font_size=20, halign='center',
                           valign='middle', input_filter='int')
    layout.add_widget(popupLabel)
    layout.add_widget(text_input)
    layout.add_widget(EnterButton)
    popup1 = Popup(title='Time in alarm', content=layout, auto_dismiss=False, size_hint=(None, None),
                   size=(400, 400))
    EnterButton.bind(on_press=lambda a: submit(text_input.text, popup1))
    text_input.bind(on_text_validate=lambda a: submit(text_input.text, popup1))
    popup1.open()


def set_alarms(session, alarm_info, time_alarm, update_bar):

    for i in range(0, len(alarm_info)):
        high_alarm = alarm_info['Alarm Levels'][i]
        high_alarm = str(round(high_alarm, 4))
        high_warn = alarm_info['Warning Levels'][i]
        high_warn = str(round(high_warn, 4))
        indicator_id = str(alarm_info['Indicator Id'][i])
        url_high_alarm = '/api2/indicators/settings/highalarm?Value={}&Enabled=true&DestinationIndicatorIds={}' \
            .format(high_alarm, indicator_id)
        url_high_warn = '/api2/indicators/settings/highwarning?Value={}&Enabled=true&DestinationIndicatorIds={}' \
            .format(high_warn, indicator_id)
        url_time_alarm = '/api2/indicators/settings/percentTimeInAlarm?Value=100&Enabled=true&Seconds={}&DestinationIndicatorIds={}' \
            .format(time_alarm, indicator_id)
        rha = sendRequest.post(session, api=url_high_alarm)
        rhw = sendRequest.post(session, api=url_high_warn)
        rta = sendRequest.post(session, api=url_time_alarm)
        update_bar()