import requests
import json
import os
import tkinter as tk
import tkinter.messagebox
import re

url = 'http://54.222.221.139:8088/wanna-console/wanna/message/anon/get'
param = {'webSiteNo': '01', 'code': 'M1236', 'locale': 'en_US'}
class JsonMod():
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

    def read_jsonpath_from_Wanna(self,path,params):
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
            n=None
            m = re.search('\[(.*)\]', p)

            if m:
                n = eval(m.group(1))
                p=p.replace(m.group(0),'')
            if n is not None:
                temp_d = temp_d[p][n]
            else:
                temp_d = temp_d[p]

        print(temp_d)
        return temp_d

    def read_jsonpath_from_localfile(self,path,filepath):
        pass

    def write_jsonpath_to_localfile(self,path,value,jsonText,writeFilepath):
        path = path.replace('//', '')
        paths = path.split('/')
        d = jsonText
        temp_d = d
        lastKey = paths[len(paths)-1]
        for i in range(len(paths)-1):
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

        self.write_json_file(writeFilepath,d)





if __name__ == '__main__':
    list_code = []
    list_lan = []
    writepath=''
    write_value=''
    websiteno=''
    jm=JsonMod()

    def cb_code():
        global list_lan,list_code
        list_code=[]
        list_lan=[]
        if v_c1236.get():
            list_code.append("M1236")
        if v_c1316.get():
            list_code.append("M1316")
        if v_c1284.get():
            list_code.append("M1284")
        if v_c1243.get():
            list_code.append("M1243")

        if v_en.get():
            list_lan.append("en_US")
        if v_fr.get():
            list_lan.append("fr_FR")
        if v_de.get():
            list_lan.append("de_DE")
        if v_es.get():
            list_lan.append("es_ES")
        if v_pt.get():
            list_lan.append("pt_BR")
        if v_sv.get():
            list_lan.append("sv_SE")
        if v_da.get():
            list_lan.append("da_DK")
        if v_nb.get():
            list_lan.append("nb_NO")
        if v_is.get():
            list_lan.append("is_IS")
        if v_fi.get():
            list_lan.append("fi_FI")

        print(list_code)
        print(list_lan)

    def b_read():
        print('bread')

        global param
        p=param.copy()
        p['webSiteNo']=e_wbn.get()
        path=e_path.get()
        for code in list_code:
            p['code'] = code
            for lan in list_lan:
                p['locale'] = lan
                ori=jm.read_jsonpath_from_Wanna(path,p)
                textarea.delete('1.0',tk.END)
                textarea.insert(tk.END,json.dumps(ori, sort_keys=True, indent=4, separators=(', ', ': ')))

    def b_write():
        try:
            print('bwrite')
            value=e_value.get()
            writepath=e_filepath.get()

            if not os.path.exists(writepath):
                os.mkdir(writepath)

            global param
            p = param.copy()
            p['webSiteNo'] = e_wbn.get()
            path = e_path.get()
            for code in list_code:
                p['code'] = code
                for lan in list_lan:
                    p['locale'] = lan
                    ori=jm.get_ori_json(p)
                    wcl=p['webSiteNo']+'_'+code+'_'+lan+'.txt'
                    jm.write_jsonpath_to_localfile(path,value,ori,writepath+'/'+wcl)
        except:
            tk.messagebox.showerror(title='出错了',message='写入错误')
        tk.messagebox.showinfo(title='',message='写入成功')


    win=tk.Tk()
    win.title('JsonMod v1.0')
    win.geometry('1360x800')
    #textarea
    textarea=tk.Text(win)
    textarea.pack(fill=tk.Y,side=tk.RIGHT)
    #websiteno
    f_wbn=tk.LabelFrame(win,text="websiteno")
    f_wbn.pack(fill=tk.X)
    l_wbn=tk.Label(f_wbn,text='网站编号')
    e_wbn=tk.Entry(f_wbn,text='01')

    #code
    v_c1316=tk.BooleanVar()
    v_c1236=tk.BooleanVar()
    v_c1284=tk.BooleanVar()
    v_c1243=tk.BooleanVar()

    f_c=tk.LabelFrame(win,text="code")
    f_c.pack(fill=tk.X)
    cb_c1316 = tk.Checkbutton(f_c, text='M1316', variable=v_c1316, onvalue=True, offvalue=False, command=cb_code)
    cb_c1236 = tk.Checkbutton(f_c, text='M1236', variable=v_c1236, onvalue=True, offvalue=False, command=cb_code)
    cb_c1284 = tk.Checkbutton(f_c, text='M1284', variable=v_c1284, onvalue=True, offvalue=False, command=cb_code)
    cb_c1243 = tk.Checkbutton(f_c, text='M1243', variable=v_c1243, onvalue=True, offvalue=False, command=cb_code)

    #locale
    v_en = tk.BooleanVar()
    v_fr = tk.BooleanVar()
    v_de = tk.BooleanVar()
    v_es = tk.BooleanVar()
    v_pt = tk.BooleanVar()
    v_sv = tk.BooleanVar()
    v_da = tk.BooleanVar()
    v_nb = tk.BooleanVar()
    v_is = tk.BooleanVar()
    v_fi = tk.BooleanVar()

    f_locale = tk.LabelFrame(win, text="locale")
    f_locale.pack(fill=tk.X)

    cb_locale_en = tk.Checkbutton(f_locale, text='en', variable=v_en, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_fr = tk.Checkbutton(f_locale, text='fr', variable=v_fr, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_de = tk.Checkbutton(f_locale, text='de', variable=v_de, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_es = tk.Checkbutton(f_locale, text='es', variable=v_es, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_pt = tk.Checkbutton(f_locale, text='pt', variable=v_pt, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_sv = tk.Checkbutton(f_locale, text='sv', variable=v_sv, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_da = tk.Checkbutton(f_locale, text='da', variable=v_da, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_nb = tk.Checkbutton(f_locale, text='nb', variable=v_nb, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_is = tk.Checkbutton(f_locale, text='is', variable=v_is, onvalue=True, offvalue=False, command=cb_code)
    cb_locale_fi = tk.Checkbutton(f_locale, text='fi', variable=v_fi, onvalue=True, offvalue=False, command=cb_code)

    #path
    f_path = tk.LabelFrame(win, text="path")
    f_path.pack(fill=tk.X)

    e_path=tk.Entry(f_path,width=100)
    e_path.insert(0,"__Default_Country__/__New_Customer__/pc/modules")
    b_path=tk.Button(f_path,text="读取", command=b_read)

    #write
    f_write = tk.LabelFrame(win, text="path")
    f_write.pack(fill=tk.X)

    l_filepath=tk.Label(f_write,text='输出的文件夹路径')
    e_filepath=tk.Entry(f_write)
    e_filepath.insert(0,'result')
    l_value=tk.Label(f_write,text='修正后的值')
    e_value=tk.Entry(f_write)
    b_write=tk.Button(f_write,text="写入", command=b_write)



    #pack
    l_wbn.pack(side=tk.LEFT)
    e_wbn.pack(side=tk.LEFT)
    cb_c1316.pack(side=tk.LEFT)
    cb_c1236.pack(side=tk.LEFT)
    cb_c1284.pack(side=tk.LEFT)
    cb_c1243.pack(side=tk.LEFT)

    cb_locale_en.pack(side=tk.LEFT)
    cb_locale_fr.pack(side=tk.LEFT)
    cb_locale_de.pack(side=tk.LEFT)
    cb_locale_es.pack(side=tk.LEFT)
    cb_locale_pt.pack(side=tk.LEFT)
    cb_locale_sv.pack(side=tk.LEFT)
    cb_locale_da.pack(side=tk.LEFT)
    cb_locale_nb.pack(side=tk.LEFT)
    cb_locale_is.pack(side=tk.LEFT)
    cb_locale_fi.pack(side=tk.LEFT)

    e_path.pack(side=tk.LEFT)
    b_path.pack(side=tk.RIGHT)

    l_filepath.pack(side=tk.LEFT)
    e_filepath.pack(side=tk.LEFT)
    b_write.pack(side=tk.RIGHT)
    e_value.pack(side=tk.RIGHT)
    l_value.pack(side=tk.RIGHT)





    win.mainloop()