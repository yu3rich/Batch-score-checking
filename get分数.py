import base64
import re
import requests
import time

import choose
import ocr
import store

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
}


def tg(headers, id, psaaword):
    url = 'http://tgjs.jxedu.gov.cn/website/login.html'  # 登录发包页面post方式
    img = 'http://tgjs.jxedu.gov.cn/website/auth.jpg'  # 验证码界面
    excle = 'http://tgjs.jxedu.gov.cn/website/we/personal/MyScore.html'  # 成绩界面
    bm = 'http://tgjs.jxedu.gov.cn/website/application.html'  # 报名界面

    response = requests.get(url=img, headers=headers)  # 使用headers避免访问受限，获取验证码
    cookies = response.cookies

    with open('code.png', 'wb') as f:  # "wb'表示对二进制文件的写入
        f.write(response.content)  # r.content表示返回内容的二进制形式
        f.close()  # with··· as 语句会自动关闭句柄，可不写close()
    time.sleep(1)
    code = ocr.Ocr_d('code.png')
    rand = sum(code.rec_sum())
    print(f'验证码：{rand}')

    data = {
        'loginName': id,
        'passWord': psaaword,
        'randCode': f'{rand}',
        # 'randCode':'123',
    }
    requests.post(url=url, headers=headers, data=data, cookies=cookies, stream=True)  # 登录系统

    data_fs = requests.get(excle, headers=headers, cookies=cookies)  # 获取分数界面信息
    data_bm = requests.get(bm, headers=headers, cookies=cookies)  # 获取报名界面信息
    data_1 = re.sub(r'\n*\s*\t*\r', '', data_fs.text)
    data_2 = re.sub(r'\n*\s*\t*\r', '', data_bm.text)
    fs_1 = re.findall(r"(?<=\<td\>\n\t{7}).*?(?=\n[\t+])", data_1)
    bm_1 = re.findall(r"(?<=\<td\>\n\t{4}).*?(?=\n[\t+])", data_2)
    data_bm.cookies.clear()
    data_bm.headers.clear()
    if not fs_1:
        return id, '密码或账号错误'
    else:
        zkz = fs_1[1]
        gwdm = bm_1[0]
        jzfs = fs_1[2]
        xkfs = fs_1[3]
        return id, gwdm, zkz, jzfs, xkfs  # 获取成功


def gb(headers, id, password):
    # 国编密码先行校验
    jy = re.search(r'^[a-zA-Z]\w{5,11}$', password)
    if jy:
        print('密码校验成功')
    else:
        print('错误，请输入6-12位数字、字母!')
        return id, '密码格式错误'

    def bm(nu):
        # 国编登录密码两次加密，第二次开头加上大写的C
        message_bytes = nu.encode('ascii')  # 入格式
        base64_bytes_1 = base64.b64encode(message_bytes)  # 编码
        base64_message_1 = base64_bytes_1.decode('ascii')
        return base64_message_1

    # 登录接口
    dl = 'https://pta.jxhrss.gov.cn/api/login'
    # 分数界面
    data_fs = 'https://pta.jxhrss.gov.cn/api/Score/getKsScoreDataList?prjId=21b7aea5369b443089d6783718aef95d'
    # 个人信息界面
    data_xx = 'https://pta.jxhrss.gov.cn/api/Score/getKsInfo?prjId=21b7aea5369b443089d6783718aef95d'
    # 验证码界面
    cod = 'https://pta.jxhrss.gov.cn/api/securityCodeBase64'

    response = requests.get(url=cod, headers=headers, verify=False)  # 使用headers避免访问受限
    cookies = response.cookies
    yyy = response.text

    verificationKey = re.search(r'(?<={").*?(?=":")', yyy).group(0)  # 验证码的key
    codimg_64 = re.search(r'(?<=base64,).*?(?="})', yyy).group(0)  # 图片的编码

    imgdata = base64.b64decode(codimg_64)
    # 将图片保存为文件
    with open("temp.jpg", 'wb') as f:
        f.write(imgdata)
    time.sleep(1)
    code = ocr.Ocr_d('temp.jpg')
    rand = code.rec()

    print(f'验证码：{rand}')

    # 获取登录后的令牌
    data = {
        "username": id,
        "password": bm('C' + bm(password)),
        "verificationCode": rand,
        "verificationKey": verificationKey
    }
    tokdata = requests.post(dl, headers=headers, cookies=cookies, json=data, verify=False)
    if tokdata.status_code == 500:
        print('验证码错误，尝试重新登录')
        tokdata.cookies.clear()
        tokdata.headers.clear()
        gb(headers, id, password)
    elif tokdata.status_code == 401:
        print('密码错误')
        return id, '登录密码错误'
    headers_1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'x-auth-token': tokdata.headers['X-Auth-Token'],
    }
    man_data = requests.get(data_xx, headers=headers_1, cookies=cookies, verify=False).text
    cj_data = requests.get(data_fs, headers=headers_1, cookies=cookies, verify=False).text
    gwid = re.search(r'(?<=bkzw":").*?(?=")', man_data).group(0)
    name = re.search(r'(?<=examinee_name":").*?(?=")', man_data).group(0)
    zkz = re.search(r'(?<=admissionNo":").*?(?=")', cj_data).group(0)
    cj = re.findall(r'(?<=subject_score":).*?(?=")', cj_data)
    return id, gwid, zkz, cj[0], cj[1]


name = choose.Lookup(r'账号信息.xlsx')
id = name.data_ss(2, 1)
password = name.data_ss(2, 2)
lx = name.data_ss(2, 3)

store = store.Dataxls('gat分数.xlsx')

xlshard = ['账号', '岗位代码', '准考证', '教综分数', '学科分数']

for o, p, t in zip(id, password, lx):
    if t == '国编':
        gb_1 = gb(headers, o, p)
        store.xls_1(gb_1, xlshard)
        print(gb_1, '\n')
    if t == '特岗':
        tg_1 = tg(headers, o, p)
        store.xls_1(tg_1, xlshard)
        print(tg_1, '\n')
