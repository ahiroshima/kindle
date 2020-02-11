import json
import requests
import time
import os
from traceback import print_exc
from urllib.parse import urljoin
from datetime import datetime

from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException
from paapi5_python_sdk.search_items_request import SearchItemsRequest
from paapi5_python_sdk.search_items_resource import SearchItemsResource

# depend on your WP environment.
WP_BASE_URL = "http://localhost/"
PAGE_ID = "398"     # Target page ID
USER_ID = 2         # User ID for WP
CATEGORY_IDS = [80] # Kindle Books category

def post_contents(title_, contents_):
    # credential情報は環境変数から取得
    WP_USER = os.environ.get('WP_USER')
    WP_PASS = os.environ.get('WP_PASS')
    # build request body
    payload = {"title": title_,
               "content": contents_,
               "author": USER_ID,
               "date": datetime.now().isoformat(),
               "categories": CATEGORY_IDS,
               "status": "publish"}
    # 作成済みの固定ページ：ID398に対して更新を行う
    res = requests.post(urljoin(WP_BASE_URL, "wp-json/wp/v2/pages" + "/" + PAGE_ID),
                        data=json.dumps(payload),
                        headers={'Content-type': "application/json"},
                        auth=(WP_USER, WP_PASS))
    print("Contents have been posted. " + repr(res))


def get_kindle_books():
    AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY')
    AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY')
    AMAZON_ASSOC_TAG = os.environ.get('AMAZON_ASSOC_TAG')

    HOST = "webservices.amazon.co.jp"
    REGION = "us-west-2"

    default_api = DefaultApi(
        access_key=AMAZON_ACCESS_KEY, secret_key=AMAZON_SECRET_KEY, host=HOST, region=REGION
    )

    # request paraeters
    KEYWORDS = "*"
    SEARCH_INDEX = "KindleStore"
    BROWSE_NODE_ID = "2291905051"
    ITEM_COUNT = 10

    # For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter
    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.ITEMINFO_BYLINEINFO,
        SearchItemsResource.ITEMINFO_CONTENTINFO,
        SearchItemsResource.ITEMINFO_TECHNICALINFO,
        SearchItemsResource.IMAGES_PRIMARY_LARGE
    ]

    try:
        # Forming request
        search_items_request = SearchItemsRequest(
            partner_tag=AMAZON_ASSOC_TAG,
            partner_type=PartnerType.ASSOCIATES,
            keywords=KEYWORDS,
            search_index=SEARCH_INDEX,
            browse_node_id=BROWSE_NODE_ID,
            item_count=ITEM_COUNT,
            resources=search_items_resource,
        )
        # Sending request
        response = default_api.search_items(search_items_request)
        # print("Complete Response:", response)

        # Parse response
        if response.errors is not None:
            print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
            print("Error code", response.errors[0].code)
            print("Error message", response.errors[0].message)
            return

        if response.search_result is not None:
            print("API called Successfully")
            return(response.search_result.items)

    except:
        print_exc()
        raise Exception


def create_kindle_list():
    books = get_kindle_books()
    contents = ""

    c_date = datetime.now().strftime("%Y/%m/%d")
    contents += "<h2>ビジネス・経済本のおすすめ（" + c_date + "更新）</h2>"
    contents += "<hr>"

    for book in books:
        try:
            contents += "<div class='row'>"
            contents +=      "<div class='col-md-10 col-md-offset-1'>"
            contents +=          "<div><h3>{}</h3></div>\n\n".format(book.item_info.title.display_value)
            contents +=          "<div>著者：{}</div>".format(book.item_info.by_line_info.contributors[0].name)
            contents +=          "<div><a href = '{}'><img src = '{}'></a></div><!-- 画像-->\n".format(book.detail_page_url, book.images.primary.large.url)
# "content.text" is NOT suported as of Feb.2020.
#            contents +=          "<div><blockquote class='blockquote'><p class='mb-0'>{}...<p></blockquote></div><!-- 内容-->\n".format(book.content.text[:200])
            contents +=          "<div><blockquote class='blockquote'><p class='mb-0'>Kindle版(電子書籍) : {}<p></blockquote></div><!-- 価格 -->\n".format(book.offers.listings[0].price.display_amount)
            contents +=          "<div><a href='{}'>本の内容・レビューなど詳細はこちら(Amazonのサイトに遷移します)</a></div><!-- リンク-->\n".format(book.detail_page_url)
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
        contents_ = create_kindle_list()
        post_contents("ビジネス・経済本のおすすめ", contents_)
    except:
        print_exc()
