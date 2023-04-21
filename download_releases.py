"""
Coped from reddit: https://www.reddit.com/r/LofiGirl/comments/phtdxb/i_made_a_python_script_to_quickly_download_new/
"""
from bs4 import BeautifulSoup
import urllib3
import os
import wget
import eyed3
from colorama import Fore, Style
import argparse
from collections import namedtuple, OrderedDict

# URL Configuration
RELEASE_URL = "https://lofigirl.com/blogs/releases"
RELEASE_LINK_PREFIX = "https://lofigirl.com"

# Release & Sound Definition
Release = namedtuple("Release", ("name","link","artists"))
SoundFile = namedtuple("SoundFile", ("title","link","artists"))
TranslatorGroup = namedtuple("TranslatorGroup", ("title","artist","album"))

def download_lofi(output_dir, download, release_numbers, translators):
    # HTTP Manager
    http = urllib3.PoolManager()

    releases = manage_info(http)

    if download:
        if release_numbers:
            selected_releases = []
            for release_num in release_numbers:
                selected_releases.append(releases[release_num])
            releases = selected_releases

        download_releases(http, releases, output_dir, translators=translators)
    else:
        print("Skipping download. Specify -d with optional release numbers to download")

def manage_info(http):

    # get html file of releases page
    resp = http.request("GET", RELEASE_URL)
    soup = BeautifulSoup(resp.data, "html.parser")

    # prepare variables for crunching releases html
    releases = []

    # crunch releases html, look for releases names, artists and URLs
    for link in soup.find_all("div", class_="Cv_release_mini_wrap_inner"):
        release_link = RELEASE_LINK_PREFIX + link.find("a").get("href")
        name = link.find("h2").string
        artists = link.find("i").string
        releases.append(Release(name, release_link, artists))

    # remove duplicates in links and names, then reverse all 3 arrays so the newest ones are at the bottom of the command line
    releases = list(OrderedDict(((release.link, release) for release in releases)).values())
    releases = list(OrderedDict(((release.name, release) for release in releases)).values())
    releases.reverse()

    # print all releases for the user to choose, get user input
    for i, release in enumerate(releases):
        print(
            Fore.RED
            + str(i)
            + ". "
            + Fore.BLUE
            + release.name
            + Style.RESET_ALL
            + " by "
            + Fore.GREEN
            + release.artists
        )
    print(Style.RESET_ALL)

    return releases

def download_release(http, release, output_dir, translators):
    print("Fetching Release: {release.name} by {release.artists}")

    # get html file of user selected release
    resp = http.request("GET", release.link)
    soup = BeautifulSoup(resp.data, "html.parser")

    # crunch release html for its name and link to its image
    album_name = soup.find(
        "div", class_="cv_custom_release_album_main_heading"
    ).h2.string
    image_link = "https:" + str(
        soup.find("div", class_="cv_custom_body_image_contents_album_part").a.get(
            "href"
        )
    )

    # crunch release html for links, titles and artists of individual songs
    sound_files = []
    for link in soup.find_all("div", class_="cv_custom_album_play_contents_inner_part"):
        try:
            sound_file_link = link.find(
                "div", class_="cv_custom_download_icon_part").get(
                    "data-audio-src"
                )
        except AttributeError as error:
            print(error)
            print("No data source found...skipping")
            continue

        sound_file_title=link.find(
                "div", class_="cv_custom_custom_content_description"
            ).h4.string.strip()[3:].strip()

        try:
            sound_file_artists = link.find(
                    "div", class_="cv_custom_custom_content_description"
                ).p.string.strip()
        except AttributeError as error:
            print(error)
            print("Using h4 tag")
            sound_file_artists = link.find(
                    "div", class_="cv_custom_custom_content_description"
                ).h4.string.strip()

        sound_files.append(SoundFile(sound_file_title, sound_file_link, sound_file_artists))

    # show user the links to the credit templates and release, also generate YouTube credits
    print(Fore.RED + "Here is the usage policy and credit templates:" + Style.RESET_ALL)
    print("https://lofigirl.com/pages/use-the-music")
    print(Fore.RED + "Here's the link to the release:" + Style.RESET_ALL)
    print(release.link)
    print(
        Fore.RED
        + "And here's the credit template for youtube for an entire album. Note that watch and listen links only show search queries on their respective platforms:"
        + Style.RESET_ALL
    )
    for sound_file in sound_files:
        print("- " + sound_file.artists + " - " + sound_file.title)
    print("- Provided by Lofi Girl")
    print(
        "- Watch: https://www.youtube.com/c/LofiGirl/search?query="
        + album_name.replace(" ", "")
    )
    print("- Listen: https://open.spotify.com/search/" + album_name.replace(" ", ""))

    album_name_stripped = album_name.translate(translators.album)

    # make a folder with the name of the album and download the cover into it
    album_path = os.path.join(output_dir, album_name_stripped)
    try:
        os.mkdir(album_path)
    except FileExistsError as error:
        print(error)
        print(
            "Folder exists - moving on...delete the folder and rerun for a fresh download"
        )
        return

    if not image_link:
        breakpoint()
    wget.download(image_link, out=os.path.join(album_path, "cover.png"))

    # create credits.txt file with the same content like what is printed into the console above^
    with open(album_path + "/credits.txt", "w") as f:
        for sound_file in sound_files:
            f.write("- " + sound_file.artists + " - " + sound_file.title + "\n")
        f.close()

    # download all songs 1 by 1 into the new folder, access it's metadata and fill album, artist, title and track num tags. Also create a trivial playlist file
    f = open(album_path + "/playlist.m3u", "w")
    for i, sound_file in enumerate(sound_files):
        artist = (
            sound_file.artists
            .translate(translators.artist)
            .replace("\u2019", "'")
            .replace("\u012b", "")
        )
        title = (
            sound_file.title
            .translate(translators.title)
            .replace("\u2019", "'")
            .replace("\u012b", "")
        )

        file_basename = f"{artist}-{title}.mp3"
        filename = os.path.join(album_path, file_basename)

        if not sound_file.link:
            breakpoint()

        wget.download(sound_file.link, out=filename)
        audiofile = eyed3.load(filename)
        audiofile.tag.album = album_name.replace("\u2019", "'").replace("\u012b", "")
        audiofile.tag.artist = (
            sound_file.artists.replace("\u2019", "'").replace("\u012b", "")
        )
        audiofile.tag.title = (
            sound_file.title.replace("\u2019", "'").replace("\u012b", "")
        )
        audiofile.tag.track_num = i + 1

        try:
            audiofile.tag.save()
        except UnicodeEncodeError as error:
            breakpoint()
            # .replace(u"\u2019", "'")
        f.write(filename)
    f.close()

    print()
    print(Fore.RED + "all done" + Style.RESET_ALL)

def download_releases(http, releases, output_dir, translators):
    print(f"Downloading {len(releases)} releases")
    for selected_release in releases:
        download_release(http, selected_release, output_dir, translators=translators)

def cli():
    def is_dir(path):
        if os.path.isdir(path):
            return path
        else:
            return NotADirectoryError(f"Supplied path is not a directory: {path}")

    parser = argparse.ArgumentParser(prog=__file__, description="Downloader for lofigirl.com")
    parser.add_argument("-o","--output", help="Output folder", type=is_dir, default="downloads", required=True)
    parser.add_argument("-d","--download", help="Specify releases to be downloaded. Leave blank for all", type=int, nargs="*")
    parser.add_argument("--title-remove", help="Remove all specified characters within the title", type=str, default="")
    parser.add_argument("--title-replace", help="Specific characters within the title to be replaced with --title-replace-with", type=str, default="")
    parser.add_argument("--title-replace-with", help="Specific characters within the title to replace occurences of --title-replace", type=str, default="")
    parser.add_argument("--artist-remove", help="Remove all specified characters within the artist", type=str, default="")
    parser.add_argument("--artist-replace", help="Specific characters within the artist to be replaced with --artist-replace-with", type=str, default="")
    parser.add_argument("--artist-replace-with", help="Specific characters within the artist to replace occurences of --artist-replace", type=str, default="")
    parser.add_argument("--album-remove", help="Remove all specified characters within the album", type=str, default="")
    parser.add_argument("--album-replace", help="Specific characters within the album to be replaced with --album-replace-with", type=str, default="")
    parser.add_argument("--album-replace-with", help="Specific characters within the album to replace occurences of --album-replace", type=str, default="")

    args = parser.parse_args()
    return args

def translator(replace_characters, replace_with_characters, remove_characters):
    return str.maketrans(replace_characters, replace_with_characters, remove_characters)

if __name__ == "__main__":
    args = cli()

    title_translator = translator(args.title_replace, args.title_replace_with, args.title_remove)
    artist_translator = translator(args.artist_replace, args.artist_replace_with, args.artist_remove)
    album_translator = translator(args.album_replace, args.album_replace_with, args.album_remove)
    tg = TranslatorGroup(title_translator, artist_translator, album_translator)

    download_lofi(output_dir=args.output, download=args.download is not None, release_numbers=args.download, translators=tg)
