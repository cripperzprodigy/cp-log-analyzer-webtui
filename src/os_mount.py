import platform
import subprocess
import os

def mount_smb(host: str, share_name: str, mount_point: str, username: str = None, password: str = None) -> str:
    """
    Attempts to mount an SMB share at the OS level.
    Returns an empty string on success, or an error message on failure.
    """
    sys_plat = platform.system().lower()
    
    try:
        if sys_plat == "windows":
            # Windows: net use Z: \\host\share /user:username password
            cmd = ["net", "use", mount_point, fr"\\{host}\{share_name}"]
            if username:
                cmd.extend([f"/user:{username}"])
            if password:
                cmd.append(password)
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"Windows Mount Error: {result.stderr or result.stdout}"
                
        elif sys_plat == "linux":
            # Linux: sudo mount -t cifs -o username=u,password=p //host/share /mnt/point
            # Note: This usually requires sudo!
            os.makedirs(mount_point, exist_ok=True)
            cmd = ["mount", "-t", "cifs", f"//{host}/{share_name}", mount_point]
            
            opts = []
            if username:
                opts.append(f"username={username}")
                if password:
                    opts.append(f"password={password}")
            else:
                opts.append("guest")
                
            if opts:
                cmd.extend(["-o", ",".join(opts)])
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"Linux Mount Error: {result.stderr or result.stdout}. (Note: May require root/sudo)"
                
        elif sys_plat == "darwin":
            # macOS: mount_smbfs //user:pass@host/share /Volumes/mnt
            os.makedirs(mount_point, exist_ok=True)
            auth_str = ""
            if username:
                auth_str = username
                if password:
                    auth_str += f":{password}"
                auth_str += "@"
            
            cmd = ["mount_smbfs", f"//{auth_str}{host}/{share_name}", mount_point]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"macOS Mount Error: {result.stderr or result.stdout}"
        else:
            return f"Unsupported OS for mounting: {sys_plat}"
            
        return ""
    except Exception as e:
        return f"Exception during mount: {str(e)}"

def unmount(mount_point: str) -> str:
    """Unmounts the previously OS-mounted drive."""
    sys_plat = platform.system().lower()
    try:
        if sys_plat == "windows":
            cmd = ["net", "use", mount_point, "/delete"]
        elif sys_plat == "darwin":
            cmd = ["umount", mount_point]
        else:
            # Linux
            cmd = ["umount", mount_point]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Unmount Error: {result.stderr or result.stdout}"
        return ""
    except Exception as e:
        return f"Exception during unmount: {str(e)}"
