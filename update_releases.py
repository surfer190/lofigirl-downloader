"""
1. Go to https://lofigirl.com/releases/
2. Get all the releases - artist and release title
3. For each release get the download link
4. Store it in a csv file in the repo
"""
import csv

from bs4 import BeautifulSoup
import httpx

RELEASES_URL = "https://lofigirl.com/releases/"

headers = {
    'user-agent': 'lofigirl-downloader/0.2.0',
    'content-type': 'application/x-www-form-urlencoded'
}

client = httpx.Client(
    headers=headers,
    timeout=30.0
)

page = 1

release_links = set()

def get_release_links():
    while True:
        
        response = client.post(
            RELEASES_URL,
            data={
                "action": "jet_engine_ajax",
                "handler": "get_listing",
                "query[post_status]": "publish",
                "query[found_posts]": "383",
                "query[max_num_pages]": "39",
                "query[post_type]": "releases",
                "query[orderby]": "",
                "query[order]": "DESC",
                "query[paged]": f"{page}",
                "query[posts_per_page]": "50",
                "query[suppress_filters]": "false",
                "query[jet_smart_filters]": "jet-engine/all-releases",
                "page_settings[post_id]": "423",
                "page_settings[queried_id]": "17370|WP_Post",
                "page_settings[element_id]": "4b7c1a2",
                "page_settings[page]": f"{page}",
                "listing_type": "elementor"
            }
        )

        html_data = response.json().get('data').get('html')

        soup = BeautifulSoup(html_data, 'html.parser')

        links = soup.find_all('a', {'class': 'jet-engine-listing-overlay-link'})

        if links:
            for link in links:
                release_links.add(link.get('href'))
        else:
            print(f'No results for page: {page}')
            break
        
        print(f'Page {page}: done')
        page = page + 1

def get_release_info():
    
    release_links = sorted(list(release_links))
    
    all_info = []
    
    for link in release_links:
        print(link)
        response = client.get(link)
        
        artists = ''
        title = ''

        if response.status_code == httpx.codes.OK:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_div = soup.find('div', {'data-id': '29d3c6b'})
            if title_div:
                title = title_div.text
                title = title.strip()
                title = title.replace('\n', '')
            
            artists_div = soup.find('div', {'data-listing-id': '15303'})
            if artists_div:
                artists = artists_div.text
                artists = artists.strip()
                artists = artists.replace('\n', '')
            
            download = soup.find('div', {'data-id': '311b599'})
            if download:
                download_link = download.find('a').get('href')
            else:
                print('NO DOWNLOAD LINK', artists, '-', title)
                continue
            
            print(artists, '-', title)
            all_info.append({
                'artists': artists,
                'title': title,
                'link': download_link
            })
        else:
            print(f'Problem: {link}')

    with open('releases.csv', 'w', newline='') as csv_file:
        fieldnames = ['artists', 'title', 'link']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for info in all_info:
            writer.writerow(info)

if __name__ == '__main__':

    get_release_links()
    
    get_release_info()
