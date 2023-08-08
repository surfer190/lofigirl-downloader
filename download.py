"""
1. Give the user a list of releases to download
2. User selects
3. By default download all
"""
import csv
import pathlib
import sys

import httpx

DOWNLOAD_DIR = pathlib.Path(__file__).parent / "downloads"

client = httpx.Client(headers={"user-agent": "lofigirl-downloader/0.2.0"})


def download_file(file_href):

    # Stream the download
    # with client.stream("GET", file_href) as reader:
    #     for data in reader.iter_bytes():
    #         print(data)

    file_name_with_extension = file_href.split("/")[-1]

    file_path = DOWNLOAD_DIR / file_name_with_extension

    # check if zip already exists
    if pathlib.Path(file_path).is_file():
        print(f"File exists: {file_path}")
        return

    file_response = client.get(file_href)

    if file_response.status_code == httpx.codes.OK:
        content_type = file_response.headers.get("content-type")
        content_disposition = file_response.headers.get("content-disposition")

        if content_type == "application/zip":
            extension = "zip"
        else:
            print(
                f"Unexpected file extension '{content_type}' for {content_disposition}"
            )
            sys.exit(1)

        with open(file_path, "wb") as current_file:
            current_file.write(file_response.content)
            print(f"Completed: {file_href}")


if __name__ == "__main__":
    with open("releases.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            artists = row.get("artists")
            title = row.get("title")
            link = row.get("link")

            download_file(link)
