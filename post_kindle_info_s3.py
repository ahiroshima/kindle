import json
import requests
import bottlenose
import time
import requests
import os
import boto3
from traceback import print_exc
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from string import Template

def get_kindle_books():
    try:
        AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY')
        AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY')
        AMAZON_ASSOC_TAG = os.environ.get('AMAZON_ASSOC_TAG')

        amazon = bottlenose.Amazon(AMAZON_ACCESS_KEY,AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG, Region='JP')
        res = amazon.ItemSearch(
            SearchIndex = 'KindleStore',
            BrowseNode = 2291905051,
            ResponseGroup= 'Large'
                )
        soup = BeautifulSoup(res,"lxml")
        print("[post_kindle_info] Kindle book list have been acquired.")
        return (soup.findAll("item"))
    except:
        print_exc()
        raise Exception


def create_kindle_list():
    books = get_kindle_books()
    contents = ""

    c_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    contents += "更新日時：" + c_date

    for book in books:
        try:
            contents += "<div class='row'>"
            contents +=      "<div class='col-md-10 col-md-offset-1'>"
            contents +=          "<div><h3>{}</h3></div>\n\n".format(book.title.text)
            contents +=          "<div>著者：{}</div>".format(book.author.text)
            contents +=          "<div><a href = '{}'><img src = '{}'></a></div><!-- 画像-->\n".format(book.detailpageurl.text, book.largeimage.url.text)
            contents +=          "<div><blockquote class='blockquote'><p class='mb-0'>{}<p></blockquote></div><!-- 内容-->\n".format(book.content.text)
            contents +=          "<div><a href='{}'>詳細はこちら</a></div><!-- リンク-->\n".format(book.detailpageurl.text)
            contents +=      "</div>"
            contents += "</div>"
            contents += "<hr>"
        except Exception as e:
            contents +=      "</div>"
            contents += "</div>"
            print(e)

    return contents

def create_contents():
    contents = ""
    try:
        kindle_list = create_kindle_list()
        # WordPress用HTML生成. テンプレートにKindle本のリストを埋め込む
        t = Template(open('./kindle_list.template').read())
        contents = t.substitute({'kindle_list': kindle_list})
    except Exception as e:
        print(e)
    return contents

def post_to_s3(contents):
    try:
        S3_BUCKET = os.environ.get('S3_BUCKET')
        open('./output.html', mode='w').write(contents)
        s3 = boto3.client('s3')
        s3.upload_file(
            './output.html', S3_BUCKET,
            'kindle-books/index.html',
            ExtraArgs={'ContentType': 'text/html', 'ACL': 'public-read'})
        print("[post_kindle_info] Contents have been posted.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    try:
        contents_ = create_contents()
        post_to_s3(contents_)
    except:
        print_exc()
