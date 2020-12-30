import json
import xlrd
import re
import os
import logging
import boto3
from botocore.exceptions import ClientError
import datetime
import requests
import copy

s = ''
# attr=['index','src','title','href']
title_map = {'plat': '平台', 'language': '语言', 'index': '板块的序号（从轮播图下开始）', 'title': '标题', 'href': '链接'}

code_map = {'pc': 'M1236', 'ms': 'M1236', 'ios': 'M1284', 'an': 'M1243', 'pc1316': 'M1316', 'ms1316': 'M1316'}

unpo_locale = ['fr', 'de', 'es', 'pt', 'sv', 'da', 'nb', 'is', 'fi']

all_lan = ['en', 'fr', 'de', 'es', 'pt', 'sv', 'da', 'nb', 'is', 'fi']

all_plat_code = ['M1236', 'M1284', 'M1243', 'M1316']



# with open('json.txt','r',encoding='UTF-8') as f:
#     s=f.read()
# j=json.loads(s)


s3_client = None

url = 'http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param = {'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}

# configuration
canUpFile = False   #如关闭上传，服务器前缀为https://dgzfssf1la12s.cloudfront.net
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

    web_code_lan = {}

    wmap = {}
    lmap = {}

    s3_prefix = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/'
    dgz_prefix = 'https://dgzfssf1la12s.cloudfront.net/'

    def __init__(self):
        print('WARNNING:小语种的改动将自动跟随英语')
        print('初始化中。。')
        # self.json_ori = self.read_json_file('json.txt')
        if not canUpFile:
            print('关闭上传, 图片不会实际上传')
            # self.s3_prefix=self.dgz_prefix
        else:
            print('上传开启')

        if autoBk:
            print('自动备份开启')
        else:
            print('自动备份关闭')
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
        """该函数通过p参数，获取wanna里特定网站编号、编码类型、语言（locale）的‘json文本’（如果本地result_开头的文件夹下存在该‘json文本’，则读取本地的）
        p参数是字典，示例:{'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}
        """

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

    # read xlxs file named config***
    def read_config(self):
        """该函数读取文件夹下的config.xlxs文件，调用后以下属性会发生变化：
        self.configs
        """
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
        """读取一个json文本
        :arg
        o {str} -- 文件路径
        :returns
        str -- json对象的字符串
        """
        with open(o, 'r', encoding='UTF-8') as f:
            s = f.read()
            return json.loads(s)

    def write_json_file(self, o, s):
        """将一个json对象写入指定文件路径下的文本
        :arg
        o {str} -- 文件路径
        s {dict} -- json对象
        """
        with open(o, 'w', encoding='UTF-8') as f:
            js = json.dumps(s)
            f.write(js)

    def upload_pic(self, picname_postfix):
        """上传图片到亚马逊s3服务器
        :arg
        picname_postfix {str} -- 带后缀的图片名，如：en-1-p.jpg
        """
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
                    raise AssertionError('找不到上传文件')
                else:
                    return pic_path
        else:
            if canUpFile:
                upload_file(self.current_dir + '/' + picname_postfix, 'image.chic-fusion.com', pic_path)
        print('上传成功：https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + pic_path)
        return pic_path

    def is_imgs(self, i, n):
        """用于判断该配置的板块是不是images类型(如：双图板块)
        :arg
        i {int} -- 配置的序号(位于self.configs)
        n {int} -- 图片的个数，初次调用传0
        :returns
        int -- 图片个数
        """

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
        """生成一个路径，用于放入亚马逊服务器
        :arg
        img {str} -- 图片名,如en-1-p
        :returns
        str -- 生成的路径，如：fablistme/20201104/en-1-m1.jpg
        """
        y = str(datetime.datetime.now().year)
        m = str(datetime.datetime.now().month)
        d = str(datetime.datetime.now().day)
        if int(m) < 10:
            m = '0' + str(m)
        if int(d) < 10:
            d = '0' + str(d)
        datestr = y + m + d
        path = self.web + '/' + datestr + '/' + img
        return path

    def get_en_pic_postfix(self, en_picname):
        """获得en开头图片的后缀，如：en-1-p.jpg的后缀为.jpg
        :arg
        en_picname {str} -- en开头的图片名
        :returns
        str or list -- 后缀名，如果双图板块，en图片有两张，则返回存有两个str的list,如:['.jpg','.gif']
        """
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

    def log_dict_format(self, dict):
        """用于输出self.web_code_lan，如：网站fablistme下所有首页code及其支持的语言：M1236: en """
        print()
        print('网站' + self.web + "下所有首页code及其支持的语言：")
        for code in dict:
            for lan in dict[code]:
                if lan == 'en':
                    print(code, end=': en ')
                else:
                    print(lan, end=' ')
            print()

    def get_web_status(self):
        """检测网站的状态，如拥有几种编码，每种编码下有几种语言。
        检测的结果存入self.web_code_lan
        """

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
        """将该网站下的所有的json文本备份到 'bk_网站名' 目录下"""
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
        """最主要的函数，处理self.configs里的配置：修改原json并将结果写入'result_网站'目录下。
        函数较长，需要记住其最外三层逻辑结构：
        while(for(if/else))
        第一层while：遍历每一项配置        while i < len(self.configs):
        第二层for：遍历该项配置的每种语言            for lan in e['title']:
        第三层if/else: 特殊处理images类型的配置               if type == 'list':elif type == 'images':

        """
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

            # 4 values to store logs
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
                global code_map
                param['locale'] = self.lmap[e_language]
                param['code'] = code_map[e_plat]

                ori = self.get_ori_json(param)
                pc = None
                pc_old = None
                pc_GB = None
                if e_plat == 'pc' or e_plat == 'pc1316':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1]
                    if lan == 'en' and 'GB' in ori:
                        pc_GB = ori["GB"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1]
                elif e_plat == 'ms' or e_plat == 'msite' or e_plat == 'ms1316':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1]
                    if lan == 'en' and 'GB' in ori:
                        pc_GB = ori["GB"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1]
                elif e_plat == 'ios' or e_plat == 'an':
                    pc = ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1]
                    pc_old = ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1]

                before.append(copy.deepcopy(pc))
                before_lan.append(e_language)

                # start process pc
                # process type-list
                if type == 'list':
                    # process title
                    if e_title != '':
                        if 'title' in pc:
                            pc['title'] = e_title
                        if e_plat == 'pc' or e_plat == 'ms' or e_plat == 'pc1316' or e_plat == 'ms1316':
                            pc["styledTitle"] = e_title
                            pc["refId"] = e_title.replace(' ', '')
                            if pc_GB:
                                pc_GB["styledTitle"] = e_title
                                pc_GB["refId"] = e_title.replace(' ', '')
                                pc_GB['title'] = e_title
                        else:
                            pc_old['title'] = e_title

                    # process href
                    if e_href != '':
                        m = re.search('.*\/(.*?)\.html', e_href)
                        if m:
                            id = m.group(1)
                        else:
                            raise AssertionError('链接格式有误：' + e_href)
                        if e_plat == 'pc' or e_plat == 'ms' or e_plat == 'pc1316' or e_plat == 'ms1316':
                            pc['href'] = e_href
                            if pc_GB:
                                pc_GB['href'] = e_href

                            if 'relatedId' in pc:
                                pc['relatedId'] = id
                                if pc_GB:
                                    pc_GB['relatedId'] = id

                        else:
                            if 'id' in pc:
                                pc['id'] = id
                                pc_old['id'] = id

                    # process src
                    if e_plat == 'pc' or e_plat == 'ms' or e_plat == 'pc1316' or e_plat == 'ms1316':
                        if 'src' in pc:
                            # path = self.gen_img_path(picname)
                            path = self.upload_pic(picname + postfixs[0])

                            pc['src'] = self.dgz_prefix + path
                            if pc_GB:
                                pc_GB['src'] = self.dgz_prefix + path
                    else:
                        picname = picname[:-1] + 'm'

                        if "titleImage" in pc:
                            path = self.gen_img_path(picname)
                            pc['titleImage'] = self.dgz_prefix + path + \
                                               postfixs[0]
                # process type-images
                elif type == 'images':
                    for x in range(len(e_titles)):

                        if e_titles[x] != '':
                            if 'title' in pc['images'][x]:
                                pc['images'][x]['title'] = e_titles[x][lan]
                            if pc_GB:
                                pc_GB['images'][x]['title'] = e_titles[x][lan]

                        if e_hrefs[x] != '':
                            m = re.search('.*\/(.*?)\.html', e_href)
                            if m:
                                id = m.group(1)
                            if 'deepLink' in pc['images'][x]:
                                pc['images'][x]['deepLink']['params'][0] = id
                                pc['images'][x]['deepLink']['params'][1] = e_titles[x][lan]
                            if 'href' in pc['images'][x]:
                                pc['images'][x]['href'] = e_hrefs[x]
                            if pc_GB:
                                pc_GB['images'][x]['href'] = e_hrefs[x]

                        if 'refId' in pc['images'][x]:
                            pc['images'][x]['refId'] = e_titles[x]['en']
                            if pc_GB:
                                pc_GB['images'][x]['refId'] = e_titles[x]['en']

                        # process src
                        if e_plat == 'pc' or e_plat == 'ms' or e_plat == 'pc1316' or e_plat == 'ms1316':
                            pass
                        else:
                            picname = picname[:-1] + 'm'
                        picname_num = picname + str(x + 1)
                        if 'src' in pc['images'][x]:
                            path = self.upload_pic(picname_num + postfixs[x])
                            pc['images'][x]['src'] = self.dgz_prefix + path
                        if 'imageUrl' in pc['images'][x]:
                            path = self.upload_pic(picname_num + postfixs[x])
                            pc['images'][x][
                                'imageUrl'] = self.dgz_prefix + path

                after.append(copy.deepcopy(pc))
                after_lan.append(e_language)
                # write
                if e_plat == 'pc' or e_plat == 'pc1316':
                    ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1] = pc
                    if lan == 'en' and 'GB' in ori:
                        ori["GB"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1] = pc_GB
                elif e_plat == 'ms' or e_plat == 'msite' or e_plat == 'ms1316':
                    ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1] = pc
                    if lan == 'en' and 'GB' in ori:
                        ori["GB"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1] = pc_GB
                elif e_plat == 'ios' or e_plat == 'an':
                    ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1] = pc
                    ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1] = pc_old

                # self.last_language = e_language
                # self.last_ori = ori

                self.write_json_file(self.resultfilepath + '/' + e_language + '_' + param['code'] + '.txt', ori)

            # log
            print()
            for l in range(len(before)):
                print(before_lan[l])
                print('改动前：')
                print(json.dumps(before[l], sort_keys=True, indent=4, separators=(', ', ': ')))
                print('改动后：')
                print(json.dumps(after[l], sort_keys=True, indent=4, separators=(', ', ': ')))
                print()

            i += 1

    def run(self):
        for dir in self.dirs:
            # process some variables
            dir_sp = dir.split('_')
            self.web = dir_sp[1].replace('.', '_')
            param['webSiteNo'] = self.wmap[self.web]
            self.current_dir = dir

            print('*' * 40)
            print('开始处理文件夹:' + dir)

            self.get_web_status()
            self.read_config()
            self.do_config()
            self.auto_bk()
            self.configs = []

        self.write_json_file('web_code_lan.txt', self.web_code_lan)


if __name__ == '__main__':
    g = Gjson()
    g.run()
