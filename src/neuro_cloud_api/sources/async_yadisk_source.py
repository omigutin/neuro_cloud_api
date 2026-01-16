import yadisk
from pathlib import Path
from typing import Union, List

from .base_source import BaseSource
from .source_type import SourceType

class AsyncYadiskSource(BaseSource):
    """Асинхронный клиент Яндекс.Диска."""

    def __init__(self, token: str):
        super().__init__(token, source_type=SourceType.YANDEX_DISK)
        self.client = yadisk.AsyncClient(token=token)

    async def connect(self) -> bool:
        if await self.check_connection():
            self.is_connected = True
            return True
        return False

    async def check_connection(self) -> bool:
        try:
            return await self.client.check_token()
        except yadisk.exceptions.UnauthorizedError:
            return False

    async def list_directories(self, path: str = "/") -> List[str]:
        result = []
        async for item in self.client.listdir(path):
            if item["type"] == "dir":
                result.append(item["path"])
        return result

    async def download_file(self, remote_path: str, local_path: Union[str, Path]) -> bool:
        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            await self.client.download(remote_path, str(local_path))
            return True
        except Exception:
            return False

    async def upload_file(self, local_path: Union[str, Path], remote_path: str) -> bool:
        try:
            local_path = Path(local_path)
            if not local_path.exists():
                return False
            await self.client.upload(str(local_path), remote_path)
            return True
        except Exception:
            return False

    async def search_directories(self, name: str, path: str = "/") -> List[str]:
        result = []
        async for item in self.client.listdir(path):
            if item["type"] == "dir" and name.lower() in item["name"].lower():
                result.append(item["path"])
        return result

    async def disconnect(self):
        """Отключение от облачного хранилища."""
        if self.client:
            await self.client.close()
        self.client = None
        self.is_connected = False