import xlrd
import csv
import pandas as pd

otitles=[]
def csv2dict(source_file):
    new_dict = {}
    with open(source_file, 'r')as csv_file:
        data = csv.reader(csv_file, delimiter=",")
        global otitles
        line_count = 0

        for row in data:
            if line_count == 0:
                otitles = row.copy()
            else:
                new_dict[line_count] = {}
                for i in range(len(otitles)):
                    new_dict[line_count][otitles[i]] = row[i]
            line_count += 1
    return new_dict


ori_data = {}
title_num_map = {}  # {'qty':{'1':'1',....},'size':{'L':'1','XL':'2',....},....}

ori_data = csv2dict('p0219.csv')

result_data = {}
for id in ori_data:
    result_data[id] = {}
    for title in ori_data[id]:
        # 转成数字并写入result_data
        if title == 'qty':
            result_data[id][title] = ori_data[id][title]
        else:
            if not title in title_num_map:
                title_num_map[title] = {}
            if not ori_data[id][title] in title_num_map[title]:
                title_num_map[title][ori_data[id][title]] = len(title_num_map[title]) + 1

            result_data[id][title] = title_num_map[title][ori_data[id][title]]

with open('result_p0219.csv', mode='w', newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(otitles)
    for e in result_data:
        list=[]
        for ee in result_data[e]:
            list.append(result_data[e][ee])
        writer.writerow(list)

# print('结果'+str(result_data))
print('枚举对应'+str(title_num_map))