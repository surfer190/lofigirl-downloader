from bs4 import BeautifulSoup
import urllib3
import os
import wget
import eyed3
from colorama import Fore, Style

#get html file of releases page
http = urllib3.PoolManager()
resp = http.request("GET","https://lofigirl.com/blogs/releases")
soup = BeautifulSoup(resp.data, 'html.parser')

#prepare variables for crunching releases html
releases_link_prefix = 'https://lofigirl.com'
releases_links = []
releases_names = []
releases_artists = []

#crunch releases html, look for releases names, artists and URLs
for link in soup.find_all('div', class_='Cv_release_mini_wrap_inner'):
    releases_links.append(releases_link_prefix+link.find('a').get('href'))
    releases_names.append(link.find('h2').string)
    releases_artists.append(link.find('i').string)

#remove duplicates in links and names, then reverse all 3 arrays so the newest ones are at the bottom of the command line
releases_links = list(dict.fromkeys(releases_links))
releases_names = list(dict.fromkeys(releases_names))
releases_links.reverse()
releases_names.reverse()
releases_artists.reverse()

#print all releases for the user to choose, get user input
for i in range (0,len(releases_links)):
    print(Fore.RED + str(i+1) + '. '+Fore.BLUE+releases_names[i]+Style.RESET_ALL+' by '+Fore.GREEN+releases_artists[i])
print(Style.RESET_ALL)
selected_release = input('Write number of the release you want to download: ')

#get html file of user selected release
resp = http.request('GET',releases_links[int(selected_release)-1])
soup = BeautifulSoup(resp.data, 'html.parser')

#crunch release html for its name and link to its image
album_name = soup.find('div', class_='cv_custom_release_album_main_heading').h2.string
image_link = 'https:'+str(soup.find('div', class_='cv_custom_body_image_contents_album_part').a.get('href'))

#crunch release html for links, titles and artists of individual songs
sound_file_links = []
sound_file_title = []
sound_file_artist = []
for link in soup.find_all('div', class_='cv_custom_album_play_contents_inner_part'):
    sound_file_links.append(link.find('div', class_='cv_custom_download_icon_part').get('data-audio-src'))
    sound_file_title.append(link.find('div', class_='cv_custom_custom_content_description').h4.string.strip()[3:])
    sound_file_artist.append(link.find('div', class_='cv_custom_custom_content_description').p.string.strip())

#show user the links to the credit templates and release, also generate YouTube credits
print(Fore.RED+'Here is the usage policy and credit templates:'+Style.RESET_ALL)
print('https://lofigirl.com/pages/use-the-music')
print(Fore.RED+'Here\'s the link to the release:'+Style.RESET_ALL)
print(releases_links[int(selected_release)-1])
print(Fore.RED+'And here\'s the credit template for youtube for an entire album. Note that watch and listen links only show search queries on their respective platforms:'+Style.RESET_ALL)
for i in range(0,len(sound_file_links)):
    print('- '+sound_file_artist[i] + ' - ' + sound_file_title[i])
print('- Provided by Lofi Girl')
print('- Watch: https://www.youtube.com/c/LofiGirl/search?query='+album_name.replace(' ',''))
print('- Listen: https://open.spotify.com/search/'+album_name.replace(' ',''))

#make a folder with the name of the album and download the cover into it
os.mkdir(album_name)
wget.download(image_link, out=os.path.join(album_name, 'cover.png'))

#create credits.txt file with the same content like what is printed into the console above^
with open(album_name+'/credits.txt','w') as f:
    f.write('Here is the usage policy and credit templates:\nhttps://lofigirl.com/pages/use-the-music\nHere\'s the link to the release:\n')
    f.write(releases_links[int(selected_release)-1])
    f.write('\nAnd here\'s the credit template for youtube for an entire album. Note that watch and listen links only show search queries on their respective platforms:\n')
    for i in range(0,len(sound_file_links)):
        f.write('- '+sound_file_artist[i] + ' - ' + sound_file_title[i]+'\n')
    f.write('- Provided by Lofi Girl\n')
    f.write('- Watch: https://www.youtube.com/c/LofiGirl/search?query='+album_name.replace(' ','')+'\n')
    f.write('- Listen: https://open.spotify.com/search/'+album_name.replace(' ',''))
    f.close()

#download all songs 1 by 1 into the new folder, access it's metadata and fill album, artist, title and track num tags. Also create a trivial playlist file
f = open(album_name+'/playlist.m3u','w')
for i in range(0,len(sound_file_links)):
    wget.download(sound_file_links[i], out=os.path.join(album_name, sound_file_title[i] + '.mp3'))
    audiofile = eyed3.load(os.path.join(album_name, sound_file_title[i] + '.mp3'))
    audiofile.tag.album = album_name
    audiofile.tag.artist = sound_file_artist[i]
    audiofile.tag.title = sound_file_title[i]
    audiofile.tag.track_num = i+1
    audiofile.tag.save()
    f.write(sound_file_title[i]+'.mp3\n')
f.close()


print()
print(Fore.RED+'all done'+Style.RESET_ALL)