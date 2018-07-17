from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import os
import shutil
import requests

_pool = None
EXEC_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(EXEC_DIR, "images")

def walk_path(node):
    path = []
    while (node is not None):
        path.insert(0, node.text(0))
        node = node.parent()
    return path

def pool():
    global _pool
    if  _pool is None:
        _pool = ProcessPoolExecutor(max_workers=1)
    return _pool

def download_image_url(url, dest):
    print("http {}".format(dest))
    r = requests.get(url, stream=True)
    request_length = r.headers.get('content-length')
        
    # window.set_status_text("Downloading {}:".format(name))
    downloaded = 0
    with open(dest, "wb") as f:
        if request_length is None:
            print("File has no content-length header.")
            f.write(r.content)
        else:
            progress_visible = 0
            for chunk in r.iter_content(chunk_size= 2 ** 17):
                downloaded += len(chunk)
                progress = int((downloaded / int(request_length)) * 100)
                if progress > progress_visible:
                    progress_visible = progress
                    print("Download status: {}%".format(progress_visible))
                else:
                    print("{} of {}".format(progress_visible, progress))
                f.write(chunk)

    # window.set_status_text("Finished downloading {}".format(name))

def url_handler(window, urls):
    current_item = window.previous_selection
    if not current_item:
        window.set_status_text("Select item before dropping.")
        return
    path_dirs = walk_path(current_item)
    image_path = os.path.join(*path_dirs)

    for url in urls:
        url = url.toString()

        if os.path.isdir(url[7:]):
            window.set_status_text("Error: Cannot drop a directory.")
            return

        if not os.path.exists(os.path.join(IMAGE_DIR, image_path)):
            os.makedirs(os.path.join(IMAGE_DIR, image_path))

        name = url.split("/")[-1]
        
        if os.path.isfile(os.path.join(IMAGE_DIR, image_path, name)):
            attempt = 1
            new_name = "({}) ".format(attempt) + name
            while os.path.isfile(os.path.join(IMAGE_DIR, image_path, new_name)):
                attempt += 1
                new_name = "({}) ".format(attempt) + name
            name = new_name

        destination = os.path.join(IMAGE_DIR, image_path, name)

        if url.startswith("file"):
            try:
                print("file: {}".format(name))
                future = pool().submit(shutil.copy2, url[7:], destination)
                future.add_done_callback(lambda x: window.set_slideshow())
                # shutil.copy2(url[7:], join(IMAGE_DIR, image_path, name))
            except IOError as e:
                print("IOError Occured", e)
                return 
            except OSError as e:
                print("OSError Occured", e)
                return

        elif url.startswith("http"):
            try:
                download_image_url(url, destination)
                future = pool().submit(download_image_url, url)
                future.add_done_callback(lambda x: window.set_slideshow())
            except IOError as e:
                print("IOError occured", e)
                return
        else:
            raise Exception("Dropped item not supported: {}".format(url))
        # window.set_slideshow()