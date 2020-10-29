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


# with open('json.txt','r',encoding='UTF-8') as f:
#     s=f.read()
# j=json.loads(s)


s3_client = None

url='http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param={'webSiteNo':'01','code':'M1236','locale':'en_US'}



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

    last_language=''
    last_ori=''

    wmap={}
    lmap={}

    def __init__(self):
        print('初始化中。。')
        # self.json_ori = self.read_json_file('json.txt')
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = 'C:\\credentials.txt'

        # find all dir
        alldir = os.scandir()
        for e in alldir:
            if e.is_dir():
                if e.name.startswith('config_'):
                    self.dirs.append(e.name)

        # read wmap and lmap into memory

        with open('wmap.txt', 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                line=line.replace('\n','')
                s = line.split(' ')
                self.wmap[s[2]]=s[0]
                line = f.readline()

        with open('lmap.txt', 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                line=line.replace('\n','')
                s = line.split('_')
                self.lmap[s[0]] = line
                line = f.readline()




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
            for col in range(cols):
                dic[table.cell_value(0, col)] = table.cell_value(row, col)

            self.configs.append(dic)

        # print(list)

    def get_ori_json(self,p):
        lan=p['locale'].split('_')[0]
        code=p['code']
        ori_path='result_' + self.current_dir[7:] + '/' + lan + '_' + code + '.txt'
        j=None
        if os.path.exists(ori_path):
            res=self.read_json_file(ori_path)
            j = res
        else:
            res = requests.get(url=url, params=p)
            j = json.loads(res.text)
            j =json.loads(j['result'])
        return j

    def read_json_file(self, o):
        with open(o, 'r', encoding='UTF-8') as f:
            s = f.read()
            return json.loads(s)

    def write_json_file(self, o, s):
        with open(o, 'w', encoding='UTF-8') as f:
            js = json.dumps(s)
            f.write(js)

    def upload_pic(self, pic_name):
        print()
        print("开始上传图片：" + pic_name)

        pic_path=self.gen_img_path(pic_name)

        lan=pic_name[0:2]
        unpo_locale=['pt','sv','da','nb','is','fi']
        print(lan)


        if os.path.exists(self.current_dir + '/' + pic_name + '.jpg'):
            pic_path += '.jpg'
            upload_file(self.current_dir + '/' + pic_name + '.jpg', 'image.chic-fusion.com', pic_path)
        elif os.path.exists(self.current_dir + '/' + pic_name + '.gif'):
            pic_path += '.gif'
            upload_file(self.current_dir + '/' + pic_name + '.gif', 'image.chic-fusion.com', pic_path)
        else:

            print('未找到图片：' + self.current_dir + '/' + pic_name)
            if lan in unpo_locale:
                pic_name=pic_name.replace(lan,'en')
                pic_path = self.gen_img_path(pic_name)
                print('返回en图片链接：'+pic_path+'jpg')
                return  pic_path + '.jpg'
            else:
                return None
        print('上传成功：https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + pic_path)
        return pic_path

    def is_imgs(self, i, n):

        e = self.configs[i]
        e_plat = e[title_map['plat']]
        e_language = e[title_map['language']]
        e_index = e[title_map['index']]

        i += 1
        if not i < len(self.configs):
            return n
        e = self.configs[i]
        next_e_plat = e[title_map['plat']]
        next_e_language = e[title_map['language']]
        next_e_index = e[title_map['index']]

        if e_plat == next_e_plat:
            if e_language == next_e_language:
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

    def do_config(self):
        global title_map
        a = 1
        i = 0
        while i < len(self.configs):
            print('*' * 20)
            e = self.configs[i]
            print('第' + str(a) + '项配置：')
            print(e)
            a += 1
            try:
                e_plat = e[title_map['plat']]
                e_language = e[title_map['language']]
                e_index = e[title_map['index']]
                e_title = e[title_map['title']]
                e_href = e[title_map['href']]
            except:
                raise AssertionError('config.xlxs标题非法')



            # is images?
            type = 'list'
            n_images = self.is_imgs(i, 0)

            if n_images != 0:
                type = 'images'

            # is image, need titles and hrefs
            e_titles = []
            e_hrefs = []
            if type == 'images':
                for ii in range(n_images + 1):
                    if ii > 0:
                        print(self.configs[i + ii])
                    e_titles.append(self.configs[i + ii][title_map['title']])
                    e_hrefs.append(self.configs[i + ii][title_map['href']])

            i += n_images

            # read origin json file

            global param
            param['webSiteNo']=self.wmap[self.web]
            param['locale']=self.lmap[e_language]

            if e_plat == 'ios':
                param['code']='M1284'
            elif e_plat == 'an':
                param['code']='M1243'

            ori = self.get_ori_json(param)
            pc = None
            pc_old=None
            if e_plat == 'pc':
                pc = ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1]
            elif e_plat == 'ms':
                pc = ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1]
            elif e_plat == 'ios' or e_plat == 'an':
                pc = ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1]
                pc_old = ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1]

            # log
            print('改动前：')
            print(pc)

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
                    m = re.search('.*\/(.*?)\.html', e['href'])
                    if m:
                        id = m.group(1)
                    if e_plat == 'pc' or e_plat == 'ms':
                        pc['href'] = e_href

                        if 'relatedId' in pc:
                            pc['relatedId']=id
                    else:
                        if 'id' in pc:
                            pc['id'] = id
                            pc_old['id'] = id


                # process src (without ios and an images type, and .gif for ios)
                if e_plat == 'pc' or e_plat == 'ms':
                    pic_name_jpg = e_language + '-' + str(int(e_index)) + '-' + e_plat[:1]

                    if 'src' in pc:
                        # path = self.gen_img_path(pic_name_jpg)
                        path = self.upload_pic(pic_name_jpg)

                        pc['src'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path
                else:
                    pic_name_jpg = e_language + '-' + str(int(e_index)) + '-' + 'm'

                    if "titleImage" in pc:
                        path = self.gen_img_path(pic_name_jpg)
                        pc['titleImage'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path + '.jpg'



            # process type-images
            elif type == 'images':
                for x in range(len(e_titles)):

                    if e_titles[x] != '':
                        pc['images'][x]['title'] = e_titles[x]

                    if e_hrefs[x] != '':
                        pc['images'][x]['href'] = e_hrefs[x]

                    # process src
                    pic_name_jpg = e_language + '-' + str(int(e_index)) + '-' + e_plat[:1] + str(x + 1)
                    if 'src' in pc['images'][x]:
                        path = self.gen_img_path(pic_name_jpg)
                        path = self.upload_pic(pic_name_jpg)
                        pc['images'][x]['src'] = 'https://s3-us-west-2.amazonaws.com/image.chic-fusion.com/' + path

            # log
            print()
            print('改动后:')
            print(pc)

            # write
            if e_plat == 'pc':
                ori["__Default_Country__"]["__New_Customer__"]["pc"]["modules"][int(e_index) + 1] = pc
            elif e_plat == 'ms':
                ori["__Default_Country__"]["__New_Customer__"]["msite"]["modules"][int(e_index) + 1] = pc
            elif e_plat == 'ios' or e_plat == 'an':
                ori["__Default_Country__"]["__New_Customer__"]["shopView"][int(e_index) + 1] = pc
                ori["__Default_Country__"]["__Old_Customer__"]["shopView"][int(e_index) + 1] = pc_old

            filepath = 'result_' + self.current_dir[7:]
            if not os.path.exists(filepath):
                os.mkdir(filepath)

            self.last_language = e_language
            self.last_ori = ori

            self.write_json_file(filepath + '/' + e_language + '_' + param['code'] + '.txt', ori)

            i += 1

    def run(self):
        for dir in self.dirs:
            dir_sp = dir.split('_')
            self.web = dir_sp[1]
            self.current_dir = dir
            print('*' * 40)
            print('开始处理文件夹:' + dir)
            self.read_config()
            self.do_config()
            self.configs = []
            self.last_language=''


if __name__ == '__main__':
    g = Gjson()
    g.run()
