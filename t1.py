import requests
import json
# url='http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
# param={'webSiteNo':'01','code':'M1236','locale':'en_US'}
# def download_json():
#     res=requests.get(url=url,params=param)
#     j=json.loads(res.text)
#     print()
#
# st='en-1-i'
# st=st[:-1]+'m'
# print(st)

# str=input('a')
# s=str.split('&')
# result=''
# for e in s:
#     lr=e.split('=')
#     e='"'+lr[0]+'":"'+lr[1]+'", '
#     result+=e
#
# print(result)

r=requests.get('https://api.floryday.com/en/web/v1/Product?lang_code=en&platform=PC&page_code=goods&currency=USD&country_code=US&abs_path=%2FCasual-Color-Block-Shirt-Round-Neckline-Shift-Dress-m118979594&module=reviews&page_number=1&filter=0&isAbtest=1')
ori = json.loads(r.text)
report_date = ori['data']['commentList'][0]['post_datetime']
date=report_date.split('/')


print(report_date)