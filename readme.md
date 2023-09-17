## Download Lofi Girl Releases

Download all lofi girl releases

### Getting Started

    python3.11 -m venv env
    source env/bin/activate
    
    pip install -r requirements.txt
    
    python download.py

This will download the zip files into the downloads folder.

The extracted files lack ID3 tagging. One can use [picard](https://github.com/metabrainz/picard) to assist with tagging.

### Update CSV

If new releases are made one can update the csv with:

    python update_releases.py

### Audio Quality

The bitrate of the music ranges from 128 kbps (Cut-off at 16 kHz) to 320kbps (Cut-off at 20 kHz)

### Size

At February 2023:

* Size: 12GB
* Number of Albums: 324

At August 2023:

* Size: 12.18 GB (zipped)
* Number of Albums: 378

### Credit

Orignal author: [Deadlibor](https://www.reddit.com/user/Deadlibor/) post on [reddit](https://www.reddit.com/r/LofiGirl/comments/phtdxb/i_made_a_python_script_to_quickly_download_new/)
