import requests
import json
url='http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param={'webSiteNo':'01','code':'M1236','locale':'en_US'}
def download_json():
    res=requests.get(url=url,params=param)
    j=json.loads(res.text)
    print()

download_json()