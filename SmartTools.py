import shutil

from dateutil.tz import tzlocal, tzutc
from kivy.config import Config

import data_point_functions
import sendRequest

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.clock import Clock
from kivy.properties import BooleanProperty
import SystemBuilder
import HeatMap
import DamageAccumulationCalculation
import AlarmLevelSetter
import DataPointTransmission
import SensorAudit
import heat_map_functions
import general_functions
import damage_accumulation_functions
import alarm_level_setter_functions
from queue import Queue
from threading import Thread
import pandas as pd
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
import os, winshell
from datetime import timedelta

kivy.require('1.11.1')
Builder.load_file("smarttools.kv")


class ThreadWithReturnValue(Thread):
    # This code is used for returning a variable when a thread ends.
    # Dont need it right now but most likely in the future
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


class MyScreenManager(ScreenManager):
    pass


class MainMenu(Screen):
    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)
        self.desired_script = 0

    def set_desired_roi_da_calculator(self):
        self.desired_script = 3
        self.manager.current = 'DACalculator'


class SystemEditorMain(Screen):

    def set_desired_system_builder(self):
        self.manager.ids.mainmenu.desired_script = 1
        self.manager.current = 'SystemBuilderMain'

    def set_desired_alarm_setter(self):
        self.manager.ids.mainmenu.desired_script = 4
        self.manager.current = 'AlarmLevels'


class SystemAudits(Screen):

    def set_desired_ss_audit(self):
        self.manager.ids.mainmenu.desired_script = 2
        self.manager.current = 'SSAuditMain'

    def set_desired_data_point(self):
        self.manager.ids.mainmenu.desired_script = 5
        self.manager.current = 'DataPointTransmissionAudit'

    def set_desired_sensor_audit(self):
        self.manager.ids.mainmenu.desired_script = 6
        self.manager.current = 'SensorAuditMain'

class AlarmLevels(Screen):
    pass


class AlarmLevelsCheck(Screen):
    def open_alarm_levels(self):
        # So in order to run this app on pycharm we need the desktop version of this path, the actual app uses the file
        # which is already located in the same folder of the .exe
        # os.startfile(App.get_running_app().desktop + '\\SmartTools Suite Installer\\Alarm Levels.xlsx')
        os.startfile(App.get_running_app().my_documents + '\\Smart Tools\\Alarm Levels.xlsx')


class DACalculator(Screen):
    pass


class DataPointTransmissionAudit(Screen):
    pass


class SystemBuilderMain(Screen):
    def open_asset_info(self):
        # So in order to run this app on pycharm we need the desktop version of this path, the actual app uses the file
        # which is already located in the same folder of the .exe
        # os.startfile(App.get_running_app().desktop + '\\SmartTools Suite Installer\\asset_info.xlsx')
        os.startfile(App.get_running_app().my_documents + '\\Smart Tools\\asset_info.xlsx')


class SSAuditMain(Screen):
    pass


class SensorAuditMain(Screen):
    pass


class UpdateApp(Screen):
    def __init__(self, **kwargs):
        super(UpdateApp, self).__init__(**kwargs)
        # Setting up progress bar values
        self.total_size = []
        self.block_size = 1024
        self.unit = 'KB'
        self.wrote = 0
        self.online_version = ''
        self.current_version = ''
        self.session_git = None
        Clock.schedule_once(lambda a: self.initialize_update())

    def initialize_update(self):
        # Read version file
        version_file = open(App.get_running_app().my_documents + '\\Smart Tools\\version', 'r')
        self.current_version = version_file.read()
        # Retrieve online version file
        self.session_git, self.online_version = sendRequest.update_program_check()
        if self.online_version != self.current_version:
            version_file.close()
            self.update_popup()
        elif self.online_version == self.current_version:
            try:
                # Remove setup.exe after the app relaunches assuming app updated successfully
                # might need some error checking here
                version_file.close()
                os.remove(App.get_running_app().my_documents + '\\Smart Tools\\smart_tools_setup.exe')
            except FileNotFoundError:
                version_file.close()
                pass

    def yes(self):
        self.manager.current = 'UpdateApp'

    def no(self):
        pass

    def update_popup(self):
        popup = Popup(title='Update Available', auto_dismiss=False, size_hint=(None, None), size=(400, 400))
        popupLabel = Label(text='Do you want to update to the latest version? (Recommended)',
                           text_size=popup.size,
                           halign="center",
                           valign="middle",
                           padding_x=10)
        YesButton = Button(text='Yes', size_hint=(1, 0.25))
        NoButton = Button(text='No', size_hint=(1, 0.25))
        YesButton.bind(on_press=popup.dismiss, on_release=lambda a: self.yes())
        NoButton.bind(on_press=popup.dismiss, on_release=lambda a: self.no())
        layout = BoxLayout(orientation='vertical', padding=10)
        layout.add_widget(popupLabel)
        layout.add_widget(YesButton)
        layout.add_widget(NoButton)
        popup.content = layout
        popup.open()

    def begin_bar(self):
        # This code block will run when the user enters the screen (it is triggered from the .kv file)
        thread = Thread(target=self.download_app)
        thread.start()

    def download_app(self):
        with open(App.get_running_app().my_documents + '\\SmartTools\\smart_tools_setup.exe', 'wb') as f:
            # Streaming, so we can iterate over the response.
            r_download_setup = self.session_git.get(
                '',
                stream=True)
            # Total size in bytes.
            self.total_size = int(r_download_setup.headers.get('content-length', 0))
            # total = math.ceil(self.total_size // self.block_size)
            self.manager.ids.updateapp.ids.pb.max = self.total_size
            self.manager.ids.updateapp.ids.pb_label.text = 'Downloading update...\nProgress: {}/{}'.format(0,
                                                                                    self.manager.ids.updateapp.ids.pb.max)
            for data in r_download_setup.iter_content(self.block_size):
                self.wrote = self.wrote + len(data)
                f.write(data)
                self.update_bar()

    def update_bar(self, dt=None):
        # This code controls the progress bar updating. It runs in the same thread as the main thread (gui)
        self.manager.ids.updateapp.ids.pb.value = self.wrote
        self.manager.ids.updateapp.ids.pb_label.text = 'Downloading update...\nProgress: {}%'.format(
            int(100*int(self.manager.ids.updateapp.ids.pb.value)/int(self.manager.ids.updateapp.ids.pb.max)))
        if self.manager.ids.updateapp.ids.pb.value == self.manager.ids.updateapp.ids.pb.max:
            if self.total_size != 0 and self.wrote != self.total_size:
                popup = Popup(title='Error', auto_dismiss=False, size_hint=(None, None), size=(400, 400))
                popupLabel = Label(text="Setup file was not downloaded successfully. "
                                        "Please ensure you have a stable internet connection and try again later.",
                                   text_size=popup.size,
                                   halign="center",
                                   valign="middle",
                                   padding_x=10)
                exitbutton = Button(text='Launch Setup', size_hint=(1, 0.25))
                exitbutton.bind(on_press=popup.dismiss, on_release=lambda a: App.get_running_app().stop())
                layout = GridLayout(cols=1, padding=10)
                layout.add_widget(popupLabel)
                layout.add_widget(exitbutton)
                popup.content = layout
                popup.open()
            elif self.total_size != 0 and self.wrote == self.total_size:
                popup = Popup(title='Done', auto_dismiss=False, size_hint=(None, None), size=(400, 400))
                popupLabel = Label(text="Process Completed Successfully.\n "
                                        "Please click the button below and follow the setup instructions!",
                                   text_size=popup.size,
                                   halign="center",
                                   valign="middle",
                                   padding_x=10)
                LaunchSetup = Button(text='Launch Setup', size_hint=(1, 0.25))
                LaunchSetup.bind(on_press=popup.dismiss, on_release=lambda a: self.update_complete())
                layout = GridLayout(cols=1, padding=10)
                layout.add_widget(popupLabel)
                layout.add_widget(LaunchSetup)
                popup.content = layout
                popup.open()
        else:
            pass

    def update_complete(self):
        open(App.get_running_app().my_documents + '\\SmartTools\\version', 'w').write(self.online_version)
        os.startfile(App.get_running_app().my_documents + '\\SmartTools\\smart_tools_setup.exe')
        App.get_running_app().stop()


class ChooseAccount(Screen):
    def __init__(self, **kwargs):
        super(ChooseAccount, self).__init__(**kwargs)
        session = App.get_running_app().session
        account_data, choices = general_functions.get_accounts(session)
        self.default_choices = [{'text': str(x)} for x in choices.values]
        self.default_data = account_data
    default_system_data = []
    chosen_account = ''
    account_id = ''

    def clear_account_data(self):
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.layout_manager.selected_nodes = []
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.refresh_from_data()
        self.manager.ids.chooseaccount.default_system_data = []
        self.manager.ids.chooseaccount.chosen_account = ''
        self.manager.ids.chooseaccount.account_id = ''
        self.manager.ids.chooseaccount.ids.search_box1.text = ''

    def choose_account_back_button(self):
        if self.manager.ids.mainmenu.desired_script == 1:
            self.clear_account_data()
            self.manager.current = 'SystemBuilderMain'
        elif self.manager.ids.mainmenu.desired_script == 2:
            self.clear_account_data()
            self.manager.current = 'SSHeatMapMain'
        elif self.manager.ids.mainmenu.desired_script == 3:
            self.clear_account_data()
            self.manager.current = 'DAHeatMap'
        elif self.manager.ids.mainmenu.desired_script == 4:
            self.clear_account_data()
            self.manager.current = 'AlarmLevels'
        elif self.manager.ids.mainmenu.desired_script == 5:
            self.clear_account_data()
            self.manager.current = 'DataPointTransmissionAudit'
        elif self.manager.ids.mainmenu.desired_script == 6:
            self.clear_account_data()
            self.manager.current = 'SensorAuditMain'

    def search(self):
        search_value = self.manager.ids.chooseaccount.ids.search_box1.text
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.data = self.default_choices
        rv_data = [list(self.manager.ids.chooseaccount.ids.rv_chooseaccount.data[a].values())[0]
                   for a in range(0, len(self.manager.ids.chooseaccount.ids.rv_chooseaccount.data))]
        filtered_data = [{'text': str(x)} for x in [a for a in rv_data if search_value.lower() in a.lower()]]
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.data = filtered_data
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.refresh_from_data()

    def update_continue_button(self):
        session = App.get_running_app().session
        data = self.manager.ids.chooseaccount.ids.rv_chooseaccount.data
        node = self.manager.ids.chooseaccount.ids.rv_chooseaccount.layout_manager.selected_nodes
        if not node:
            general_functions.ok_popup(title='Error',
                                       message="You need to choose an account to continue.",
                                       response=lambda a: None)
        else:
            choice_account = data[node[0]]['text'].split(' - ', 1)
            search_result1 = self.default_data[self.default_data['Account Name'] == choice_account[0]]
            account_id = search_result1[search_result1['Name'] == choice_account[1]].reset_index(drop=True)['Id'][0]
            system_data, choices = general_functions.get_sub_accounts(session, account_id)
            data2 = [{'text': str(x)} for x in choices.values]
            self.chosen_account = choice_account[1]
            self.account_id = account_id
            self.default_system_data = system_data
            if self.manager.ids.mainmenu.desired_script == 1:
                self.manager.ids.choosesystemsingle.ids.rv_choosesystem.data = data2
                self.manager.ids.choosesystemsingle.ids.rv_choosesystem.refresh_from_data()
                self.manager.current = 'ChooseSystemSingle'
            elif self.manager.ids.mainmenu.desired_script == 2 or self.manager.ids.mainmenu.desired_script == 3 \
                    or self.manager.ids.mainmenu.desired_script == 4 or self.manager.ids.mainmenu.desired_script == 5\
                    or self.manager.ids.mainmenu.desired_script == 6:
                self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data = data2
                self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
                self.manager.current = 'ChooseSystemMulti'

    def load_accounts(self):
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.data = self.manager.ids.chooseaccount.default_choices
        self.manager.current = 'ChooseAccount'


class ChooseSystemSingle(Screen):
    system_id = []
    full_history = []
    auto_template = False

    def back_button(self):
        self.manager.ids.choosesystemsingle.system_id = []
        self.manager.ids.choosesystemsingle.full_history = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.layout_manager.selected_nodes = []
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.refresh_from_data()
        self.manager.current = 'ChooseAccount'

    def question_full_history(self):
        layout = BoxLayout(orientation='vertical', padding=10)
        popupLabel = Label(text='Do you wish to assign full history to the sensor?\n '
                                '(DO NOT USE FOR NEW SENSOR INSTALLS)',
                           size_hint=(1, 0.5))
        YesButton = Button(text='Yes', size_hint=(1, 0.25))
        NoButton = Button(text='No', size_hint=(1, 0.25))
        layout.add_widget(popupLabel)
        layout.add_widget(YesButton)
        layout.add_widget(NoButton)
        popup = Popup(title='Error', content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
        YesButton.bind(on_press=lambda a: self.yes(), on_release=popup.dismiss)
        NoButton.bind(on_press=lambda a: self.no(), on_release=popup.dismiss)
        popup.open()

    def use_automotive_template(self):
        self.auto_template = True
        self.question_full_history()

    def yes(self):
        self.full_history = '3'
        self.manager.current = 'ProgressScreen'

    def no(self):
        self.full_history = '1'
        self.manager.current = 'ProgressScreen'

    def update_continue_button(self):
        system_data = self.manager.ids.chooseaccount.default_system_data
        data = self.manager.ids.choosesystemsingle.ids.rv_choosesystem.data
        nodes = self.manager.ids.choosesystemsingle.ids.rv_choosesystem.layout_manager.selected_nodes
        if not nodes:
            general_functions.ok_popup(title='Error',
                                       message="You need to choose a system to continue.",
                                       response=lambda a: None)
        else:
            choice_system = data[nodes[0]]['text']
            system_id = system_data[system_data['Name'] == choice_system].reset_index(drop=True)['Id'][0]
            self.system_id = system_id
            layout = BoxLayout(orientation='vertical', padding=10)
            popupLabel = Label(text='Do you wish to use the automotive template?', size_hint=(1, 0.5))
            YesButton = Button(text='Yes', size_hint=(1, 0.25))
            NoButton = Button(text='No', size_hint=(1, 0.25))
            layout.add_widget(popupLabel)
            layout.add_widget(YesButton)
            layout.add_widget(NoButton)
            popup = Popup(title='Automotive question', content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
            YesButton.bind(on_press=lambda a:self.use_automotive_template(), on_release=popup.dismiss)
            NoButton.bind(on_press=lambda a:self.question_full_history(), on_release=popup.dismiss)
            popup.open()


class ChooseSystemMulti(Screen):
    system_names = []
    system_ids = []

    def back_button(self):
        self.manager.ids.choosesystemmulti.system_names = []
        self.manager.ids.choosesystemmulti.system_ids = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.layout_manager.selected_nodes = []
        self.manager.ids.chooseaccount.ids.rv_chooseaccount.refresh_from_data()
        self.manager.current = 'ChooseAccount'

    def clear_all(self):
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()

    def select_all(self):
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes =\
            [a for a in range(0, len(self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data))]
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()

    def update_continue_button(self):
        system_data = self.manager.ids.chooseaccount.default_system_data
        data = self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data
        nodes = self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes
        if not nodes:
            general_functions.ok_popup(title='Error',
                                       message="You need to choose at least one system to continue.",
                                       response=lambda a: None)
        else:
            for i in range(0, len(nodes)):
                choice_system = data[nodes[i]]['text']
                self.system_names.append(choice_system)
                self.system_ids.append(system_data[system_data['Name'] == choice_system].reset_index(drop=True)['Id'][0])
            self.manager.current = 'ChooseGroupMulti'


class ChooseGroupMulti(Screen):
    asset_class_info = []
    entered_asset_classes = []
    group_ids = []
    group_data = []
    group_system_names = []
    current_system_name = []
    current_system_number = 0
    system_information = []
    time_in_alarm = 0
    avg_days = 0
    specified_daily_interval = 0 # this is for data point code
    specific_date = False # this is for data point code
    specified_hourly_interval = 0 # this is for data point code
    starting_hour = 0 # this is for data point code
    start_time = ''
    end_time = ''
    date_excel1 = ''
    date_excel2 = ''
    day_or_hour = None  # this is for data point code

    def day_or_hour_function(self, code_type):
        # this is for data point code
        if code_type == 0:
            self.day_or_hour = 'day'
            data_point_functions.get_time_daily(self.manager, App.get_running_app().local)
        elif code_type == 1:
            self.day_or_hour = 'hour'
            data_point_functions.get_time_hourly(self.manager, App.get_running_app().local)

    def back_button(self):
        self.manager.ids.choosesystemmulti.system_names = []
        self.manager.ids.choosesystemmulti.system_ids = []
        self.manager.ids.choosegroupmulti.current_system_name = []
        self.manager.ids.choosegroupmulti.current_system_number = 0
        self.manager.ids.choosegroupmulti.group_ids = []
        self.manager.ids.choosegroupmulti.group_data = []
        self.manager.ids.choosegroupmulti.group_system_names = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()
        self.manager.current = 'ChooseSystemMulti'

    def clear_all(self):
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()

    def select_all(self):
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes =\
            [a for a in range(0, len(self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data))]
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()

    def initialize_data(self):
        session = App.get_running_app().session
        self.group_data, choices = general_functions.get_system_group_ids(session, self.manager.ids.choosesystemmulti.system_ids[self.current_system_number])
        self.current_system_name = self.manager.ids.choosesystemmulti.system_names[self.current_system_number]
        self.manager.ids.choosegroupmulti.ids.group_label.text = 'Choose all of the groups from {} that you are interested in'.format(self.current_system_name)
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data = [{'text': str(x)} for x in choices.values]
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()

    def update_continue_button(self):
        # This code gets all of the system ids and system names
        if self.current_system_number < len(self.manager.ids.choosesystemmulti.system_ids) - 1:
            last_system = False
        else:
            last_system = True
        group_data = self.group_data
        data = self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data
        nodes = self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes
        if not nodes:
            general_functions.ok_popup(title='Error',
                                       message="You need to choose at least one group to continue.",
                                       response=lambda a: None)
        else:
            if not last_system:
                for i in range(0, len(nodes)):
                    choice_group = data[nodes[i]]['text']
                    self.group_ids.append(group_data[group_data['Name'] == choice_group].reset_index(drop=True)['Id'][0])
                    self.group_system_names.append(self.current_system_name)
                self.current_system_number += 1
                self.initialize_data()
            else:
                for i in range(0, len(nodes)):
                    choice_group = data[nodes[i]]['text']
                    self.group_ids.append(group_data[group_data['Name'] == choice_group].reset_index(drop=True)['Id'][0])
                    self.group_system_names.append(self.current_system_name)
                system_information = pd.DataFrame(data=[self.group_system_names, self.group_ids])
                system_information = system_information.transpose()
                system_information.columns = ['Name', 'Id']
                self.system_information = system_information
                # Here is where the code can diverge depending on the script;
                if self.manager.ids.mainmenu.desired_script == 2:
                    # this is asking for date intervals
                    heat_map_functions.get_time_range(self.manager)
                elif self.manager.ids.mainmenu.desired_script == 3:
                    # We need to enter the asset classes so we will ask for them then the date intervals afterwards
                    # in a different function
                    session = App.get_running_app().session
                    damage_accumulation_functions.retrieve_asset_classes(self.manager, session)
                elif self.manager.ids.mainmenu.desired_script == 4:
                    # grab time in alarm before moving on
                    self.time_in_alarm = alarm_level_setter_functions.time_in_alarm(self.manager)
                elif self.manager.ids.mainmenu.desired_script == 5:
                    # grab time range first
                    popup = Popup(title='Choose Time Range Settings',
                                  auto_dismiss=False, size_hint=(None, None),
                                  size=(400, 400))
                    layout = BoxLayout(orientation='vertical', padding=10)
                    popupLabel = Label(text='Do you want a day-by-day or hour-by-hour audit?',
                                       text_size=popup.size,
                                       halign="center",
                                       valign="middle",
                                       padding_x=10
                                       )
                    DayButton = Button(text='Day-by-Day', size_hint=(1, 0.25))
                    HourButton = Button(text='Hour-by-Hour', size_hint=(1, 0.25))
                    DayButton.bind(on_press=lambda a: self.day_or_hour_function(0),
                                   on_release=popup.dismiss)
                    HourButton.bind(on_press=lambda a: self.day_or_hour_function(1),
                                    on_release=popup.dismiss)
                    layout.add_widget(popupLabel)
                    layout.add_widget(DayButton)
                    layout.add_widget(HourButton)
                    popup.content = layout
                    popup.open()
                elif self.manager.ids.mainmenu.desired_script == 6:
                    self.manager.current = 'ProgressScreen'

class ProgressScreen(Screen):
    def __init__(self, **kwargs):
        super(ProgressScreen, self).__init__(**kwargs)
        self.q = Queue()
        self.results = []
        self.current_thread = None

    def setup(self):
        pass

    def exit(self):
        App.get_running_app().stop()

    def mainmenu(self):
        # Clear out variables so we can start over with a different script.
        # Is it possible to make this less disgusting?
        self.manager.ids.chooseaccount.clear_account_data()  # this helps clean it up a bit,
        # we could do something similar here
        self.manager.ids.choosesystemsingle.system_id = []
        self.manager.ids.choosesystemsingle.full_history = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.choosesystemmulti.system_names = []
        self.manager.ids.choosesystemmulti.system_ids = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        self.manager.ids.choosegroupmulti.current_system_name = []
        self.manager.ids.choosegroupmulti.current_system_number = 0
        self.manager.ids.choosegroupmulti.group_ids = []
        self.manager.ids.choosegroupmulti.group_data = []
        self.manager.ids.choosegroupmulti.group_system_names = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()
        self.manager.ids.progress.ids.pb.value = 0
        self.current_thread = None
        self.manager.current = 'MainMenu'

    def initialize_thread(self, iterator, target, name, *args):
        # This starts the thread and keeps track of it. I did this to experiment with returning values from a thread
        # it was a lot harder than I anticipated so I will return to this later.
        self.manager.ids.progress.ids.pb.max = len(iterator)
        self.manager.ids.progress.ids.pb_label.text = 'Progress: {}/{}'.format(0, self.manager.ids.progress.ids.pb.max)
        self.current_thread = ThreadWithReturnValue(target=target, name=name, args=args)
        self.current_thread.start()

    def begin_bar(self):
        # This code block will run when the user enters the screen (it is triggered from the .kv file)
        # Here we have to initialize threads in order to run long scripts, otherwise the gui will lag and
        # the progress bar wont work.
        desktop = App.get_running_app().desktop
        my_documents = App.get_running_app().my_documents
        session = App.get_running_app().session
        chosen_account = self.manager.ids.chooseaccount.chosen_account
        account_id = self.manager.ids.chooseaccount.account_id

        if self.manager.ids.mainmenu.desired_script == 1:
            automotive_template = self.manager.ids.choosesystemsingle.auto_template
            system_id = self.manager.ids.choosesystemsingle.system_id
            full_history = self.manager.ids.choosesystemsingle.full_history
            # So in order to run this app on pycharm we need the desktop version of this path, the actual app uses the file
            # which is already located in the same folder of the .exe
            # asset_info = pd.read_excel(desktop + '\\asset_info.xlsx').reset_index(drop=True)
            asset_info = pd.read_excel(my_documents + '\\Smart Tools\\asset_info.xlsx').reset_index(drop=True)
            self.initialize_thread(asset_info, SystemBuilder.sensor_assignment, "System Builder", desktop,
                                   session, account_id, system_id, full_history, asset_info, automotive_template,
                                   lambda: Clock.schedule_once(self.update_bar))
        elif self.manager.ids.mainmenu.desired_script == 2:
            avg_days = self.manager.ids.choosegroupmulti.avg_days
            system_information = self.manager.ids.choosegroupmulti.system_information
            self.initialize_thread(system_information, HeatMap.heat_map, "Heat Map", session, desktop, account_id,
                                   system_information, avg_days, lambda: Clock.schedule_once(self.update_bar))
        elif self.manager.ids.mainmenu.desired_script == 3:
            start_time = self.manager.ids.choosegroupmulti.start_time
            end_time = self.manager.ids.choosegroupmulti.end_time
            date_excel1 = self.manager.ids.choosegroupmulti.date_excel1
            date_excel2 = self.manager.ids.choosegroupmulti.date_excel2
            system_information = self.manager.ids.choosegroupmulti.system_information
            system_list = system_information['Name'].drop_duplicates(keep='first', inplace=False).reset_index(drop=True)
            self.initialize_thread(system_list, DamageAccumulationCalculation.da_calculation,
                                   "Damage Accumulation Calculation", self.manager, session, desktop, start_time,
                                   end_time, date_excel1, date_excel2, system_list, system_information,
                                   self.manager.ids.choosegroupmulti.asset_class_info, chosen_account,
                                   lambda: Clock.schedule_once(self.update_bar))
        elif self.manager.ids.mainmenu.desired_script == 4:
            system_information = self.manager.ids.choosegroupmulti.system_information
            self.initialize_thread(system_information, AlarmLevelSetter.gather_ov_alarms, "Alarm Level Setter", session,
                                   desktop, my_documents, system_information, lambda: Clock.schedule_once(self.update_bar))
        elif self.manager.ids.mainmenu.desired_script == 5:
            if self.manager.ids.choosegroupmulti.day_or_hour == 'day':
                # this is the data point code, it uses a heavily edited version of the time range code in general_functions
                start_time = self.manager.ids.choosegroupmulti.start_time
                date_list = [format(start_time + timedelta(days=a), '%m-%d-%Y') for a in
                             range(0, self.manager.ids.choosegroupmulti.specified_daily_interval)]
                start_time = start_time.astimezone(App.get_running_app().utc)
                date_excel1 = self.manager.ids.choosegroupmulti.date_excel1
                date_excel2 = self.manager.ids.choosegroupmulti.date_excel2
                system_information = self.manager.ids.choosegroupmulti.system_information
                self.initialize_thread(date_list, DataPointTransmission.data_point_daily, "Data Point Code",
                                       session, desktop, start_time, date_excel1, date_excel2, system_information,
                                       chosen_account, date_list, lambda: Clock.schedule_once(self.update_bar))
            elif self.manager.ids.choosegroupmulti.day_or_hour == 'hour':
                # the hourly code uses slightly different variables
                specified_hourly_interval = self.manager.ids.choosegroupmulti.specified_hourly_interval
                starting_hour = self.manager.ids.choosegroupmulti.starting_hour
                start_time = self.manager.ids.choosegroupmulti.start_time
                if self.manager.ids.choosegroupmulti.specified_daily_interval == 0:
                    date_list = [format(start_time, '%m-%d-%Y')]
                elif self.manager.ids.choosegroupmulti.specified_daily_interval > 0:
                    date_list = [format(start_time + timedelta(days=a), '%m-%d-%Y') for a in
                                 range(0, self.manager.ids.choosegroupmulti.specified_daily_interval)]
                date_hourly_list = [format(start_time + timedelta(hours=a),
                                           '%H:%M') for a in range(0, specified_hourly_interval)]
                start_time = start_time.astimezone(App.get_running_app().utc)
                date_excel1 = self.manager.ids.choosegroupmulti.date_excel1
                date_excel2 = self.manager.ids.choosegroupmulti.date_excel2
                system_information = self.manager.ids.choosegroupmulti.system_information
                self.initialize_thread(date_list, DataPointTransmission.data_point_hourly, "Data Point Code",
                                       session, desktop, start_time, date_excel1, date_excel2, starting_hour,
                                       system_information, chosen_account, date_list, date_hourly_list,
                                       lambda: Clock.schedule_once(self.update_bar))
        elif self.manager.ids.mainmenu.desired_script == 6:
            system_information = self.manager.ids.choosegroupmulti.system_information
            self.initialize_thread(system_information, SensorAudit.sensor_audit, "Sensor Audit Code",
                                   session, desktop, chosen_account, system_information,
                                   lambda: Clock.schedule_once(self.update_bar))

    def update_bar(self, dt=None):
        # This code controls the progress bar updating. It runs in the same thread as the main thread (gui)
        self.manager.ids.progress.ids.pb.value += 1
        self.manager.ids.progress.ids.pb_label.text = \
            'Progress: {}/{}\n{}%'.format(int(self.manager.ids.progress.ids.pb.value),
                                          self.manager.ids.progress.ids.pb.max,
                                          int(100*int(self.manager.ids.progress.ids.pb.value)/
                                              int(self.manager.ids.progress.ids.pb.max)))
        if self.manager.ids.progress.ids.pb.value == self.manager.ids.progress.ids.pb.max and \
            self.manager.ids.mainmenu.desired_script == 4:
            self.manager.current = 'AlarmLevelsCheck'
        elif self.manager.ids.progress.ids.pb.value == self.manager.ids.progress.ids.pb.max:
            layout = GridLayout(cols=1, padding=10)
            popupLabel = Label(text="Process Completed Successfully")
            ExitButton = Button(text='Exit', size_hint=(1, 0.25))
            MainMenuButton = Button(text='Main Menu', size_hint=(1, 0.25))
            layout.add_widget(popupLabel)
            layout.add_widget(ExitButton)
            layout.add_widget(MainMenuButton)
            popup = Popup(title='Done', content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
            ExitButton.bind(on_press=popup.dismiss, on_release=lambda a: self.exit())
            MainMenuButton.bind(on_press=popup.dismiss, on_release=lambda a: self.mainmenu())
            popup.open()
        else:
            pass


# Need progress screen 2 for scripts that have two parts (2 loading bars)
class ProgressScreen2(Screen):
    def __init__(self, **kwargs):
        super(ProgressScreen2, self).__init__(**kwargs)
        self.q = Queue()
        self.results = []
        self.current_thread = None

    def setup(self):
        pass

    def exit(self):
        App.get_running_app().stop()

    def mainmenu(self):
        self.manager.ids.chooseaccount.clear_account_data()
        self.manager.ids.choosesystemsingle.system_id = []
        self.manager.ids.choosesystemsingle.full_history = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemsingle.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.choosesystemmulti.system_names = []
        self.manager.ids.choosesystemmulti.system_ids = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.data = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.layout_manager.selected_nodes = []
        self.manager.ids.choosesystemmulti.ids.rv_choosesystem.refresh_from_data()
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.data = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.layout_manager.selected_nodes = []
        self.manager.ids.choosegroupmulti.current_system_name = []
        self.manager.ids.choosegroupmulti.current_system_number = 0
        self.manager.ids.choosegroupmulti.group_ids = []
        self.manager.ids.choosegroupmulti.group_data = []
        self.manager.ids.choosegroupmulti.group_system_names = []
        self.manager.ids.choosegroupmulti.ids.rv_choosegroup.refresh_from_data()
        self.manager.ids.progress.ids.pb.value = 0
        self.manager.ids.progress2.ids.pb.value = 0
        self.current_thread = None
        self.manager.current = 'MainMenu'

    def initialize_thread(self, iterator, target, name, *args):
        self.manager.ids.progress2.ids.pb.max = len(iterator)
        self.manager.ids.progress2.ids.pb_label.text = 'Progress: {}/{}'.format(0, self.manager.ids.progress2.ids.pb.max)
        self.current_thread = ThreadWithReturnValue(target=target, name=name, args=args)
        self.current_thread.start()

    def begin_bar(self):
        session = App.get_running_app().session
        my_documents = App.get_running_app().my_documents
        if self.manager.ids.mainmenu.desired_script == 4:
            time_alarm = self.manager.ids.choosegroupmulti.time_in_alarm
            # So in order to run this app on pycharm we need the desktop version of this path, the actual app uses the file
            # which is already located in the same folder of the .exe
            # alarm_info = pd.read_excel(desktop + '\\Alarm Levels.xlsx').reset_index(drop=True)
            alarm_info = pd.read_excel(my_documents + '\\Smart Tools\\Alarm Levels.xlsx').reset_index(drop=True)
            self.initialize_thread(alarm_info, alarm_level_setter_functions.set_alarms, "Alarm Level Setter", session,
                                   alarm_info, time_alarm, lambda: Clock.schedule_once(self.update_bar))

    def update_bar(self, dt=None):
        self.manager.ids.progress2.ids.pb.value += 1
        self.manager.ids.progress2.ids.pb_label.text = \
            'Progress: {}/{}\n{}%'.format(int(self.manager.ids.progress2.ids.pb.value),
                                          self.manager.ids.progress2.ids.pb.max,
                                          int(100 * int(self.manager.ids.progress2.ids.pb.value) /
                                              int(self.manager.ids.progress2.ids.pb.max)))
        if self.manager.ids.progress2.ids.pb.value == self.manager.ids.progress2.ids.pb.max:
            layout = GridLayout(cols=1, padding=10)
            popupLabel = Label(text="Process Completed Successfully")
            ExitButton = Button(text='Exit', size_hint=(1, 0.25))
            MainMenuButton = Button(text='Main Menu', size_hint=(1, 0.25))
            layout.add_widget(popupLabel)
            layout.add_widget(ExitButton)
            layout.add_widget(MainMenuButton)
            popup = Popup(title='Done', content=layout, auto_dismiss=False, size_hint=(None, None), size=(400, 400))
            ExitButton.bind(on_press=popup.dismiss, on_release=lambda a: self.exit())
            MainMenuButton.bind(on_press=popup.dismiss, on_release=lambda a: self.mainmenu())
            popup.open()
        else:
            pass


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected


class ScreenManagerApp(App):
    # Initializing variables
    desktop = winshell.desktop()
    my_documents = winshell.my_documents()
    dirname = my_documents + '\\Smart Tools'
    local = tzlocal()  # This contains the local timezone
    utc = tzutc()  # This contains the utc timezone
    # Login
    session, sd_login = sendRequest.login()

    # First time setup
    def setup(self, dirname, dt=None):
        try:
            dirname = self.my_documents + '\\Smart Tools'
            os.mkdir(dirname)
        except FileExistsError:
            pass
        # Not sure if we need the permission error check here, my documents should be editable
        try:
            shutil.copy('version', dirname + '\\version')
            shutil.copy('asset_info.xlsx', dirname + '\\asset_info.xlsx')
        except PermissionError:
            pass

    def build(self):
        self.title = 'Smart Tools'
        Clock.schedule_once(lambda a: self.setup(self.dirname))
        return MyScreenManager()


if __name__ == '__main__':
    ScreenManagerApp().run()
