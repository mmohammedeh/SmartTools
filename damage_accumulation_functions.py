import pandas as pd
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
import general_functions

######################################################
# Make sure the entered asset classes actually exist
import sendRequest


def retrieve_asset_classes(manager, session):
    popup = Popup(title='Asset Class Entry',
                  auto_dismiss=False, size_hint=(None, None),
                  size=(400, 400))
    layout = BoxLayout(orientation='vertical', padding=10)
    popupLabel = Label(text='Enter all of the asset classes you are interested in separated by commas',
                       text_size=popup.size,
                       halign="center",
                       valign="middle",
                       padding_x=10
                       )
    EnterButton = Button(text='Submit', size_hint=(1, 0.25))
    scroll_view = ScrollView(size=(popup.width, popup.height), size_hint=(1, 0.75))
    text_input = TextInput(hint_text='ex: 001-01-01, 001-01-02, ...', multiline=False, font_size=20, halign='center',
                           valign='middle')
    layout.add_widget(popupLabel)
    scroll_view.add_widget(text_input)
    layout.add_widget(scroll_view)
    layout.add_widget(EnterButton)
    EnterButton.bind(on_press=lambda a: process_asset_classes(manager, session, text_input.text),
                     on_release=popup.dismiss)
    popup.content = layout
    popup.open()


def process_asset_classes(manager, session, entry):
    r_filters = sendRequest.get(session, api='/api2/accounts/{}/filters'.format(manager.ids.chooseaccount.account_id))
    filter_list = r_filters.json()
    if ',' in entry:
        manager.ids.choosegroupmulti.entered_asset_classes = [a.replace(' ', '') for a in entry.split(',') if a != '']
    elif '\n' in entry:
        manager.ids.choosegroupmulti.entered_asset_classes = [a.replace(' ', '') for a in entry.split('\n') if a != '']
    elif ',' in entry and '\n' in entry:
        manager.ids.choosegroupmulti.entered_asset_classes = [a.replace(' ', '').replace('\n', '')
                                                           for a in entry.split(',') if a != '']
    else:
        manager.ids.choosegroupmulti.entered_asset_classes = [a.replace(' ', '').replace('\n', '')
                                                              for a in entry.split(',') if a != '']
    asset_classes = []
    filter_ids = []
    b = []  # messed up asset class entries
    for x in manager.ids.choosegroupmulti.entered_asset_classes:
        for n in range(0, len(filter_list)):
            if (x in filter_list[n]['Name'] and 'Damage Accumulation' in filter_list[n]['Name']) or \
                    (x in filter_list[n]['Name'] and 'DA' in filter_list[n]['Name']):
                asset_classes.append(x)
                filter_ids.append(filter_list[n]['Id'])
                break
            else:
                if n == len(filter_list) - 1:
                    b.append(x)
                else:
                    pass
    # Notifying if asset class filter failed to be found
    if len(b) != 0:
        incorrect_asset_classes = [b + ',' for b in b]
        layout = GridLayout(cols=1, padding=10)
        popupLabel = Label(text="The following asset class(es) contain(s) a mistake,\n"
                                "{}\n"
                                "Please re-enter the asset class list.".format(incorrect_asset_classes),
                           halign="center",
                           valign="middle",
                           padding_x=10)
        OkButton = Button(text='Ok', size_hint=(1, 0.25))
        layout.add_widget(popupLabel)
        layout.add_widget(OkButton)
        popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None),
                      size=(400, 400))
        OkButton.bind(on_press=popup.dismiss, on_release=lambda a: retrieve_asset_classes(manager, session))
        popup.open()
    else:
        asset_class_info = pd.DataFrame(data=[asset_classes, filter_ids]).transpose()
        asset_class_info.columns = ["Asset Class", "Filter Id"]
        general_functions.get_time_range(manager)
        manager.ids.choosegroupmulti.asset_class_info = asset_class_info
