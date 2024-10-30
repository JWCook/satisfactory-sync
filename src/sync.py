from .api import SatisfactoryAPIClient
from .storage import StorageClient


# WIP
def backup_save():
    """Get latest save contents from the Satisfactory server and upload to remote storage"""
    client = SatisfactoryAPIClient()
    save_content = client.get_save()

    storage = StorageClient()
    storage.upload_save(save_content)


if __name__ == "__main__":
    backup_save()
