import time
import base64
import json
from typing import Any

from requests import RequestException, Response, Session

from .config import CONFIG


class SatisfactoryAPIClient:
    """Basic wrapper class for some Satisfactory API endpoints"""

    def __init__(self):
        self.session = Session()
        # TODO: Refresh when expired (only needed for long-running processes; may not need yet)
        self.token = self.get_token()

    @property
    def token_role(self) -> str:
        return json.loads(base64.b64decode(self.token)).get("pl")

    def get_token(self) -> str:
        response = self.request(
            "PasswordLogin",
            {"Password": CONFIG.satisfactory_password, "MinimumPrivilegeLevel": "Administrator"},
        )
        return response.json()["data"]["authenticationToken"]

    def request(self, function: str, data: str | dict = None, token: str = None) -> Response:
        """Make an (optionally authenticated) API request"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {"function": function}
        if data:
            payload["data"] = data

        response = self.session.post(
            CONFIG.api_url,
            headers=headers,
            json=payload,
            verify=False,
        )
        response.raise_for_status()
        return response

    def save(self, save_name: str = CONFIG.save_name) -> Response:
        return self.request("SaveGame", {"SaveName": save_name}, self.token)

    def load(self, save_name: str = CONFIG.save_name) -> Response:
        return self.request("LoadGame", {"SaveName": save_name}, self.token)

    def get_save(self, save_name: str = CONFIG.save_name) -> bytes:
        """Get latest save contents"""
        self.save(save_name)
        response = self.request("DownloadSaveGame", {"SaveName": save_name}, token=self.token)
        return response.content

    # WIP
    def upload_save(self, save_content: bytes, save_name: str, load: bool = False):
        """Upload save game file to the Dedicated Server"""
        params = {"SaveName": save_name, "LoadSaveGame": load, "EnableAdvancedGameSettings": False}
        files = {
            "data": ("data", json.dumps(params), "application/json"),
            "saveGameFile": ("saveGameFile", save_content, "application/octet-stream"),
        }
        response = self.session.post(
            CONFIG.api_url,
            json={"function": "UploadSaveGame"},
            headers={"Authorization": f"Bearer {self.token}"},
            files=files,
            verify=False,
        )
        response.raise_for_status()
        return response

    def describe_saves(self):
        """Get info of all saves. Currently assumes just one session.
        Example response:
        [ {
            'saveVersion': 46,
            'buildVersion': 372858,
            'saveName': 'Hoxxes III_autosave_2',
            'saveLocationInfo': 'SLI_Server',
            'mapName': 'Persistent_Level',
            'mapOptions': '',
            'sessionName': 'Hoxxes III',
            'playDurationSeconds': 159762,
            'saveDateTime': '2024.10.30-00.52.41',
            'isModdedSave': False,
            'isEditedSave': False,
            'isCreativeModeEnabled': False
        }, ... ]
        """
        response = self.request("EnumerateSessions", token=self.token)
        return response.json()["data"]["sessions"][0]["SaveHeaders"]

    def health_check(self) -> bool:
        try:
            response = self.request("HealthCheck", {"ClientCustomData": ""})
            return response.json()["data"]["health"] == "healthy"
        except (RequestException, KeyError):
            return False

    def get_state(self) -> dict[str, Any]:
        """Get the current server state. Example response:
        {
            'activeSessionName': 'Hoxxes III',
            'numConnectedPlayers': 0,
            'playerLimit': 6,
            'techTier': 4,
            'activeSchematic': "/Script/Engine.BlueprintGeneratedClass'/Game/FactoryGame/Schematics/Progression/Schematic_4-1.Schematic_4-1_C'",
            'gamePhase': "/Script/FactoryGame.FGGamePhase'/Game/FactoryGame/GamePhases/GP_Project_Assembly_Phase_1.GP_Project_Assembly_Phase_1'",
            'isGameRunning': True,
            'totalGameDuration': 159758,
            'isGamePaused': True,
            'averageTickRate': 29.768978118896484,
            'autoLoadSessionName': 'Hoxxes III'
        }
        """
        response = self.request("QueryServerState", token=self.token)
        return response.json()["data"]["serverGameState"]

    def get_server_options(self):
        """Get the current server options. Example response:
        {
            'FG.DSAutoPause': 'True',
            'FG.DSAutoSaveOnDisconnect': 'True',
            'FG.AutosaveInterval': '600.0',
            'FG.ServerRestartTimeSlot': '600.0',
            'FG.SendGameplayData': 'True',
            'FG.NetworkQuality': '1'
        }
        """
        response = client.request("GetServerOptions", token=client.token)
        return response.json()["data"]["serverOptions"]

    def set_autoload_session(self, save_name: str = CONFIG.save_name):
        return self.request("SetAutoLoadSessionName", {"SessionName": save_name}, token=self.token)

    def restart(self):
        """Shut down the server process and let the service manager restart it"""
        self.request("Shutdown", token=self.token)

    def test_save_restart(self):
        """Save and cleanly restart the server"""
        self.save()
        time.sleep(15)  # TODO: Way to check that the save is complete instead of sleep?
        self.restart()


if __name__ == "__main__":
    client = SatisfactoryAPIClient()
    SatisfactoryAPIClient.test_save_restart()
