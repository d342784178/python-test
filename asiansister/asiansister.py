import random

import requests
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

from requests.adapters import HTTPAdapter

requests.packages.urllib3.disable_warnings()
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'https://127.0.0.1:7890'}
subDirectory = 'asd'
pool = ThreadPoolExecutor(1)
requestSession = requests.Session()
requestSession.mount('http://', HTTPAdapter(max_retries=5))
requestSession.mount('https://', HTTPAdapter(max_retries=5))


def download(code):
    print(f'start download {code}')
    r = requestSession.get(f'http://www.asiansister.com/tool/getImageDownload.php?code={code}',
                           proxies=proxies, timeout=(1, 3))

    urls = r.text.split(',')

    if len(urls) == 1:
        print(f'No collection have {code} code...')
        print()
        return

    count = 0
    folderName = f'{code}'
    if subDirectory != '':
        folderName = f'{subDirectory}/{folderName}'
    fileNamePrefix = 'image_'
    fileCount = len(urls) - 1

    indicator = ['-' for i in range(fileCount)]

    outputDirectory = folderName + '/'

    if not os.path.exists(os.path.dirname(outputDirectory)):
        try:
            os.makedirs(os.path.dirname(outputDirectory))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    else:
        if len(os.listdir(outputDirectory)) == len(urls) - 1:
            print(f"You already have {outputDirectory} download complete...")
            print()
            return

    urls = urls[1:len(urls)]

    def req_get(url, localCount):
        global completeCount
        c = localCount
        try:
            img = requestSession.get(url.replace('https', 'http'), stream=False, proxies=proxies, timeout=(1, 3))
            outputPath = f'{outputDirectory}{fileNamePrefix}{c}.jpg'
            localFile = open(outputPath, 'wb+')
            localFile.write(img.content)
            indicator[c] = '*'
        except Exception as e:
            print(e)
            print("file download failed, please check your internet connection!")

    futures = []
    for i, url in enumerate(urls):
        print(f'download {code}-{i}')
        resultFuture = pool.submit(req_get, url, count)
        count += 1
        futures.append(resultFuture)
        if len(futures) == 20 :
            for index, ff in enumerate(futures):
                if index % 5 == 0:
                    continue
                ff.result()
                futures.remove(ff)

    print("Download Complete!!!!")
    print()


futures2 = []
dirs = os.listdir(subDirectory)
dirs.sort()
for index in range(2):
    download(index)
