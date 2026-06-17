import asyncio
import os
from typing import Any, Dict, List, Optional

import aiofiles
import paramiko
import smbclient


class VFSNode:
    def __init__(self, name: str, path: str, is_dir: bool, protocol: str = "local"):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.protocol = protocol  # "local", "sftp", "smb"


class VirtualFileSystem:
    def __init__(self):
        # Store active remote connections
        self.connections = {}

    def add_connection(self, conn_id: str, config: Dict[str, Any]):
        """
        config shape:
        {
            "protocol": "sftp" | "smb",
            "host": "192.168.1.100",
            "port": 22 | 445,
            "username": "user",
            "password": "password",  # optional
            "share_name": "logs"     # for SMB only
        }
        """
        self.connections[conn_id] = config

    def remove_connection(self, conn_id: str):
        if conn_id in self.connections:
            del self.connections[conn_id]

    def _parse_path(self, path: str):
        """
        Paths are expected to be either:
        - ./local/path
        - /local/path
        - vfs://[conn_id]/path
        """
        if path.startswith("vfs://"):
            parts = path[6:].split("/", 1)
            conn_id = parts[0]
            rel_path = "/" + parts[1] if len(parts) > 1 else "/"
            if conn_id in self.connections:
                return self.connections[conn_id], rel_path, conn_id
            raise ValueError(f"Unknown virtual connection: {conn_id}")
        return {"protocol": "local"}, path, None

    async def list_dir(self, path: str) -> List[VFSNode]:
        config, rel_path, conn_id = self._parse_path(path)
        protocol = config["protocol"]

        if protocol == "local":
            return await self._list_local(path)
        elif protocol == "sftp":
            # SFTP is generally blocking in paramiko, so we run it in a thread
            return await asyncio.to_thread(self._list_sftp, config, rel_path, conn_id)
        elif protocol == "smb":
            return await asyncio.to_thread(self._list_smb, config, rel_path, conn_id)

        return []

    async def read_lines(
        self, path: str, start_line: int = 1, max_lines: int = 100
    ) -> List[str]:
        config, rel_path, conn_id = self._parse_path(path)
        protocol = config["protocol"]

        if protocol == "local":
            return await self._read_local(path, start_line, max_lines)
        elif protocol == "sftp":
            return await asyncio.to_thread(
                self._read_sftp, config, rel_path, start_line, max_lines
            )
        elif protocol == "smb":
            return await asyncio.to_thread(
                self._read_smb, config, rel_path, start_line, max_lines
            )
        return []

    # --- Local Implementations ---
    async def _list_local(self, path: str) -> List[VFSNode]:
        nodes = []
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                nodes.append(
                    VFSNode(
                        name=item,
                        path=full_path,
                        is_dir=os.path.isdir(full_path),
                        protocol="local",
                    )
                )
        except Exception as e:
            print(f"Error listing local dir: {e}")
            raise e
        return nodes

    async def _read_local(
        self, path: str, start_line: int, max_lines: int
    ) -> List[str]:
        lines = []
        try:
            async with aiofiles.open(
                path, mode="r", encoding="utf-8", errors="replace"
            ) as f:
                current = 0
                async for line in f:
                    current += 1
                    if current >= start_line:
                        lines.append(line.strip())
                    if len(lines) >= max_lines:
                        break
        except Exception as e:
            raise e
        return lines

    # --- SFTP Implementations ---
    def _get_sftp_client(self, config):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Determine auth method
        kwargs = {
            "hostname": config["host"],
            "port": int(config.get("port", 22)),
            "username": config.get("username", "anonymous"),
            "timeout": 5,
        }

        if config.get("password"):
            kwargs["password"] = config["password"]

        ssh.connect(**kwargs)
        return ssh, ssh.open_sftp()

    def _list_sftp(self, config, path, conn_id) -> List[VFSNode]:
        ssh, sftp = None, None
        try:
            ssh, sftp = self._get_sftp_client(config)
            if not path or path == "/":
                path = "."

            nodes = []
            for entry in sftp.listdir_attr(path):
                import stat

                is_dir = stat.S_ISDIR(entry.st_mode)

                # Construct virtual path
                base = f"vfs://{conn_id}"
                if path == ".":
                    vpath = f"{base}/{entry.filename}"
                else:
                    clean_path = path.rstrip("/")
                    vpath = f"{base}{clean_path}/{entry.filename}"

                nodes.append(
                    VFSNode(
                        name=entry.filename, path=vpath, is_dir=is_dir, protocol="sftp"
                    )
                )
            return nodes
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()

    def _read_sftp(self, config, path, start_line, max_lines) -> List[str]:
        ssh, sftp = None, None
        lines = []
        try:
            ssh, sftp = self._get_sftp_client(config)
            with sftp.open(path, "r") as f:
                current = 0
                for line in f:
                    current += 1
                    if current >= start_line:
                        try:
                            lines.append(line.decode("utf-8", errors="replace").strip())
                        except AttributeError:
                            lines.append(line.strip())
                    if len(lines) >= max_lines:
                        break
            return lines
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()

    # --- SMB Implementations ---
    def _register_smb(self, config):
        username = config.get("username")
        password = config.get("password")

        if not username:
            # Guest access
            smbclient.register_session(config["host"], username="Guest", password="")
        else:
            smbclient.register_session(
                config["host"], username=username, password=password
            )

    def _list_smb(self, config, path, conn_id) -> List[VFSNode]:
        self._register_smb(config)
        share = config["share_name"]

        # e.g., \\192.168.1.100\logs\path
        smb_path = rf"\\{config['host']}\{share}\{path.lstrip('/')}"
        smb_path = smb_path.replace("/", "\\")

        nodes = []
        for entry in smbclient.scandir(smb_path):
            is_dir = entry.is_dir()

            base = f"vfs://{conn_id}"
            clean_path = path.rstrip("/")
            if clean_path == "" or clean_path == "/":
                vpath = f"{base}/{entry.name}"
            else:
                vpath = f"{base}{clean_path}/{entry.name}"

            nodes.append(
                VFSNode(name=entry.name, path=vpath, is_dir=is_dir, protocol="smb")
            )
        return nodes

    def _read_smb(self, config, path, start_line, max_lines) -> List[str]:
        self._register_smb(config)
        share = config["share_name"]
        smb_path = rf"\\{config['host']}\{share}\{path.lstrip('/')}"
        smb_path = smb_path.replace("/", "\\")

        lines = []
        with smbclient.open_file(
            smb_path, mode="r", encoding="utf-8", errors="replace"
        ) as f:
            current = 0
            for line in f:
                current += 1
                if current >= start_line:
                    lines.append(line.strip())
                if len(lines) >= max_lines:
                    break
        return lines


vfs = VirtualFileSystem()
