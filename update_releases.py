"""
1. Go to https://lofigirl.com/releases/
2. Get all the releases - artist and release title
3. For each release get the download link
4. Store it in a csv file in the repo
"""
import csv
import logging

from bs4 import BeautifulSoup
import httpx

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

RELEASES_URL = "https://lofigirl.com/wp-admin/admin-ajax.php"

headers = {
    "user-agent": "lofigirl-downloader/0.3.0",
    "content-type": "application/x-www-form-urlencoded",
}

client = httpx.Client(
    headers=headers,
    timeout=120.0,
    verify=False,
    http2=True,
    limits=httpx.Limits(
        keepalive_expiry=100,
    ),
    follow_redirects=True
)

release_links = set()

def get_release_links():

    page = 0

    while True:
        try:
            response = client.post(
                RELEASES_URL,
                data={
                    "action": "jet_smart_filters",
                    "provider": "jet-engine/all-releases",
                    "settings[lisitng_id]": "344",
                    "settings[columns]": "2",
                    "settings[columns_tablet]": "2",
                    "settings[columns_mobile]": "1",
                    "settings[column_min_width]": "240",
                    "settings[column_min_width_tablet]": "",
                    "settings[column_min_width_mobile]": "",
                    "settings[inline_columns_css]": "false",
                    "settings[is_archive_template]": "",
                    "settings[post_status][]": "publish",
                    "settings[use_random_posts_num]": "",
                    "settings[posts_num]": "8",
                    "settings[max_posts_num]": "9",
                    "settings[not_found_message]": "No+releases+was+found,+please+retry+with+other+filters+:c",
                    "settings[is_masonry]": "",
                    "settings[equal_columns_height]": "yes",
                    "settings[use_load_more]": "",
                    "settings[load_more_id]": "",
                    "settings[load_more_type]": "scroll",
                    "settings[load_more_offset][unit]": "px",
                    "settings[load_more_offset][size]": "0",
                    "settings[loader_text]": "Loading+more+artists",
                    "settings[loader_spinner]": "yes",
                    "settings[use_custom_post_types]": "",
                    "settings[custom_post_types][]": "releases",
                    "settings[hide_widget_if]": "",
                    "settings[carousel_enabled]": "",
                    "settings[slides_to_scroll]": "1",
                    "settings[arrows]": "true",
                    "settings[arrow_icon]": "fa+fa-angle-left",
                    "settings[dots]": "",
                    "settings[autoplay]": "true",
                    "settings[pause_on_hover]": "true",
                    "settings[autoplay_speed]": "5000",
                    "settings[infinite]": "true",
                    "settings[center_mode]": "",
                    "settings[effect]": "slide",
                    "settings[speed]": "500",
                    "settings[inject_alternative_items]": "",
                    "settings[scroll_slider_enabled]": "",
                    "settings[scroll_slider_on][]": [
                        "desktop",
                        "tablet",
                        "mobile"
                    ],
                    "settings[custom_query]": "yes",
                    "settings[custom_query_id]": "27",
                    "settings[_element_id]": "all-releases",
                    "props[found_posts]": "409",
                    "props[max_num_pages]": "41",
                    "props[page]": f"{page}",
                    "props[query_type]": "posts",
                    "props[query_id]": "27",
                    "paged": f"{page + 1}"
                },
            )
        except httpx.HTTPError as error:
            logger.exception(error)
            logger.warning('Issue getting page: %s...skipping', page)
            continue

        html_data = response.json().get("content")

        soup = BeautifulSoup(html_data, "html.parser")

        links = soup.find_all("a", {"class": "jet-engine-listing-overlay-link"})

        if links:
            for link in links:
                release_links.add(link.get("href"))
        else:
            logger.info("No results for page: %s", page)
            break

        logger.info(f"Page %s: done", page)
        page = page + 1


def get_release_info():

    # make a variable for function scope - to stop UnboundLocalError
    current_release_links = sorted(list(release_links))

    all_info = []

    for link in current_release_links:
        logger.info(link)

        try:
            response = client.get(link)
        except httpx.HTTPError as error:
            logger.info(error)
            logger.warning("Skipping: %s", link)
            continue

        artists = ""
        title = ""

        if response.status_code == httpx.codes.OK:
            soup = BeautifulSoup(response.content, "html.parser")

            title_div = soup.find("div", {"data-id": "29d3c6b"})
            if title_div:
                title = title_div.text
                title = title.strip()
                title = title.replace("\n", "")

            artists_div = soup.find("div", {"data-listing-id": "15303"})
            if artists_div:
                artists = artists_div.text
                artists = artists.strip()
                artists = artists.replace("\n", "")

            download = soup.find("div", {"data-id": "311b599"})
            if download:
                download_link = download.find("a").get("href")
            else:
                logger.info("NO DOWNLOAD LINK %s - %s", artists, title)
                continue

            try:
                logger.info("%s - %s", artists, title)
            except UnicodeEncodeError as ex:
                logger.info(ex)
            
            all_info.append({"artists": artists, "title": title, "link": download_link})
        else:
            logger.error("Problem: %s", link)

    with open("releases.csv", "w", newline="", encoding='utf-8') as csv_file:
        fieldnames = ["artists", "title", "link"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()

        for info in all_info:
            writer.writerow(info)


if __name__ == "__main__":

    get_release_links()

    get_release_info()
