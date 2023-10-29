import os.path
import datetime
from typing import Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials_source_path = os.path.join('warranty-manager-flask-app', 'env_files')

class EventParams:
    summary: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    start_date_input: Optional[str] = None
    end_date_input: Optional[str] = None

    def __init__(self, summary=None, location=None, description=None, start_date_input=None, end_date_input=None,):
        self.summary = summary
        self.location = location
        self.description = description
        self.start_date_input = start_date_input
        self.end_date_input = end_date_input


def create_token(google_credentials, token_pickle):
    creds = None

    if os.path.exists(token_pickle):
        creds = Credentials.from_authorized_user_file(token_pickle, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file=google_credentials, scopes=SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_pickle, 'w') as token:
            token.write(creds.to_json())

        return creds


def verify_token(credentials_source):
    token_pickle = os.path.join(credentials_source, r'read_calendar_token.pickle')
    google_credentials = os.path.join(credentials_source, r'credentials.json')
    if os.path.exists(token_pickle):
        creds = Credentials.from_authorized_user_file(token_pickle, SCOPES)
    else:
        creds = create_token(google_credentials, token_pickle)

    return creds


def parse_dict_list(dict_list):
    text = ""
    for dict_item in dict_list:
        text += f"* {dict_item['summary']} - {dict_item['start']['dateTime']} - {dict_item['end']['dateTime']}\n"

    return text


def create_events(event_params, creds):
    event_body = event_parser(params=event_params)
    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId='primary', body=event_body).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    
    return event


def event_parser(params: EventParams) -> dict:
    summary = params.summary or "New Event"
    description = params.description or "Event description"

    default_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone()
    default_timezone_str = str(default_timezone)
    default_timezone_datetime = default_timezone_str.split(" ")

    default_date = default_timezone_datetime[0]
    default_time = default_timezone_datetime[1].split("+")[0].split(".")[0]
    default_tz = default_timezone_datetime[1].split("+")[1]

    start_date_input = params.start_date_input or default_date
    start_date = start_date_input

    start_time_input = default_time
    start_time = start_time_input

    end_date_input = params.end_date_input or default_date
    end_date = end_date_input

    end_datetime = default_timezone + datetime.timedelta(hours=1)
    end_time = end_datetime.strftime('%H:%M:%S')

    event = {
        "summary": summary,
        "location": '',
        "description": description,
        "colorId": 6,
        "start": {"dateTime": f"{start_date}T{start_time}+{default_tz}", "timeZone": "Asia/Jerusalem"},
        "end": {"dateTime": f"{end_date}T{end_time}+{default_tz}", "timeZone": "Asia/Jerusalem"},
        "recurrence": [f"RRULE:FREQ=DAILY;COUNT=1"],
    }
    return event


def main():
    creds = verify_token(credentials_source_path)

    summary = "Warranty Checkout2"
    description = ("Warranty will expire in [x] days at [expiration_date]. We recommend "
                   "to check [device name] for issues and use warranty if necessary2.")
    start_date_input = "2023-09-20"
    end_date_input = "2023-09-20"
    
    params = EventParams(summary=summary, start_date_input=start_date_input, end_date_input=end_date_input, description=description)
    create_events(params, creds)


if __name__ == '__main__':
    main()
