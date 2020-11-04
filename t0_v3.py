import json
import xlrd
import re
import os
import logging
import boto3
from botocore.exceptions import ClientError
import datetime
import requests

s = ''
# attr=['index','src','title','href']
title_map = {'plat': '平台', 'language': '语言', 'index': '板块的序号（从轮播图下开始）', 'title': '标题', 'href': '链接'}

code_map = {'pc': 'M1236', 'ms': 'M1236', 'ios': 'M1284', 'an': 'M1243'}

unpo_locale = ['pt', 'sv', 'da', 'nb', 'is', 'fi']

all_lan = ['en', 'fr', 'de', 'es', 'pt', 'sv', 'da', 'nb', 'is', 'fi']

all_plat_code = ['M1236', 'M1284', 'M1243']

# with open('json.txt','r',encoding='UTF-8') as f:
#     s=f.read()
# j=json.loads(s)


s3_client = None

url = 'http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param = {'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}

# configuration
canUpFile = False
autoBk = True


def upload_file(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    global s3_client
    # Upload the file
    if s3_client is None:
        s3_client = boto3.client('s3')

    try:
        response = s3_client.upload_file(file_name, bucket, object_name, ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        logging.error(e)
        return False
    return True


class Gjson():
    configs = []
    dirs = []
    current_dir = ''

    last_language = ''
    last_ori = ''

    web_code_lan = {}

    wmap = {}
    lmap = {}

    def __init__(self):
        print('WARNNING:小语种的改动将自动跟随英语')
        print('初始化中。。')
        # self.json_ori = self.read_json_file('json.txt')
        if not canUpFile:
            print('假上传开启, 图片不会实际上传')

        if autoBk:
            print('自动备份开启')
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = 'C:\\credentials.txt'

        # find all dir
        alldir = os.scandir()
        for e in alldir:
            if e.is_dir():
                if e.name.startswith('config_'):
                    self.dirs.append(e.name)

        # read web_code_lan, wmap and lmap  into memory
        try:
            self.web_code_lan = self.read_json_file('web_code_lan.txt')
        except:
            self.web_code_lan = {}

        with open('wmap.txt', 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                line = line.replace('\n', '')
                s = line.split(' ')
                self.wmap[s[2]] = s[0]
                line = f.readline()

        with open('lmap.txt', 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                line = line.replace('\n', '')
                s = line.split('_')
                self.lmap[s[0]] = line
                line = f.readline()

    def get_ori_json(self, p):
        lan = p['locale'].split('_')[0]
        code = p['code']
        ofile = 'result_' + self.current_dir[7:] + '/' + lan + '_' + code + '.txt'
        j = None
        if os.path.exists(ofile):
            res = self.read_json_file(ofile)
            j = res
        else:
            res = requests.get(url=url, params=p)
            j = json.loads(res.text)
            assert j['code'] == 200, '不存在该语言或平台：' + str(p)
            j = json.loads(j['result'])
        assert j
        return j

    # def write_result(self):

    # read xlxs file named config***
    def read_config(self):
        # self.config_jsons=self.read_json_file('config.txt')
        config_xlxs_path = self.current_dir + "/config.xlsx"
        assert os.path.exists(config_xlxs_path), config_xlxs_path + '不存在'

        workbook = xlrd.open_workbook(config_xlxs_path)
        table = workbook.sheet_by_name('Sheet1')
        rows = table.nrows
        cols = table.ncols
        for row in range(1, rows):
            dic = {}
            ldic = {}
            lanlist = []
            if table.cell_value(row, 0) == '':
                continue

            for col in range(cols):
                value = table.cell_value(row, col)
                title_value = table.cell_value(0, col)

                if title_value == '平台':
                    lanlist = self.web_code_lan[self.web][code_map[value]].copy()
                if title_value.count('语') > 0:
                    ma = re.search('（(.*)）', title_value)
                    assert ma, '表头语言错误'
                    if value == '':
                        continue
                    e_language = ma.group(1)
                    # if lanlist.__contains__(e_language):
                    lanlist.remove(e_language)
                    if table.cell_value(row, col) != '':
                        ldic[e_language] = value
                else:

                    if isinstance(value, float):
                        dic[table.cell_value(0, col)] = int(value)
                    else:
                        dic[table.cell_value(0, col)] = value

            for unpopl in lanlist:
                ldic[unpopl] = ldic['en']

            dic['title'] = ldic
            self.configs.append(dic)

        # print(list)

    def read_json_file(self, o):
        with open(o, 'r', encoding='UTF-8') as f:
            s = f.read()
            return json.loads(s)

    def write_json_file(self, o, s):
        with open(o, 'w', encoding='UTF-8') as f:
            js = json.dumps(s)
            f.write(js)

    def upload_pic(self, picname_postfix):
        print()
        print("开始上传图片：" + picname_postfix)

        pic_path = self.gen_img_path(picname_postfix)

        lan = picname_postfix[0:2]

        if not os.path.exists(self.current_dir + '/' + picname_postfix):
            print('未找到图片：' + self.current_dir + '/' + picname_postfix)
            if lan in unpo_locale:
                picname_postfix = picname_postfix.replace(lan, 'en')
                pic_path = self.gen_img_path(picname_postfix)
                print('返回en图片链接：' + pic_path)
                return pic_path
            else:
                if canUpFile:
                    return None
                else:
                    return pic_path
        else:
            if canUpFile:
                upload_file(self.current_dir + '/' + picname_postfix, 'image.chic-fusion.com', pic_path)
        print('上传成功：https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + pic_path)
        return pic_path

    def is_imgs(self, i, n):

        e = self.configs[i]
        e_plat = e[title_map['plat']]
        # e_language = e[title_map['language']]
        e_index = e[title_map['index']]

        i += 1
        if not i < len(self.configs):
            return n
        e = self.configs[i]
        next_e_plat = e[title_map['plat']]
        # next_e_language = e[title_map['language']]
        next_e_index = e[title_map['index']]

        if e_plat == next_e_plat:
            if e_index == next_e_index:
                n += 1
                return self.is_imgs(i, n)
        return n

    def gen_img_path(self, img):
        y = str(datetime.datetime.now().year)
        m = str(datetime.datetime.now().month)
        d = str(datetime.datetime.now().day)
        if int(m) < 10:
            m = '0' + str(m)
        if int(d) < 10:
            d = '0' + str(d)
        datestr = y + m + d
        path = 'zwb/' + self.web + '/' + datestr + '/' + img
        return path

    def get_en_pic_postfix(self, en_picname):
        allpic = os.scandir(self.current_dir)
        postfixs = []
        for e in allpic:
            if e.name.startswith(en_picname):
                postfix = e.name.replace(en_picname, '')
                postfixs.append(postfix)
        if len(postfixs) > 1:
            for i in range(len(postfixs)):
                postfixs[i] = postfixs[i][1:]
        if len(postfixs) < 1:
            if canUpFile:
                raise AssertionError('找不到图片')
            else:
                postfixs.append('.jpg')
        return postfixs

    def add_unpo_lan_title(self):
        # global param
        # p=param
        # p['locale']=self.lmap['pt']
        #
        # res = requests.get(url=url, params=p)
        pass

    def log_dict_format(self, dict):
        print()
        print('网站' + self.web + "下所有首页code及其支持的语言：")
        for code in dict:
            for lan in dict[code]:
                if lan == 'en':
                    print(code, end=': en ')
                else:
                    print(lan, end=' ')
            print()

    def log_web_status(self):

        if self.web in self.web_code_lan:
            self.log_dict_format(self.web_code_lan[self.web])
        else:
            self.web_code_lan[self.web] = {}
            global param
            p = param

            for code in all_plat_code:
                # p['webSiteNo']=self.wmap[self.web]
                p['code'] = code
                for lan in all_lan:
                    p['locale'] = self.lmap[lan]
                    res = json.loads(requests.get(url=url, params=p).text)
                    if lan == 'en':
                        if res['code'] == 200:
                            self.web_code_lan[self.web][code] = []
                            self.web_code_lan[self.web][code].append(lan)
                        else:
                            break
                    else:
                        if res['code'] == 200:
                            self.web_code_lan[self.web][code].append(lan)
            self.log_dict_format(self.web_code_lan[self.web])

    def auto_bk(self):
        global param
        p = param.copy()
        bk_file = 'bk_' + self.web
        for code in self.web_code_lan[self.web]:
            p['code'] = code
            for locale in self.web_code_lan[self.web][code]:
                p['locale'] = self.lmap[locale]
                res = json.loads(requests.get(url=url, params=p).text)
                if not os.path.exists(bk_file):
                    os.mkdir(bk_file)
                self.write_json_file(bk_file + '/' + locale + '_' + code + '.txt', json.loads(res['result']))

    def do_config(self):
        # assign value to resultfilepath
        self.resultfilepath = 'result_' + self.current_dir[7:]
        if not os.path.exists(self.resultfilepath):
            os.mkdir(self.resultfilepath)

        global title_map
        a = 1
        i = 0
        while i < len(self.configs):
            # log config item
            print('*' * 20)
            e = self.configs[i]
            print('第' + str(a) + '项配置：')
            print(e)
            a += 1

            # assign 3 params
            try:
                e_plat = e[title_map['plat']]
                # e_language = e[title_map['language']]
                e_index = e[title_map['index']]
                # e_title = e[title_map['title']]
                e_href = e[title_map['href']]
            except:
                raise AssertionError('config.xlxs标题非法')

            postfixs = self.get_en_pic_postfix('en-' + str(e_index) + '-' + e_plat[:1])

            # is images?
            type = 'list'
            n_images = self.is_imgs(i, 0)

            if n_images != 0:
                type = 'images'

            # is image, need titles and hrefs
            e_titles = []
            e_hrefs = []
            if type == 'images':
                if len(postfixs) != n_images + 1:
                    if canUpFile:
                        raise AssertionError('找不到图片')
                    else:
                        for k in range(n_images + 1):
                            postfixs.append('.jpg')
                for ii in range(n_images + 1):
                    if ii > 0:
                        print(self.configs[i + ii])
                    e_titles.append(self.configs[i + ii]['title'])
                    e_hrefs.append(self.configs[i + ii][title_map['href']])

            i += n_images

            # 2 values to store logs
            before = []
            before_lan = []
            after = []
            after_lan = []

            for lan in e['title']:

                e_language = lan
                e_title = e['title'][lan]
                picname = e_language + '-' + str(int(e_index)) + '-' + e_plat[:1]

                # read origin json file
                global param
                param['locale'] = self.lmap[e_language]

                if e_plat == 'ios':
                    param['code'] = 'M1284'
                elif e_plat == 'an':
                    param['code'] = 'M1243'
                else:
                    param['code'] = 'M1236'

                ori = self.get_ori_json(param)
                pc = None
                pc_old = None
                if e_plat == 'pc':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1]
                elif e_plat == 'ms' or e_plat == 'msite':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1]
                elif e_plat == 'ios' or e_plat == 'an':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1]
                    pc_old = ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1]

                before.append(pc)
                before_lan.append(e_language)

                # start process pc
                # process type-list
                if type == 'list':
                    # process title
                    if e_title != '':
                        pc['title'] = e_title
                        if e_plat == 'pc' or e_plat == 'ms':
                            pc["styledTitle"] = e_title
                            pc["refId"] = e_title.replace(' ', '')
                        else:
                            pc_old['title'] = e_title

                    # process href (without ios and an)
                    if e_href != '':
                        m = re.search('.*\/(.*?)\.html', e_href)
                        if m:
                            id = m.group(1)
                        else:
                            raise AssertionError('链接格式有误：' + e_href)
                        if e_plat == 'pc' or e_plat == 'ms':
                            pc['href'] = e_href

                            if 'relatedId' in pc:
                                pc['relatedId'] = id
                        else:
                            if 'id' in pc:
                                pc['id'] = id
                                pc_old['id'] = id

                    # process src (without ios and an images type)
                    if e_plat == 'pc' or e_plat == 'ms':
                        if 'src' in pc:
                            # path = self.gen_img_path(picname)
                            path = self.upload_pic(picname + postfixs[0])

                            pc['src'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path
                    else:
                        picname[-1] = 'm'

                        if "titleImage" in pc:
                            path = self.gen_img_path(picname)
                            pc['titleImage'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path + \
                                               postfixs[0]
                # process type-images
                elif type == 'images':
                    for x in range(len(e_titles)):

                        if e_titles[x] != '':
                            pc['images'][x]['title'] = e_titles[x][lan]

                        if e_hrefs[x] != '':
                            pc['images'][x]['href'] = e_hrefs[x]

                        # process src
                        picname_num = picname + str(x + 1)
                        if 'src' in pc['images'][x]:
                            path = self.upload_pic(picname_num + postfixs[x])
                            pc['images'][x]['src'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path

                after.append(pc)
                after_lan.append(e_language)
                # write
                if e_plat == 'pc':
                    ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1] = pc
                elif e_plat == 'ms' or e_plat == 'msite':
                    ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1] = pc
                elif e_plat == 'ios' or e_plat == 'an':
                    ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1] = pc
                    ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1] = pc_old

                # self.last_language = e_language
                # self.last_ori = ori

                self.write_json_file(self.resultfilepath + '/' + e_language + '_' + param['code'] + '.txt', ori)

            # log
            print()
            print('改动前：')
            for l in range(len(before)):
                print(before_lan[l])
                print(json.dumps(before[l], sort_keys=True, indent=4, separators=(', ', ': ')))
            print('改动后：')
            for l in range(len(after)):
                print(after_lan[l])
                print(json.dumps(after[l], sort_keys=True, indent=4, separators=(', ', ': ')))

            i += 1

    def run(self):
        for dir in self.dirs:
            dir_sp = dir.split('_')
            self.web = dir_sp[1]
            param['webSiteNo'] = self.wmap[self.web]
            self.current_dir = dir
            print('*' * 40)
            print('开始处理文件夹:' + dir)
            self.log_web_status()
            self.read_config()
            self.do_config()
            self.auto_bk()
            self.configs = []
            self.last_language = None
            self.web = None
        self.write_json_file('web_code_lan.txt', self.web_code_lan)


if __name__ == '__main__':
    g = Gjson()
    g.run()
