import datetime
import sqlite3
import json
import requests
from config import config
import string
import random
import re
import time
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageFilter
import io, os

status_user = {
    0: 'Забанен',
    1: 'Работает'
}

# DB METHODS
def GetUsers():
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `users` WHERE 1")
    results = cursor.fetchall()
    conn.close()
    return results

def GetUser(id_):
    try:
        id_ = int(id_)
        conn = sqlite3.connect(config['db_name'])
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `users` WHERE `userid`={id_}")
        results = cursor.fetchall()
        conn.close()
        return results[0]
    except:
        return []

def AddUser(message):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `users` WHERE `userid`={message.from_user.id}")
    if cursor.fetchall() == []:
        cursor.execute("INSERT INTO `users` VALUES (NULL, {}, '{}', '{}', 1, {}, 0, 0)".format(
            message.from_user.id, message.from_user.username, message.from_user.first_name, int(datetime.datetime.now().timestamp())))
        conn.commit()
    conn.close()

def AddCount(userid, count):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute(f"UPDATE `users` SET `count`=`count`+{count} WHERE `userid`={userid}")
    conn.commit()
    conn.close()

def AddBuyCount(userid, count):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute(f"UPDATE `users` SET `buycount`=`buycount`+{count} WHERE `userid`={userid}")
    conn.commit()
    conn.close()







# QIWI
def GetHistoryPayments():
    parameters = {'rows': 10, 'nextTxnId': '', 'nextTxnDate': ''}
    r = requests.get(f'https://edge.qiwi.com/payment-history/v2/persons/{config["qiwi_number"]}/payments', params=parameters, headers={
        'accept': 'application/json',
        'Authorization': 'Bearer ' + config['qiwi_token']
    })
    return r.text

def CheckPayment(summa, comment):
    summa = int(summa)
    js = json.loads(GetHistoryPayments())
    for i in js['data']:
        #Logging(i, 'PAYMENT', 'QIWI')
        if i['type'] == 'IN' and i['status'] == 'SUCCESS':
            if i['sum']['amount'] == summa and i['sum']['currency'] == 643:
                if i['comment'] == comment:
                    return True
    return False

def CreatePayment(userid, summa, comment):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute("INSERT INTO `payments` VALUES (NULL, {}, {}, '{}', 'WAIT', '', {}, '')".format(
        userid, summa, comment, round(time.time())))
    conn.commit()
    conn.close()
    
def GetPayment(userid, summa, comment):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `payments` WHERE `userid`={} AND `summa`={} AND `comment`='{}'".format(
        userid, summa, comment))
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

def UpdatePayment(userid, summa, comment, status):
    conn = sqlite3.connect(config['db_name'])
    cursor = conn.cursor()
    cursor.execute(f"UPDATE `payments` SET `status`='{status}' WHERE `userid`={userid} AND `summa`={summa} AND `comment`='{comment}'")
    conn.commit()
    conn.close()





# OTHER METHODS
def GenerateString(length = 8):
    return ''.join([random.choice(string.ascii_lowercase + string.digits if i != 5 else string.ascii_uppercase) for i in range(length)])


def Logging(text, prefix, userid='DEBUG'):
    t1 = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    result = f'[{t1}] [{userid}] [{prefix}] - {text}'
    print(result)
    file_log = open(f'Logs.txt', 'a', encoding='utf-8')
    file_log.write(result + '\n')
    file_log.close()

def GetTypeFishing(userid):
    tf = config['type_fishing']
    return tf[userid % len(tf)]

def GetImage(userid=0):
    files = list(os.walk('images'))[0][2]
    img = Image.open("images/{}".format(files[int(userid) % len(files)]))
    blurred_image = img.filter(ImageFilter.GaussianBlur(config['blur']))
    img_byte_arr = io.BytesIO()
    blurred_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# VK
def GetInformation(userid):
    r = requests.get(f'https://api.vk.com/method/users.get?access_token={config["vk_api"]}&user_ids={userid}&v=5.131&fields=sex,bdate,photo_max,last_seen')
    return json.loads(r.text)

def GetSex(sex):
    SEX = {
        0: "Неизвестно",
        1: "Женский",
        2: "Мужской"
    }
    return SEX[sex]

def GetRegister(userid):
    try:
        r = requests.get(f'https://vk.com/foaf.php?id={userid}').text
        date = re.findall('<ya:created dc:date="(.*?)"/>', r)[0][:-6]
        date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
        return date
    except:
        return 'Неизвестно'

def GetBirthday(text):
    try:
        text = text['bdate']
        return BeautifulDate(text)
    except:
        return 'Не указано'

def BeautifulDate(text):
    try:
        text = text.split('.')
        mounth = ''
        if text[1] == '1':
            mounth = 'января'
        elif text[1] == '2':
            mounth = 'февраля'
        elif text[1] == '3':
            mounth = 'марта'
        elif text[1] == '4':
            mounth = 'апреля'
        elif text[1] == '5':
            mounth = 'мая'
        elif text[1] == '6':
            mounth = 'июня'
        elif text[1] == '7':
            mounth = 'июля'
        elif text[1] == '8':
            mounth = 'августа'
        elif text[1] == '9':
            mounth = 'сентября'
        elif text[1] == '10':
            mounth = 'октября'
        elif text[1] == '11':
            mounth = 'ноября'
        elif text[1] == '12':
            mounth = 'декабря'
        text[1] = mounth
        return ' '.join(text)
    except:
        return 'Неизвестно'


def GetDateSliv(reg):
    return BeautifulDate('{}.{}.{}'.format((reg + datetime.timedelta(days=13)).day, (reg + relativedelta(months=3)).month, reg.year + int((datetime.datetime.now().year - reg.year) // 1.2)))