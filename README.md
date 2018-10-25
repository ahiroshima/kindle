# 概要
- Amazon Product Advertising APIを利用して、指定したノードのKindle本リストを取得
- 取得したデータをHTMLにパースし、WordPressに投稿する

# 環境
下記クレデンシャルは環境変数から取得
AMAZON_ACCESS_KEY
AMAZON_SECRET_KEY
AMAZON_ASSOC_TAG
WP_USER
WP_PASS

# セットアップ
pip install -r requirements.txt

Raspberry piで動かす時に
- Couldn't find a tree builder with the features you requested: lxml. Do you need to install a parser library?
とエラーが出たら、
sudo apt install python-lxml
を実行すると解決する。

# 前提
Amazon Product Advertising APIを利用する為にはアマゾンアソシエイトへの登録が必要です
