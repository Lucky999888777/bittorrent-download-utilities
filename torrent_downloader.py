#!/usr/bin/env python3
"""
torrent_downloader.py
---------------------
Downloads the content of every .torrent file found in a folder, saving the
downloaded data into that same folder. File/folder names come straight from
the torrent itself, so they match exactly what the torrent defines.

Usage:
    python torrent_downloader.py "C:\\path\\to\\folder"
    python torrent_downloader.py /path/to/torrents
    python torrent_downloader.py            (you will be asked for the folder)

Requires:
    pip install libtorrent
"""

import argparse
import sys
import time
from pathlib import Path

try:
    import libtorrent as lt
except ImportError:
    sys.exit(
        "The 'libtorrent' module is not installed.\n"
        "Install it with:  pip install libtorrent"
    )

STATE_NAMES = [
    "queued", "checking files", "downloading metadata", "downloading",
    "finished", "seeding", "allocating", "checking resume data",
]


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:6.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:6.1f} PB"


def format_eta(seconds: float) -> str:
    """Turn a number of seconds into e.g. '1h 05m 12s'."""
    seconds = int(seconds)
    if seconds >= 99 * 3600:
        return "--"
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def make_session() -> "lt.session":
    settings = {
        "listen_interfaces": "0.0.0.0:6881,[::]:6881",
        "enable_dht": True,
        "enable_lsd": True,
        "enable_upnp": True,
        "enable_natpmp": True,
        "dht_bootstrap_nodes": (
            "router.bittorrent.com:6881,"
            "router.utorrent.com:6881,"
            "dht.transmissionbt.com:6881"
        ),
        "alert_mask": lt.alert.category_t.error_notification
        | lt.alert.category_t.status_notification,
    }
    return lt.session(settings)


def download_one(session, torrent_file: Path, save_dir: Path) -> bool:
    """Download a single torrent. Returns True when complete."""
    try:
        info = lt.torrent_info(str(torrent_file))
    except Exception as exc:  # corrupt / not a real torrent file
        print(f"  ! Could not read {torrent_file.name}: {exc}")
        return False

    print(f"\n=== {torrent_file.name} ===")
    print(f"  Content name : {info.name()}")
    print(f"  Total size   : {human_size(info.total_size()).strip()}")
    print(f"  Saving to    : {save_dir}")

    params = lt.add_torrent_params()
    params.ti = info
    params.save_path = str(save_dir)
    handle = session.add_torrent(params)

    # Smoothed (moving-average) download speed so the ETA doesn't jump around.
    # It is recalculated every second from the live speed, so it stays dynamic.
    smooth_rate = 0.0
    alpha = 0.2  # higher = reacts faster to speed changes, lower = steadier

    try:
        while True:
            status = handle.status()

            if status.errc.value() != 0:
                print(f"\n  ! Error: {status.errc.message()}")
                session.remove_torrent(handle)
                return False

            if status.is_finished:
                print(f"\r  Progress: 100.0%  -  download complete!{' ' * 40}")
                session.remove_torrent(handle)
                return True

            state = STATE_NAMES[int(status.state)] if int(status.state) < len(STATE_NAMES) else "?"

            # Update the smoothed speed (first real sample seeds the average)
            current_rate = float(status.download_rate)
            if smooth_rate == 0.0:
                smooth_rate = current_rate
            else:
                smooth_rate = alpha * current_rate + (1 - alpha) * smooth_rate

            # ETA = bytes still needed / smoothed speed
            remaining = max(status.total_wanted - status.total_wanted_done, 0)
            if smooth_rate >= 1.0 and remaining > 0:
                eta_text = format_eta(remaining / smooth_rate)
            else:
                eta_text = "--"

            print(
                f"\r  {status.progress * 100:5.1f}% | "
                f"down {human_size(status.download_rate)}/s | "
                f"up {human_size(status.upload_rate)}/s | "
                f"peers {status.num_peers:3d} | "
                f"ETA {eta_text:<12} | {state:<22}",
                end="",
                flush=True,
            )
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Stopped by user. Re-run the script later to resume.")
        session.remove_torrent(handle)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download all .torrent files in a folder into that same folder."
    )
    parser.add_argument("folder", nargs="?", help="Folder containing .torrent files")
    args = parser.parse_args()

    folder_str = args.folder or input("Enter the folder path containing .torrent files: ").strip().strip('"')
    folder = Path(folder_str).expanduser().resolve()

    if not folder.is_dir():
        sys.exit(f"Not a valid folder: {folder}")

    torrents = sorted(folder.glob("*.torrent"))
    if not torrents:
        sys.exit(f"No .torrent files found in {folder}")

    print(f"Found {len(torrents)} torrent file(s) in {folder}")
    session = make_session()

    done, failed = [], []
    try:
        for tfile in torrents:
            ok = download_one(session, tfile, folder)
            (done if ok else failed).append(tfile.name)
    except KeyboardInterrupt:
        print("\nInterrupted.")

    print("\n---------- Summary ----------")
    print(f"Completed: {len(done)}")
    for name in done:
        print(f"  ✓ {name}")
    if failed:
        print(f"Failed/incomplete: {len(failed)}")
        for name in failed:
            print(f"  ✗ {name}")


if __name__ == "__main__":
    main()
