"""Download the HDMA Africa DEM and flow-direction tiles from ScienceBase."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Code.utils.utility import load_config, resolve_path


DEM_ITEM_ID = "591f6d02e4b0ac16dbdde1c7"
FD_ITEM_ID = "591f6d0fe4b0ac16dbdde1cb"
UNITS = (
    "0",
    "1_1",
    "1_2",
    "1_3",
    "2",
    "3_1",
    "3_2",
    "3_3",
    "3_4",
    "4",
    "5_1",
    "5_2",
    "5_3",
    "5_4",
    "5_5",
    "6",
    "7",
    "8",
    "9",
)
SCIENCEBASE_FILE_URL = "https://www.sciencebase.gov/catalog/file/get/{item_id}?name={file_name}"
SCIENCEBASE_ITEM_JSON_URL = "https://www.sciencebase.gov/catalog/item/{item_id}?format=json"
USER_AGENT = "Mozilla/5.0 (Africa_Irrigation HDMA downloader)"


def _sciencebase_url(item_id: str, file_name: str) -> str:
    return SCIENCEBASE_FILE_URL.format(item_id=item_id, file_name=file_name)


def _open_url(url: str, proxy: str | None, timeout_s: int):
    opener = urllib.request.build_opener()
    if proxy:
        opener.add_handler(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return opener.open(request, timeout=timeout_s)


def _is_valid_zip(path: Path) -> bool:
    return path.exists() and zipfile.is_zipfile(path)


def _format_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _download_with_curl(
    curl_path: str,
    url: str,
    part_path: Path,
    proxy: str | None,
    connect_timeout_s: int,
    stalled_timeout_s: int,
) -> None:
    cmd = [
        curl_path,
        "--http1.1",
        "--fail",
        "--location",
        "--show-error",
        "--connect-timeout",
        str(connect_timeout_s),
        "--retry-connrefused",
        "-C",
        "-",
        "-A",
        USER_AGENT,
        url,
        "--output",
        str(part_path),
    ]
    if stalled_timeout_s > 0:
        cmd[1:1] = ["--speed-limit", "1", "--speed-time", str(stalled_timeout_s)]
    if proxy:
        cmd[1:1] = ["--proxy", proxy]

    subprocess.run(cmd, check=True)


def _download_with_urllib(
    url: str,
    part_path: Path,
    proxy: str | None,
    connect_timeout_s: int,
) -> None:
    headers = {"User-Agent": USER_AGENT}
    resume_from = part_path.stat().st_size if part_path.exists() else 0
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"

    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener()
    if proxy:
        opener.add_handler(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    with opener.open(request, timeout=connect_timeout_s) as response:
        status = getattr(response, "status", None)
        mode = "ab" if resume_from and status == 206 else "wb"
        with open(part_path, mode) as out_file:
            shutil.copyfileobj(response, out_file)


def _check_url(
    url: str,
    proxy: str | None,
    connect_timeout_s: int,
) -> None:
    curl_path = shutil.which("curl.exe") or shutil.which("curl")
    if curl_path is not None:
        cmd = [
            curl_path,
            "--http1.1",
            "--fail",
            "--location",
            "--head",
            "--show-error",
            "--connect-timeout",
            str(connect_timeout_s),
            "--max-time",
            str(connect_timeout_s),
            "-A",
            USER_AGENT,
            url,
        ]
        if proxy:
            cmd[1:1] = ["--proxy", proxy]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"ScienceBase access check failed for {url} "
                f"(curl exit code {exc.returncode}). If this URL opens in your browser, "
                "rerun with the same VPN/proxy settings or pass --proxy explicitly."
            ) from exc
        return

    opener = urllib.request.build_opener()
    if proxy:
        opener.add_handler(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")
    with opener.open(request, timeout=connect_timeout_s) as response:
        print(f"HTTP {response.status} {response.reason}")


def _file_url_from_metadata(item_id: str, file_info: dict) -> str | None:
    for key in ("url", "downloadUri", "downloadUrl"):
        url = file_info.get(key)
        if url:
            return url

    path_on_disk = file_info.get("pathOnDisk")
    if path_on_disk:
        encoded_path = urllib.parse.quote(path_on_disk, safe="")
        return f"https://www.sciencebase.gov/catalog/file/get/{item_id}?f={encoded_path}"

    return None


def _metadata_file_urls(
    item_id: str,
    proxy: str | None,
    timeout_s: int,
) -> dict[str, str]:
    url = SCIENCEBASE_ITEM_JSON_URL.format(item_id=item_id)
    with _open_url(url, proxy=proxy, timeout_s=timeout_s) as response:
        item = json.load(response)

    file_urls: dict[str, str] = {}
    for file_info in item.get("files", []):
        name = file_info.get("name")
        download_url = _file_url_from_metadata(item_id, file_info)
        if name and download_url:
            file_urls[name] = download_url

    return file_urls


def _download_file(
    url: str,
    out_path: Path,
    retries: int = 5,
    delay_s: int = 10,
    proxy: str | None = None,
    connect_timeout_s: int = 30,
    stalled_timeout_s: int = 900,
    overwrite: bool = False,
    dry_run: bool = False,
    check_only: bool = False,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print(f"Would download {out_path.name}: {url}")
        return

    if check_only:
        print(f"Checking {out_path.name}: {url}", flush=True)
        _check_url(url, proxy=proxy, connect_timeout_s=connect_timeout_s)
        return

    if out_path.exists() and not overwrite:
        if _is_valid_zip(out_path):
            print(f"Skipping existing valid ZIP: {out_path.name}")
            return
        raise RuntimeError(
            f"{out_path} already exists but is not a valid ZIP. "
            "Delete it or rerun with --overwrite."
        )
    if overwrite and out_path.exists():
        out_path.unlink()

    part_path = out_path.with_suffix(out_path.suffix + ".part")
    if part_path.exists():
        print(f"Resuming {out_path.name} from {_format_bytes(part_path.stat().st_size)}")
    else:
        print(f"Downloading {out_path.name}")

    if proxy:
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["HTTP_PROXY"] = proxy

    curl_path = shutil.which("curl.exe") or shutil.which("curl")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            if curl_path is not None:
                _download_with_curl(
                    curl_path,
                    url,
                    part_path,
                    proxy=proxy,
                    connect_timeout_s=connect_timeout_s,
                    stalled_timeout_s=stalled_timeout_s,
                )
            else:
                _download_with_urllib(
                    url,
                    part_path,
                    proxy=proxy,
                    connect_timeout_s=connect_timeout_s,
                )

            if not _is_valid_zip(part_path):
                raise RuntimeError(f"Downloaded file is not a valid ZIP: {part_path}")

            part_path.replace(out_path)
            print(f"Saved {out_path}")
            return
        except Exception as exc:  # pragma: no cover - surfaced to terminal
            # curl exit 33: server doesn't support byte ranges — discard the partial
            # file so the next attempt starts from scratch instead of failing again.
            if (
                isinstance(exc, subprocess.CalledProcessError)
                and exc.returncode == 33
                and part_path.exists()
            ):
                print(f"Server does not support byte ranges; discarding partial file and restarting.")
                part_path.unlink()
            last_error = exc
            if attempt < retries:
                print(
                    f"Download failed for {out_path.name}: {exc}; "
                    f"retrying in {delay_s}s ({attempt}/{retries})"
                )
                time.sleep(delay_s)
            else:
                break

    raise RuntimeError(
        f"Failed to download {out_path.name}: {last_error}. "
        f"Any partial file was kept at {part_path} so the next run can resume."
    )


def _parse_units(raw_units: list[str] | None) -> tuple[str, ...]:
    if raw_units is None:
        return UNITS

    normalized = tuple(unit.strip() for unit in raw_units if unit.strip())
    invalid = sorted(set(normalized) - set(UNITS))
    if invalid:
        valid = ", ".join(UNITS)
        raise ValueError(f"Unknown HDMA unit(s): {', '.join(invalid)}. Valid units: {valid}")

    return normalized


def _layer_info(layer: str) -> tuple[str, str]:
    layer = layer.upper()
    if layer == "DEM":
        return DEM_ITEM_ID, "af_dem"
    if layer == "FD":
        return FD_ITEM_ID, "af_fd"
    raise ValueError(f"Unknown layer '{layer}'. Use DEM or FD.")


def _download_layer(
    layer: str,
    dest_dir: Path,
    units: tuple[str, ...],
    retries: int = 5,
    delay_s: int = 10,
    proxy: str | None = None,
    connect_timeout_s: int = 30,
    stalled_timeout_s: int = 900,
    overwrite: bool = False,
    dry_run: bool = False,
    check_only: bool = False,
    use_metadata_urls: bool = True,
) -> None:
    item_id, prefix = _layer_info(layer)
    file_urls: dict[str, str] = {}
    if use_metadata_urls and not dry_run:
        try:
            file_urls = _metadata_file_urls(item_id, proxy=proxy, timeout_s=connect_timeout_s)
        except Exception as exc:
            print(f"Could not read ScienceBase file metadata for {layer}: {exc}")
            print("Falling back to filename-based ScienceBase URLs.")

    for unit in units:
        file_name = f"{prefix}_{unit}.zip"
        url = file_urls.get(file_name, _sciencebase_url(item_id, file_name))
        _download_file(
            url,
            dest_dir / file_name,
            retries=retries,
            delay_s=delay_s,
            proxy=proxy,
            connect_timeout_s=connect_timeout_s,
            stalled_timeout_s=stalled_timeout_s,
            overwrite=overwrite,
            dry_run=dry_run,
            check_only=check_only,
        )


def main() -> None:
    config = load_config()
    default_dest = Path(resolve_path("Data/Raw/HDMA_Africa"))

    parser = argparse.ArgumentParser(description="Download the HDMA Africa DEM and flow-direction ZIP tiles.")
    parser.add_argument(
        "--layers",
        nargs="+",
        default=["DEM", "FD"],
        help="HDMA layers to download. Default: DEM FD",
    )
    parser.add_argument(
        "--units",
        nargs="+",
        default=None,
        help="Optional HDMA processing units to download, e.g. --units 5_4 or --units 0 1_1 1_2. Default: all 19 units.",
    )
    parser.add_argument(
        "--dest",
        default=str(default_dest),
        help="Root directory that will receive DEM/ and FD/ subfolders.",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional proxy URL, e.g. http://proxy:8080. By default curl/Python use existing environment proxy settings.",
    )
    parser.add_argument(
        "--connect-timeout",
        type=int,
        default=30,
        help="Seconds to wait while establishing each connection. This is not a total download timeout.",
    )
    parser.add_argument(
        "--stalled-timeout",
        type=int,
        default=900,
        help="Abort curl if the transfer is effectively stalled for this many seconds. Use 0 to disable.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Deprecated alias for --stalled-timeout, kept for older workflow calls.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of download attempts per tile.",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Seconds to wait between retries.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing ZIPs instead of skipping them.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the files and URLs that would be downloaded without contacting ScienceBase.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check ScienceBase access for the selected files without downloading them.",
    )
    parser.add_argument(
        "--filename-urls",
        action="store_true",
        help="Use filename-based ScienceBase URLs instead of URLs discovered from item metadata.",
    )

    args = parser.parse_args()
    if args.timeout is not None:
        args.stalled_timeout = args.timeout

    dest_root = Path(args.dest)
    units = _parse_units(args.units)

    if args.proxy:
        print(f"Using explicit proxy: {args.proxy}")
    else:
        print("No explicit proxy configured; existing HTTPS_PROXY/HTTP_PROXY environment settings will be honored.")

    for layer in args.layers:
        layer_key = layer.upper()
        _layer_info(layer_key)
        if layer_key == "DEM":
            dest_dir = Path(resolve_path(config["Africa_HDMA_DEM_zip_dir_path"]))
        else:
            dest_dir = Path(resolve_path(config["Africa_HDMA_FD_zip_dir_path"]))
        if dest_root != default_dest:
            dest_dir = dest_root / layer_key
        _download_layer(
            layer_key,
            dest_dir,
            units=units,
            retries=args.retries,
            delay_s=args.delay,
            proxy=args.proxy,
            connect_timeout_s=args.connect_timeout,
            stalled_timeout_s=args.stalled_timeout,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            check_only=args.check_only,
            use_metadata_urls=not args.filename_urls,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}") from None
