"""Basic wrappers for some Satisfactory API endpoints"""
import os
import time

from requests import RequestException, Response, Session

HOST = 'satisfactory.jkcook.casa'
PORT = 7777
BASE_URL = f'https://{HOST}:{PORT}/api/v1'
PASSWORD = os.environ.get('SATISFACTORY_PASSWORD')
DEFAULT_SAVE = 'satisfactory_backup'
SESSION = Session()


def api_request(function: str, data: str | dict = None, token: str = None) -> Response:
    """Make an (optionally authenticated) API request"""
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    payload = {'function': function}
    if data:
        payload['data'] = data

    response = SESSION.post(
        BASE_URL,
        headers=headers,
        json=payload,
        verify=False,
    )
    response.raise_for_status()
    return response


def get_token() -> str:
    response = api_request(
        'PasswordLogin',
        {'Password': PASSWORD, 'MinimumPrivilegeLevel': 'Administrator'},
    )
    return response.json()['data']['authenticationToken']


def save(token: str, save_name: str = DEFAULT_SAVE) -> Response:
    return api_request('SaveGame', {'SaveName': save_name}, token)


def get_save(token:str, save_name: str = DEFAULT_SAVE) -> bytes:
    save(token, save_name)
    response = api_request('DownloadSaveGame', {'SaveName': save_name}, token)
    return response.content


def health_check() -> bool:
    try:
        response = api_request('HealthCheck', {'ClientCustomData': ''})
        return response.json()['data']['health'] == 'healthy'
    except (RequestException, KeyError):
        return False


def get_state(token:str) -> dict:
    response = api_request('QueryServerState', token=token)
    return response.json()['data']['serverGameState']


def restart():
    """Cleanly restart the server"""
    token = get_token()
    save(token=token)
    # TODO: Way to check that the save is complete instead of sleep?
    time.sleep(15)
    # Shut down the server process and let the service manager restart it
    api_request('Shutdown', token=token)


if __name__ == '__main__':
    restart()
