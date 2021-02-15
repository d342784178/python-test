import os
import time
import random
import urllib
import requests
import sys
import shutil
import zipfile
from bs4 import BeautifulSoup as bs
import xml.dom.minidom as xdm
from concurrent.futures import ThreadPoolExecutor
from urllib.request import ProxyHandler, build_opener

cache_path = "epub/cache"
book_path = "epub/book"
proxies = {'http': 'http://127.0.0.1:19180', 'https': 'https://127.0.0.1:19180'}
urlOpener = build_opener(ProxyHandler(proxies))


def worker(book_link, b_item, index, itemNums):
    # print(b_item.getAttribute("href"))
    for j in range(1, 10):
        try:
            item = b_item.getAttribute("href")
            if "/" in item:
                sub_link = item.split("/")
                sub_path = "{}/{}".format(cache_path, sub_link[0])
                file_name = sub_link[1]
                # print(sub_link[1])
                isSubExists = os.path.exists(sub_path)
                if not isSubExists:
                    os.makedirs(sub_path)
                if "html" in file_name:
                    r = requests.get("{}{}".format(book_link, item), timeout=5, proxies=proxies)
                    soup = bs(r.content, "html5lib")
                    try:
                        soup.find('div', class_="readertop").decompose()
                        soup.find('div', class_="readermenu").decompose()
                        soup.find('div', class_="reader-to-vip c-pointer").decompose()
                    except:
                        print("[*] Nothing to remove")
                    f = open("{}/{}".format(sub_path, file_name), 'w', encoding='utf-8')
                    f.write(str(soup))
                    f.close()
                else:
                    urlopen("{}{}".format(book_link, item), "{}/{}".format(sub_path, file_name))
            elif "html" in item:  # 超链接,进行下载
                # print(item)
                # urllib.request.urlretrieve("{}{}".format(book_link,item),"{}/{}".format(cache_path,item))
                r = requests.get("{}{}".format(book_link, item), timeout=5, proxies=proxies)
                soup = bs(r.content, "html5lib")
                try:
                    soup.find('div', class_="readertop").decompose()
                    soup.find('div', class_="readermenu").decompose()
                    soup.find('div', class_="reader-to-vip c-pointer").decompose()
                except:
                    print("[*] Nothing to remove")
                f = open("{}/{}".format(cache_path, item), 'w', encoding='utf-8')
                f.write(str(soup))
                f.close()
            else:
                urlopen("{}{}".format(book_link, item), "{}/{}".format(cache_path, item))
            break
        except Exception as e:
            print("[-] E:{}".format(e))
            print("[-] Retrying {} of 10 times".format(j))
            time.sleep(random.randint(1, 4))
    print("[*] {} of {} items downloaded".format(index, itemNums), end="\r")


def initCacheDir():
    # 初始化缓存目录
    isCacheExists = os.path.exists(cache_path)
    if isCacheExists:
        shutil.rmtree(cache_path)  # 清除旧文件夹
        print("[*] Cache cleared successfully")
        os.makedirs(cache_path)  # 建立新文件夹
    else:
        os.makedirs(cache_path)
    # 初始化图书存放目录
    isBookExists = os.path.exists(book_path)
    if not isBookExists:
        os.makedirs(book_path)


def urlopen(url, filename):
    opener = urllib.request.build_opener(ProxyHandler(proxies))
    # install it
    urllib.request.install_opener(opener)

    r = urllib.request.urlopen(url)
    open(filename, "wb").write(r.read())


def downloadFile(book_link, execute):
    opf_link = book_link + "content.opf"
    for i in range(1, 11):
        try:
            urlopen(opf_link, "{}/content.opf".format(cache_path))
            break
        except Exception as e:
            print("[-] E:{}".format(e))
            print("[-] Retrying {} of 10 times".format(i))
            time.sleep(random.randint(1, 4))
    isOpfExists = os.path.exists(cache_path + "/content.opf")
    if isOpfExists:
        print("[+] Opf file download successfully")
    else:
        print("[-] Opf file download failed, please check your internet connection!")
        sys.exit()

    #解析opf文件
    xml_doom = xdm.parse("{}/content.opf".format(cache_path))
    book_info = xml_doom.documentElement
    book_name = book_info.getElementsByTagName("dc:title")
    # print(book_name[0].childNodes[0].data)
    name = book_name[0].childNodes[0].data
    book_author = book_info.getElementsByTagName("dc:creator")
    # print(book_author[0].childNodes[0].data)
    author = book_author[0].childNodes[0].data
    book_content = book_info.getElementsByTagName("item")
    itemNums = len(book_content)
    print("[*] Opf file analyze successfully")
    print("[*] Downloading contents...")

    #下载opf-item
    futures = []
    for index, b_item in enumerate(book_content):
        resultFuture = execute(book_link, b_item, index, itemNums)
        futures.append(resultFuture)
    for f in futures:
        # 阻塞拿到结果
        f.result()

    #下载完成,进行打包
    print("[+] Content download successfully")
    f = open("{}/mimetype".format(cache_path), 'w', encoding='utf-8')
    f.write("application/epub+zip")
    f.close()
    print("[*] Mimetype file create successfully")
    os.makedirs("{}/META-INF".format(cache_path))
    f = open("{}/META-INF/container.xml".format(cache_path), 'w', encoding='utf-8')
    f.write(
        '<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n   <rootfiles>\n      <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>\n   </rootfiles>\n</container>')
    f.close()
    print("[*] Meta info create successfully")
    new_book = zipfile.ZipFile("{}/tmp.zip".format(book_path), 'w')
    print("[*] Packaging...")
    pack = os.walk(cache_path)
    for current_path, subfolders, filesname in pack:
        for file in filesname:
            src = os.path.join(current_path, file)
            dst = src.replace(cache_path, "", 1)
            # print("{},{}".format(src,dst))
            new_book.write(src, arcname=dst, compress_type=zipfile.ZIP_STORED)
    new_book.close()
    os.rename("{}/tmp.zip".format(book_path), "{}/{}-{}.epub".format(book_path, name, author))
    print("[*] {}-{} download successfully".format(name, author))


def main():
    book_link_list = open("epub/file.txt", "r").readlines()
    pool = ThreadPoolExecutor(50)

    def execute(*args):
        return pool.submit(worker, *args)

    for book_link in book_link_list:
        initCacheDir()
        book_link = book_link.strip('\n')
        print("[*] {} download start".format(book_link))
        downloadFile(book_link, execute)


if __name__ == '__main__':
    main()
    # print(worker(9998))
