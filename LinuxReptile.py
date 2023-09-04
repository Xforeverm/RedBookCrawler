import json
import pymysql
import requests
import traceback
from utils import *

today = str(datetime.date.today())


def getRedBookData():
    login_url = 'https://customer.xiaohongshu.com/api/cas/loginWithAccount'  # login url
    session_url = 'https://ad.xiaohongshu.com/api/leona/session'  # session url
    final_url = 'https://ad.xiaohongshu.com/api/leona/rtb/campaign/list'  # request url
    login_data = json.dumps(
        {"account": f"{redbook_username}", "password": f"{redbook_password}", "service": f"{redbook_url}"})
    session_data = {"ticket": "", "clientId": "https://ad.xiaohongshu.com"}
    final_data = {"startTime": today, "endTime": today, "pageNum": 1, "pageSize": 10}
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        'Cookie': ''
    }
    # request login get cookies
    res = requests.post(login_url, data=login_data,
                        headers=headers)
    for v in res.cookies:
        headers['Cookie'] += v.name + '=' + v.value + '; '

    # session_data must have ticket from login request
    session_data['ticket'] = res.json()['data']
    res = requests.post(session_url, data=json.dumps(session_data),
                        headers=headers)

    # set Cookie:ares.beaker.session.id
    headers['Cookie'] += 'ares.beaker.session.id=' + res.cookies.get('ares.beaker.session.id')
    headers['Referer'] = 'https://ad.xiaohongshu.com/aurora/ad/manage/campaign'
    res = requests.post(final_url, headers=headers,
                        data=json.dumps(final_data))

    result = res.json()['data']['aggregationData']
    result['account'] = f"reBook={redbook_username}"
    res.close()
    return result


def getScrmData():
    info_url = 'https://account.wxb.com/user/info?'
    pre_url = 'https://account.wxb.com/index2/preLogin'
    login_url = 'https://account.wxb.com/index2/login'
    final_url = "https://api-scrm.wxb.com/stat/qwOverview?corp_id=30083&start_date=" + today + "&end_date=" + today
    pre_data = {
        'email': scrm_username,
        'from': 'https%3A%2F%2Fscrm.wxb.com%2F',
        'password': scrm_password
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://scrm.wxb.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        # 'Referer': 'https://account.wxb.com/page/login?logo=//s.yezgea02.com/common/mskeW5.png&from=https%3A%2F%2Fscrm.wxb.com%2F',
        'Cookie': ''
    }
    resu = requests.get(info_url, headers=headers)
    headers['Cookie'] += 'PHPSESSID=' + resu.cookies.get('PHPSESSID') + '; '
    resu.close()

    resu = requests.post(pre_url, data=pre_data, headers=headers)
    resu.close()

    resu = requests.post(login_url, data=pre_data, headers=headers)
    resu.close()

    resu = requests.get(
        final_url,
        headers=headers)
    resu.close()

    return 'scrm=' + pre_data.get('email'), resu.json()['data']['add_customer']


if __name__ == '__main__':
    conn = pymysql.connect(host='101.42.7.42', user='crawler', password='XA2zM2iXMiaWBhp2', port=3306, db='crawler',
                           charset='utf8')
    try:
        scrm, add_customer = getScrmData()
        result = getRedBookData()
        scrm += ', ' + result['account']

        # database connect
        cursor = conn.cursor()
        sql = f"INSERT into qc_crawler (fee, impression, ctr, messageUser, initiativeMessage, messageConsultCpl, initiativeMessageCpl, add_customer , account, time) values ({result['fee']}, {result['impression']}, '{result['ctr']}', {result['messageUser']}, {result['initiativeMessage']}, {result['messageConsultCpl']}, {result['initiativeMessageCpl']}, {add_customer}, '{scrm}','{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')"
        print(sql)
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print(traceback.format_exc())
        conn.rollback()
        send_email(traceback.format_exc())
    finally:
        if conn:
            conn.close()
        if cursor:
            cursor.close()
