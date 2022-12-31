import general_functions


def get_time_range(manager):
    general_functions.entry_popup(title='Enter Average Length',
                                  message='Enter the number of days you want the signal strength data averaged over.',
                                  hint='Number of days',
                                  input_filter='int',
                                  manager=manager)
