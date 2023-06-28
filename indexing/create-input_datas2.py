import pandas as pd
import csv


status_name = {1:'空有/売出中', 3:'空無/売止', 4:'成約', 9:'削除'}
type_name ={1101:'売地', 1102:'借地権譲渡', 1103:'底地権譲渡', 1201:'新築戸建', 1202:'中古戸建', 1203:'新築テラスハウス', 1204:'中古テラスハウス',
            1301:'新築マンション', 1302:'中古マンション', 1303:'新築公団', 1304:'中古公団', 1305:'新築公社', 1306:'中古公社', 1307:'新築タウンハウス', 1308:'中古タウンハウス', 1309:'リゾートマンション',
            1401:'店舗', 1403:'店舗付住宅', 1404:'住宅付店舗', 1405:'事務所', 1406:'店舗・事務所', 1407:'ビル', 1408:'工場', 1409:'マンション', 1410:'倉庫', 1411:'アパート', 1412:'寮', 1413:'旅館', 1414:'ホテル', 1415:'別荘', 1416:'リゾートマン', 1420:'社宅', 1499:'その他',
            1502:'店舗', 1505:'事務所', 1506:'店舗・事務所', 1507:'ビル', 1509:'マンション', 1599:'その他', 3101:'マンション', 3102:'アパート', 3103:'一戸建', 3104:'テラスハウス', 3105:'タウンハウス', 3106:'シェアハウス', 3110:'寮・下宿',
            3201:'店舗(建物全部)', 3202:'店舗(建物一部)', 3203:'事務所', 3204:'店舗・事務所', 3205:'工場', 3206:'倉庫', 3207:'一戸建', 3208:'マンション', 3209:'旅館', 3210:'寮', 3211:'別荘', 3212:'土地', 3213:'ビル', 3214:'住宅付店舗(一戸建)', 3215:'住宅付店舗(建物一部)', 3282:'駐車場', 3299:'その他'}
building_name = {1:'木造', 2:'ブロック', 3:'鉄骨造', 4:'RC', 5:'SRC', 6:'PC', 7:'HPC', 9:'その他', 10:'軽量鉄骨', 11:'ALC', 12:'鉄筋ブロック', 13:'CFT(コンクリート充填鋼管)'}
new_flag_name = {0:'中古', 1:'新築・未入居'}
room_plan_name = {10:'R', 20:'K', 25:'SK', 30:'DK', 35:'SDK', 40:'LK', 45:'SLK', 50:'LDK', 55:'SLDK'}
room_type_name = {1:'和室', 2:'洋室', 3:'DK', 4:'LDK', 5:'L', 6:'D', 7:'K', 9:'その他', 21:'LK', 22:'LD', 23:'S'}
parking_type_name = {1:'空有', 2:'空無', 3:'近隣', 4:'無'}
ok_name = {0:'不可', 1:'可'}
# zip_name = ''
# addr1_name = ''
# addr2_name = ''
# structure_name = ''
# area_name = ''
# room_num_name = ''
# room_plan_name = ''
# roomx_plan_name = []
# roomx_tatami_name = []
# roomx_floor_name = []
# feature_name = ''
# price_name = ''

names = []

def write_output(row, index):
    id = index+1
    f = open('data/property_'+str(id)+'.txt', 'w', encoding='UTF-8')
    outdata = "以下は物件ID=" +str(id)+"の詳細情報です。\n"
    outdata += "・物件ID: " + str(id) + '\n'
    outdata += "・" + names[0] + ': ' + row[0] + '\n'
    outdata += "・" + names[5] + ': ' + status_name[int(row[5])] + '\n'
    outdata += "・" + names[6] + ': ' + type_name[int(row[6])] + '\n'
    outdata += "・" + names[9] + ': ' + row[9] + '\n'
    outdata += "・" + names[14] + ': ' + row[14] + '\n'
    outdata += "・" + names[15] + ': ' + row[15] + '\n'
    outdata += "・" + names[17] + ': ' + row[17] + '\n'
    outdata += "・" + names[18] + ': ' + row[18] + '\n'
    outdata += "・" + names[19] + ': ' + row[19] + '\n'
    outdata += "・" + names[20] + ': ' + row[20] + '\n'
    outdata += "・" + names[70] + ': ' + building_name[int(row[70])] + '\n'
    outdata += "・" + names[72] + ': ' + row[72] + '平米\n'
    outdata += "・" + names[79] + ': ' + new_flag_name[int(row[79])] + '\n'
    outdata += "・" + names[87] + ': ' + row[87] + '\n'
    outdata += "・" + names[88] + ': ' + row[87] + room_plan_name[int(row[88])] + '\n'

    for i in range(10):

        if row[89+i*4].strip() == '':
            #print(i)
            continue
        outdata += '・間取' + str(i+1) +'の種類: ' + room_type_name[int(row[89+i*4])] + '\n'
        outdata += '・間取' + str(i+1) +'の畳数: ' + row[90+i*4] + '畳\n'
        outdata += '・間取' + str(i+1) +'の所在階: ' + row[91+i*4] + '階\n'
        outdata += '・間取' + str(i+1) +'の室数: ' + row[92+i*4] + '室\n'

    outdata += "・" + names[130] + ': ' + row[130] + '\n'
    outdata += "・" + names[138] + ': ' + row[138] + '円\n'
    key_money_unit = 'ヶ月'
    deposit_money_unit = 'ヶ月'
    if (int(row[146]) > 100):
        key_money_unit = '円'
    outdata += names[146] + ': ' + row[146] + key_money_unit + '\n'
    if (int(row[148]) > 100):
        deposit_money_unit = '円'
    outdata += "・" + names[148] + ': ' + row[148] + deposit_money_unit + '\n'

    outdata += "・" + names[179] + ': ' + parking_type_name[int(row[179])] + '\n'

    outdata += "・" + names[410] + ': ' + ok_name[int(row[410])] + '\n'
    outdata += "・" + names[411] + ': ' + ok_name[int(row[411])] + '\n'
    outdata += "・" + names[412] + ': ' + ok_name[int(row[412])] + '\n'

    f.write(outdata)
    f.write('\n')
    f.close()

#出力ファイル
#fout = open('data/out.txt', 'w', encoding='UTF-8')

with open('homes.csv','r',encoding='cp932') as f:
    reader = csv.reader(f)
    for index, row in enumerate(reader):
        #print (row)
        if index == 0:
            pass
        elif index == 1:
            names = row
        else:
            write_output(row, index)


#fout.close()
