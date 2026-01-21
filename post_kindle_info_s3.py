import json
import requests
import time
import os
import boto3
from traceback import print_exc
from urllib.parse import urljoin
from datetime import datetime
from string import Template
from dotenv import load_dotenv

from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException
from paapi5_python_sdk.search_items_request import SearchItemsRequest
from paapi5_python_sdk.search_items_resource import SearchItemsResource
from paapi5_python_sdk.offers_v2 import OffersV2


def get_kindle_books():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)

    AMAZON_ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
    AMAZON_SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
    AMAZON_ASSOC_TAG = os.environ.get("AMAZON_ASSOC_TAG")

    HOST = "webservices.amazon.co.jp"
    REGION = "us-west-2"

    default_api = DefaultApi(
        access_key=AMAZON_ACCESS_KEY, secret_key=AMAZON_SECRET_KEY, host=HOST, region=REGION
    )

    # request paraeters
    KEYWORDS = os.environ.get("KEYWORDS")
    SEARCH_INDEX = os.environ.get("SEARCH_INDEX")
    BROWSE_NODE_ID = os.environ.get("BROWSE_NODE_ID")
    ITEM_COUNT = int(os.environ.get("ITEM_COUNT"))

    # For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter
    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERSV2_LISTINGS_PRICE,        # OffersV2: 新形式（優先）
        SearchItemsResource.OFFERSV2_LISTINGS_DEALDETAILS,  # OffersV2: セール情報
        SearchItemsResource.OFFERS_LISTINGS_PRICE,          # Offers v1: 互換性維持
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


def format_price_info(book):
    """
    OffersV2またはOffers v1から価格情報をフォーマット
    
    Args:
        book: Item オブジェクト
    
    Returns:
        str: フォーマット済み価格情報
    """
    try:
        # OffersV2の場合（優先）
        if hasattr(book, 'offers_v2') and book.offers_v2 and book.offers_v2.listings:
            listing = book.offers_v2.listings[0]
            price_parts = []
            
            # メイン価格
            if listing.price and listing.price.money and listing.price.money.display_amount:
                price_parts.append(listing.price.money.display_amount)
            
            # 割引情報
            if listing.price and listing.price.savings and listing.price.savings.percentage:
                price_parts.append(f"({listing.price.savings.percentage}%OFF)")
            
            # セール情報
            if listing.deal_details and listing.deal_details.badge:
                price_parts.append(f"【{listing.deal_details.badge}】")
            
            if price_parts:
                return " ".join(price_parts)
        
        # Offers v1へのフォールバック
        if book.offers and book.offers.listings:
            return book.offers.listings[0].price.display_amount
        
        return "価格情報なし"
    
    except Exception as e:
        print(f"Error formatting price: {e}")
        return "価格情報なし"


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
            price_info = format_price_info(book)
            contents +=          "<div><blockquote class='blockquote'><p class='mb-0'>Kindle版(電子書籍) : {}<p></blockquote></div><!-- 価格 -->\n".format(price_info)
            contents +=          "<div><a href='{}'>本の内容・レビューなど詳細はこちら(Amazonのサイトに遷移します)</a></div><!-- リンク-->\n".format(book.detail_page_url)
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
        # HTMLテンプレートにKindle本のリストを埋め込む
        t = Template(open('./kindle_list.template').read())
        contents = t.substitute({'kindle_list': kindle_list})
    except Exception as e:
        print(e)
    return contents


def post_to_s3(contents):
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)

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
