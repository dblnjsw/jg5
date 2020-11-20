import requests
import json
import re

url = 'http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param = {'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}
all_lan = ['en', 'fr', 'de', 'es', 'pt', 'sv', 'da', 'nb', 'is', 'fi']
all_plat_code = ['M1236', 'M1284', 'M1243', 'M1316']


class JsonMod():
    wmap_reverse = {}
    web_code_lan = {}
    lmap = {}

    def __init__(self):
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
                self.wmap_reverse[s[0]] = s[2]
                line = f.readline()

        with open('lmap.txt', 'r', encoding='UTF-8') as f:
            line = f.readline()
            while line:
                line = line.replace('\n', '')
                s = line.split('_')
                self.lmap[s[0]] = line
                line = f.readline()

    def end(self):
        self.write_json_file('web_code_lan.txt', self.web_code_lan)

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

    def get_ori_json(self, p):
        """
        该函数通过p参数，获取wanna里特定网站编号、编码类型、语言（locale）的‘json文本’（如果本地result_开头的文件夹下存在该‘json文本’，则读取本地的）
        p参数是字典，示例:{'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}
        """

        lan = p['locale'].split('_')[0]
        code = p['code']
        j = None

        res = requests.get(url=url, params=p)
        j = json.loads(res.text)
        assert j['code'] == 200, '不存在该语言或平台：' + str(p)
        j = json.loads(j['result'])
        assert j
        return j

    def read_jsonpath_from_Wanna(self, path, params):
        """该函数按给定的json路径读取一个wanna上指定的json文件

        :param path: {str}json路径，例："__Default_Country__/__New_Customer__/pc/modules"
        :param params: {dict}访问wanna的参数，例："{'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}"
        :return: {str}/{dict}
        """
        path = path.replace('//', '')
        paths = path.split('/')
        d = self.get_ori_json(params)
        temp_d = d
        for p in paths:
            n = None
            m = re.search('\[(.*)\]', p)

            if m:
                n = eval(m.group(1))
                p = p.replace(m.group(0), '')
            if n is not None:
                temp_d = temp_d[p][n]
            else:
                temp_d = temp_d[p]

        print(temp_d)
        return temp_d

    def read_jsonpath_from_localfile(self, path, filepath):
        pass

    def write_jsonpath_to_localfile(self, path, value, jsonText, writeFilepath):
        if path is None or value is None:
            self.write_json_file(writeFilepath, jsonText)
            return

        path = path.replace('//', '')
        paths = path.split('/')
        d = jsonText
        temp_d = d
        lastKey = paths[len(paths) - 1]
        for i in range(len(paths) - 1):
            n = None
            m = re.search('\[(.*)\]', paths[i])
            if m:
                n = eval(m.group(1))
                paths[i] = paths[i].replace(m.group(0), '')
            if n is not None:
                temp_d = temp_d[paths[i]][n]
            else:
                temp_d = temp_d[paths[i]]

        n = None
        m = re.search('\[(.*)\]', lastKey)
        if m:
            n = eval(m.group(1))
            lastKey = lastKey.replace(m.group(0), '')
        if n is not None:
            temp_d[lastKey][n] = value
        else:
            temp_d[lastKey] = value

        self.write_json_file(writeFilepath, d)

    def get_web_status(self, websiteno):
        """检测网站的状态，如拥有几种编码，每种编码下有几种语言。
        检测的结果存入self.web_code_lan
        """
        self.web = self.wmap_reverse[websiteno]

        if self.web in self.web_code_lan:
            # self.log_dict_format(self.web_code_lan[self.web])
            pass
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
            # self.log_dict_format(self.web_code_lan[self.web])
