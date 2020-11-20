import jsonMod
import os
import tkinter as tk
import tkinter.messagebox
import json

if __name__ == '__main__':
    v_lan_map = {}
    v_code_lan_map = {}
    map_code_lan = {}
    names = locals()
    list_code = []
    list_lan = []
    writepath = ''
    write_value = ''
    websiteno = ''
    jm = jsonMod.JsonMod()


    def cb_code():
        global map_code_lan
        map_code_lan = {}
        list_lan = []
        for code in v_code_lan_map:
            for lan in v_code_lan_map[code]:
                if v_code_lan_map[code][lan].get():
                    if code in map_code_lan:
                        map_code_lan[code].append(lan)
                    else:
                        map_code_lan[code] = []
                        map_code_lan[code].append(lan)

        print(map_code_lan)


    def b_read():
        print('bread')

        global param
        p = param.copy()
        p['webSiteNo'] = e_wbn.get()
        path = e_path.get()
        for code in v_code_lan_map:
            p['code'] = code
            for lan in v_code_lan_map[code]:
                p['locale'] = jm.lmap[lan]
                ori = jm.read_jsonpath_from_Wanna(path, p)
                textarea.delete('1.0', tk.END)
                textarea.insert(tk.END, json.dumps(ori, sort_keys=True, indent=4, separators=(', ', ': ')))


    def b_write():
        try:
            print('bwrite')
            value = e_value.get()
            writepath = e_filepath.get()

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
                    ori = jm.get_ori_json(p)
                    wcl = p['webSiteNo'] + '_' + code + '_' + lan + '.txt'
                    jm.write_jsonpath_to_localfile(path, value, ori, writepath + '/' + wcl)
            tk.messagebox.showinfo(title='', message='写入成功')
        except:
            tk.messagebox.showerror(title='出错了', message='写入错误')


    def b_bk():
        cb_code()
        writepath = e_filepath.get()

        if not os.path.exists(writepath):
            os.mkdir(writepath)

        global map_code_lan
        p = jsonMod.param.copy()
        p['webSiteNo'] = e_wbn.get()
        path = e_path.get()
        for code in map_code_lan:
            p['code'] = code
            for lan in map_code_lan[code]:
                p['locale'] = jm.lmap[lan]
                ori = jm.get_ori_json(p)
                wcl = p['webSiteNo'] + '_' + code + '_' + lan + '.txt'
                try:
                    jm.write_jsonpath_to_localfile(None, None, ori, writepath + '/' + wcl)
                    # tk.messagebox.showinfo(title='', message='备份成功')
                except:
                    pass
                    # tk.messagebox.showerror(title='出错了', message='备份错误')


    def b_hookall():
        jm.get_web_status(e_wbn.get())

        for code in v_code_lan_map:
            for lan in v_code_lan_map[code]:
                v_code_lan_map[code][lan].set(False)

        for web in jm.web_code_lan:
            if web == jm.wmap_reverse[e_wbn.get()]:
                for code in jm.web_code_lan[web]:
                    for lan in jm.web_code_lan[web][code]:
                        v_code_lan_map[code][lan].set(True)
                break


    win = tk.Tk()
    win.title('JsonModGUI v1.0')
    win.geometry('1360x800')
    # textarea
    textarea = tk.Text(win)
    textarea.pack(fill=tk.Y, side=tk.RIGHT)
    # websiteno
    f_wbn = tk.LabelFrame(win, text="websiteno")
    f_wbn.pack(fill=tk.X)
    l_wbn = tk.Label(f_wbn, text='网站编号')
    e_wbn = tk.Entry(f_wbn, text='01')
    b_wbn_hook = tk.Button(f_wbn, text="一键勾选", command=b_hookall)
    b_wbn_bk = tk.Button(f_wbn, text="备份", command=b_bk)

    # code & locale
    for code in jsonMod.all_plat_code:
        v_code_lan_map[code] = {}
        f_varname = 'f_' + code
        names[f_varname] = tk.LabelFrame(win, text=code)
        names[f_varname].pack(fill=tk.X)
        for lan in jsonMod.all_lan:
            v_varname = 'v_' + code + '_' + lan
            names[v_varname] = tk.BooleanVar()
            v_code_lan_map[code][lan] = names[v_varname]

            cb_varname = 'cb_' + code + '_' + lan
            names[cb_varname] = tk.Checkbutton(names[f_varname], text=lan, variable=names[v_varname], onvalue=True,
                                               offvalue=False, command=cb_code)

    # path
    f_path = tk.LabelFrame(win, text="path")
    f_path.pack(fill=tk.X)

    e_path = tk.Entry(f_path, width=100)
    e_path.insert(0, "__Default_Country__/__New_Customer__/pc/modules")
    b_path = tk.Button(f_path, text="读取", command=b_read)

    # write
    f_write = tk.LabelFrame(win, text="path")
    f_write.pack(fill=tk.X)

    l_filepath = tk.Label(f_write, text='输出的文件夹路径')
    e_filepath = tk.Entry(f_write)
    e_filepath.insert(0, 'result')
    l_value = tk.Label(f_write, text='修正后的值')
    e_value = tk.Entry(f_write)
    b_write = tk.Button(f_write, text="写入", command=b_write)

    # pack
    l_wbn.pack(side=tk.LEFT)
    e_wbn.pack(side=tk.LEFT)
    b_wbn_hook.pack(side=tk.RIGHT)
    b_wbn_bk.pack(side=tk.RIGHT)

    for code in jsonMod.all_plat_code:
        for lan in jsonMod.all_lan:
            names['cb_' + code + '_' + lan].pack(side=tk.LEFT)

    e_path.pack(side=tk.LEFT)
    b_path.pack(side=tk.RIGHT)

    l_filepath.pack(side=tk.LEFT)
    e_filepath.pack(side=tk.LEFT)
    b_write.pack(side=tk.RIGHT)
    e_value.pack(side=tk.RIGHT)
    l_value.pack(side=tk.RIGHT)

    win.mainloop()
    jm.end()