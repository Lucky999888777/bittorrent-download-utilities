#!/usr/bin/env python3
"""
Magnet link downloader.

Usage:
    python magnet_downloader.py                      # prompts for input
    python magnet_downloader.py "<magnet>" "<folder>"

Requires:
    pip install libtorrent
"""

import os
import sys
import time

try:
    import libtorrent as lt
except ImportError:
    sys.exit("libtorrent is not installed. Run:  pip install libtorrent")


STATE_NAMES = [
    "queued", "checking", "downloading metadata", "downloading",
    "finished", "seeding", "allocating", "checking resume data",
]


def fmt_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def download_magnet(magnet_link: str, save_dir: str) -> None:
    save_dir = os.path.abspath(os.path.expanduser(save_dir))
    os.makedirs(save_dir, exist_ok=True)

    session = lt.session({
        "listen_interfaces": "0.0.0.0:6881",
        "enable_dht": True,
        "enable_lsd": True,
        "enable_upnp": True,
        "enable_natpmp": True,
        "dht_bootstrap_nodes": (
            "router.bittorrent.com:6881,"
            "router.utorrent.com:6881,"
            "dht.transmissionbt.com:6881"
        ),
    })

    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = save_dir
    handle = session.add_torrent(params)

    print("Fetching metadata from peers...")
    while not handle.status().has_metadata:
        time.sleep(1)

    info = handle.torrent_file()
    print(f"Name : {info.name()}")
    print(f"Size : {fmt_size(info.total_size())}")
    print(f"Saving to: {save_dir}\n")

    try:
        while True:
            s = handle.status()
            state = STATE_NAMES[int(s.state)] if int(s.state) < len(STATE_NAMES) else str(s.state)
            print(
                f"\r{s.progress * 100:6.2f}% | {state:<12} | "
                f"down {fmt_size(s.download_rate)}/s | "
                f"up {fmt_size(s.upload_rate)}/s | "
                f"peers {s.num_peers:<4}",
                end="",
                flush=True,
            )
            if s.is_finished or s.state in (lt.torrent_status.finished, lt.torrent_status.seeding):
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted. Partial download left in the folder.")
        return

    print(f"\n\nDownload complete! Files saved in: {save_dir}")


def main() -> None:
    if len(sys.argv) >= 3:
        magnet, folder = sys.argv[1], sys.argv[2]
    else:
        magnet = input("Paste magnet link: ").strip().strip('"').strip("'")
        folder = input("Enter download folder path: ").strip().strip('"').strip("'")

    if not magnet.startswith("magnet:?"):
        sys.exit("Invalid magnet link (must start with 'magnet:?').")
    if not folder:
        sys.exit("Please provide a download folder.")

    download_magnet(magnet, folder)


if __name__ == "__main__":
    main()
