import json
import requests
import bottlenose
import time
import requests
import os
from traceback import print_exc
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup

# WP環境に合わせて変更すること
wp_base_url_ = "http://localhost/"
page_id = "398"     # ポスト対象のページID 事前にWordPressのAPIなどで調べておく
user_id = 2         #投稿ユーザーID、事前にWordPressで確認しておく
category_ids = [80] #Kindle Booksカテゴリー

def create_post(title_, contents_):
    # credential情報は環境変数から取得
    WP_USER = os.environ.get('WP_USER')
    WP_PASS = os.environ.get('WP_PASS')
    # build request body
    payload = {"title": title_,
               "content": contents_,
               "author": user_id,
               "date": datetime.now().isoformat(),
               "categories": category_ids,
               "status": "publish"}
    # 作成済みの固定ページ：ID398に対して更新を行う
    res = requests.post(urljoin(wp_base_url_, "wp-json/wp/v2/pages" + "/" + page_id),
                        data=json.dumps(payload),
                        headers={'Content-type': "application/json"},
                        auth=(WP_USER, WP_PASS))
    print("Contents have been posted. " + repr(res))


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
        print("Kindle book list have been acquired.")
        return (soup.findAll("item"))
    except:
        print_exc()
        raise Exception


def get_kindle_list():
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


if __name__ == "__main__":
    try:
        contents_ = get_kindle_list()
        create_post("ビジネス・経済本のおすすめ", contents_)
    except:
        print_exc()
