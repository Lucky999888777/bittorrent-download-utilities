# BitTorrent Download Utilities

Two interactive command-line tools built with the Python `libtorrent` bindings:

- `magnet_downloader.py` downloads a torrent from a magnet URI to a folder you choose. It prompts for the magnet URI and destination when run without arguments, or accepts both as positional arguments.
- `torrent_downloader.py` finds every lowercase `.torrent` file directly inside a chosen folder and downloads each torrent's contents into that same folder. Use `--help` to see its command-line usage.

## Requirements

- Python 3
- The `libtorrent` Python package. Availability of prebuilt packages depends on your Python version and operating system.

Install the dependency from PowerShell or another terminal in this folder:

```powershell
python -m pip install -r requirements.txt
```

If `python` is not available on Windows, use the Python launcher:

```powershell
py -m pip install -r requirements.txt
```

## Usage

### Download from a magnet link

Interactive prompts:

```powershell
python magnet_downloader.py
```

Or provide the magnet URI and destination folder:

```powershell
python magnet_downloader.py "magnet:?xt=urn:btih:..." "C:\path\to\downloads"
```

The script waits for peers to provide torrent metadata before showing the download progress.

### Download `.torrent` files from a folder

Pass the folder as an argument:

```powershell
python torrent_downloader.py "C:\path\to\torrent-files"
```

Or run it without an argument and enter the folder when prompted:

```powershell
python torrent_downloader.py
```

The script processes each `.torrent` file found at the folder's top level. It saves payload data into that same folder; it does not search subfolders.

## Networking, privacy, and responsible use

These scripts use BitTorrent peer-to-peer networking, including DHT and local peer discovery. They enable peer connections and use port `6881`; the magnet downloader also enables UPnP and NAT-PMP. BitTorrent clients can upload pieces to other peers while downloading, and may continue sharing while active. Your public IP address can be visible to peers in a swarm. Network behavior also depends on the torrent and libtorrent settings.

Use these tools only for content you have the right to download and share, and follow the rules that apply to your network and location. Do not run downloads inside this source-code folder. Use a separate data folder, since torrent payloads can contain large or private files.

## GitHub notes

The included `.gitignore` excludes torrent metadata files, common download folders, and partial-download state. It cannot identify every possible payload filename, so keep downloaded content outside the repository and inspect staged files before publishing. No license is included; choose and add one if you want to grant others permission to reuse the code.
