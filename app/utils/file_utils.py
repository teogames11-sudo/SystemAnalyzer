"""
File operations: delete to recycle bin or permanently.
"""
import os
import shutil
from pathlib import Path

try:
    import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


def delete_to_trash(paths: list[str]) -> tuple[int, list[str]]:
    """Move files to recycle bin. Returns (success_count, failed_paths)."""
    success = 0
    failed = []
    for path in paths:
        try:
            if HAS_SEND2TRASH:
                send2trash.send2trash(path)
            else:
                os.remove(path)
            success += 1
        except Exception as e:
            failed.append(f"{path}: {e}")
    return success, failed


def delete_permanent(paths: list[str]) -> tuple[int, list[str]]:
    """Permanently delete files/directories. Returns (success_count, failed_paths)."""
    success = 0
    failed = []
    for path in paths:
        try:
            p = Path(path)
            if p.is_file() or p.is_symlink():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            success += 1
        except Exception as e:
            failed.append(f"{path}: {e}")
    return success, failed


def get_recycle_bin_size() -> tuple[int, int]:
    """Returns (file_count, total_bytes) for recycle bin on all drives."""
    import ctypes
    total_size = 0
    total_count = 0
    try:
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase
                  if os.path.exists(f"{d}:\\")]
        for drive in drives:
            info = ctypes.create_string_buffer(1024)
            try:
                # SHQueryRecycleBin
                shell32 = ctypes.windll.shell32
                class SHQUERYRBINFO(ctypes.Structure):
                    _fields_ = [("cbSize", ctypes.c_ulong),
                                 ("i64Size", ctypes.c_longlong),
                                 ("i64NumItems", ctypes.c_longlong)]
                rb = SHQUERYRBINFO()
                rb.cbSize = ctypes.sizeof(rb)
                ret = shell32.SHQueryRecycleBinW(drive, ctypes.byref(rb))
                if ret == 0:
                    total_size += rb.i64Size
                    total_count += rb.i64NumItems
            except Exception:
                pass
    except Exception:
        pass
    return total_count, total_size


def empty_recycle_bin() -> bool:
    """Empty the recycle bin. Returns True on success."""
    try:
        import ctypes
        SHERB_NOCONFIRMATION = 0x00000001
        SHERB_NOPROGRESSUI = 0x00000002
        SHERB_NOSOUND = 0x00000004
        flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        return result == 0
    except Exception:
        return False
