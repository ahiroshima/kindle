import time
import requests
import os
from flask import Flask

from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException
from paapi5_python_sdk.search_items_request import SearchItemsRequest
from paapi5_python_sdk.search_items_resource import SearchItemsResource


app = Flask(__name__)

@app.route('/')
def parseHTML():

    responses = getResponses()
    content = """
            <!doctype html>
            <html lang="ja">
              <head>
                <title>Kindle Books</title>
                <!-- Required meta tags -->
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

                <!-- Bootstrap CSS -->
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
              </head>
              <body>
                <div class='container'>
            """
    for response in responses:
        try:
            content += "<div class='row'>"
            content +=      "<div class='col-md-10 col-md-offset-1'>"
            content +=          "<div><h3>{}</h3></div>\n\n".format(response.item_info.title.display_value)
            content +=          "<div>著者：{}</div>".format(response.item_info.by_line_info.contributors[0].name)
            content +=          "<div><a href = '{}'><img src = '{}'></a></div><!-- 画像-->\n".format(response.detail_page_url, response.images.primary.large.url)
# 2020.2月時点でPA-APIのレスポンスにEditorialReviewsが実装されていない為、内容の取得ができない
#            content +=          "<div><blockquote class='blockquote'><p class='mb-0'>{}<p></blockquote></div><!-- 内容-->\n".format(response.content)
            content +=          "<div><blockquote class='blockquote'><p class='mb-0'>{}<p></blockquote></div><!-- 価格 -->\n".format(response.offers.listings[0].price.display_amount)
            content +=          "<div><a href='{}'>詳細はこちら</a></div><!-- リンク-->\n".format(response.detail_page_url)
            content +=      "</div>"
            content += "</div>"
            content += "<hr>"
        except Exception as e:
            content +=      "</div>"
            content+= "</div>"
            print(e)

    content += """
            </div>
            <!-- Optional JavaScript -->
            <!-- jQuery first, then Popper.js, then Bootstrap JS -->
            <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js" integrity="sha384-vFJXuSJphROIrBnz7yo7oB41mKfc8JzQZiCq4NCceLEaO4IHwicKwpJf9c9IpFgh" crossorigin="anonymous"></script>
            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js" integrity="sha384-alpBpkh1PFOepccYVYDB4do5UnbKysX5WZXm3XxPqe5iKTfUKjNkCk9SaVuEZflJ" crossorigin="anonymous"></script>
          </body>
        </html>
        """
    return content


def getResponses():
    AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY')
    AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY')
    AMAZON_ASSOC_TAG = os.environ.get('AMAZON_ASSOC_TAG')

    host = "webservices.amazon.co.jp"
    region = "us-west-2"

    default_api = DefaultApi(
        access_key=AMAZON_ACCESS_KEY, secret_key=AMAZON_SECRET_KEY, host=host, region=region
    )

    keywords = "*"
    search_index = "KindleStore"
    browse_node_id = "2291905051"
    item_count = 10

    """ For more details, refer: https://webservices.amazon.com/paapi5/documentation/search-items.html#resources-parameter """
    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.ITEMINFO_BYLINEINFO,
        SearchItemsResource.ITEMINFO_CONTENTINFO,
        SearchItemsResource.ITEMINFO_TECHNICALINFO,
        SearchItemsResource.IMAGES_PRIMARY_LARGE
    ]

    """ Forming request """
    try:
        search_items_request = SearchItemsRequest(
            partner_tag=AMAZON_ASSOC_TAG,
            partner_type=PartnerType.ASSOCIATES,
            keywords=keywords,
            search_index=search_index,
            browse_node_id=browse_node_id,
            item_count=item_count,
            resources=search_items_resource,
        )
    except ValueError as exception:
        print("Error in forming SearchItemsRequest: ", exception)
        return

    try:
        """ Sending request """
        response = default_api.search_items(search_items_request)
        print("Complete Response:", response)

        """ Parse response """
        if response.errors is not None:
            print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
            print("Error code", response.errors[0].code)
            print("Error message", response.errors[0].message)

        if response.search_result is not None:
            print("API called Successfully")
            return(response.search_result.items)

    except ApiException as exception:
        print("Error calling PA-API 5.0!")
        print("Status code:", exception.status)
        print("Errors :", exception.body)
        print("Request ID:", exception.headers["x-amzn-RequestId"])

    except TypeError as exception:
        print("TypeError :", exception)

    except ValueError as exception:
        print("ValueError :", exception)

    except Exception as exception: #503エラーが出たら再取得する
        print("Exception :", exception)
        print("再取得しています....")
        time.sleep(3)

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=8080)
