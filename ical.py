#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from icalendar import Calendar, Event


DATA = {
    'Gelbe Tonne': ['27.01.2021', '01.03.2021', '30.03.2021', '30.04.2021', '09.06.2021',
                    '06.07.2021', '04.08.2021', '03.09.2021', '05.10.2021', '02.11.2021',
                    '30.11.2021', '29.12.2021'],
    'Papiertonne': ['12.01.2021', '11.02.2021', '12.03.2021', '15.04.2021',
                    '18.05.2021', '21.06.2021', '19.07.2021', '17.08.2021', '17.09.2021',
                    '18.10.2021', '15.11.2021', '13.12.2021'],
    'Sperrmüll': ['27.01.2021', '20.07.2021']
}


def create_ical(data):
    cal = Calendar()

    for event_name in data:
        for event_date in data[event_name]:
            event = Event()
            event.add('summary', event_name)
            event.add('dtstart', datetime.strptime(
                event_date, '%d.%m.%Y').date())
            cal.add_component(event)

    return cal


def export_to_file(cal, target_path='out/', filename='output.ics'):
    Path(target_path).mkdir(parents=True, exist_ok=True)
    with open(target_path + filename, 'wb') as f:
        f.write(cal.to_ical())


if __name__ == "__main__":
    ical = create_ical(DATA)
    export_to_file(ical)
