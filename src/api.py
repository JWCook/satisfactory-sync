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

    def get_save(self, save_name: str = CONFIG.save_name) -> bytes:
        """Get latest save contents"""
        self.save(save_name)
        response = self.request("DownloadSaveGame", {"SaveName": save_name}, token=self.token)
        return response.content

    def health_check(self) -> bool:
        try:
            response = self.request("HealthCheck", {"ClientCustomData": ""})
            return response.json()["data"]["health"] == "healthy"
        except (RequestException, KeyError):
            return False

    def get_state(self) -> dict[str, Any]:
        response = self.request("QueryServerState", token=self.token)
        return response.json()["data"]["serverGameState"]

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
