from urllib import parse
import time, struct, random, socket, hashlib, threading

from uncompyle6.parsers.reducecheck import tryexcept

cz = 0
wx = [0, 0, 0, 0, 0]
mmh = 0
mmh_mm = 0


def login_interface(myfile='account.txt'):
    global mmh, mmh_mm
    account = get_account(myfile)
    mmh_list = []
    for key in sorted(account):
        mmh_list.append(key)
    account_len = len(account)
    while account_len != 0:
        md = int(input(['请选择模式：1.经典模式 2.一键砸罐子模式 3.一键分经验模式']))
        while md == 1:
            num = 0
            for x in mmh_list:
                print('%d、%s' % (num + 1, x))
                num += 1
            i = int(input(['请输入要登录的账号,0退出']))
            if i != 0 and i <= account_len:
                m = int(input(['请选择服务器：1.随机服务器 2.指定服务器']))
                mmh = int(mmh_list[i - 1])
                mmh_mm = account[mmh_list[i - 1]]
                if m == 1:
                    kaipai(mmh, mmh_mm, 1)
                elif m == 2:
                    fwq = int(input(['请输入服务器']))
                    kaipai(mmh, mmh_mm, 1, fwq)
                else:
                    exit(0)
            elif i > account_len:
                print('?')
            else:
                exit(0)
        if md == 2:
            print('正在一键砸罐子')
            for x in range(account_len):
                try:
                    threading.Thread(target=kaipai, args=(int(mmh_list[x - 1]), account[mmh_list[x - 1]], 2)).start()
                    # kaipai(int(mmh_list[x - 1]), account[mmh_list[x - 1]], 2)
                except Exception as e:
                    try:
                        print('%d砸罐子失败' % int(mmh_list[x - 1]))
                    finally:
                        e = None
                        del e
        if md == 3:
            print('正在一键分经验')
            for x in range(account_len):
                try:
                    # kaipai(int(mmh_list[x - 1]), account[mmh_list[x - 1]], 3)
                    threading.Thread(target=kaipai, args=(int(mmh_list[x - 1]), account[mmh_list[x - 1]], 3)).start()
                except Exception as e:
                    try:
                        print('%d分经验失败' % int(mmh_list[x - 1]))
                    finally:
                        e = None
                        del e
        else:
            exit(1)


def get_account(myfile):
    with open(myfile, 'r') as file:
        content = file.read()
    account = {}
    # md5 = hashlib.md5()
    for line in content.split('\n'):
        if line:
            uid, pwd = line.split(':')
            pwd1 = hashlib.md5(pwd.encode(encoding='UTF-8')).hexdigest()
            # md5.update(pwd.encode('utf-8'))
            # pwd1 = md5.hexdigest()
            account[uid] = pwd1
    return account

def login_taomi(uid, pwd, model, fwq):
    uid_hex = hex(uid)
    str1 = ''.join(uid_hex)
    str2 = list()
    if uid_hex.__len__() % 2 == 0:
        for x in range(2, uid_hex.__len__(), 2):
            str2.append(int(('0x' + str1[x:x + 2]), base=16))

    else:
        str2.append(int(('0x0' + str1[2]), base=16))
        for x in range(3, uid_hex.__len__(), 2):
            str2.append(int(('0x' + str1[x:x + 2]), base=16))

    if str2.__len__() <= 3:
        str2.insert(0, 0)
    if str2.__len__() <= 3:
        str2.insert(0, 0)
    pwd1 = hashlib.md5(pwd.encode()).hexdigest()
    pwd_hex = pwd1.encode().hex()
    pwd1 = list()
    for x in range(0, 64, 2):
        pwd1.append(int(('0x' + pwd_hex[x:x + 2]), base=16))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('49.234.206.24', 8989))
    req = struct.pack('148B', 0, 0, 0, 148, 0, 103, *str2, *(0, 0, 0, 1, 0, 0, 0, 0), *pwd1,
                      *(0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 110, 111, 110, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0))
    s.send(req)
    rec = s.recv(2048)
    if rec.__len__() != 42:
        print('登陆失败')
        return
    t = rec[22:38]
    packet = [0, 0, 0, 162, 0, 107, *str2, 0, 0, 0, 2, 0, 0, 0, 0]
    packet += t
    packet = packet + [110, 111, 110, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0]
    t1 = tuple(packet)
    req = struct.pack('162B', *t1)
    s.send(req)
    rec = s.recv(2048)
    packet2 = [0, 0, 0, 38, 0, 105, *str2, 0, 0, 0, 1, 0, 0, 0, 0]
    packet2 += t
    packet2 = packet2 + [0, 0, 0, 0]
    t1 = tuple(packet2)
    req = struct.pack('38B', *t1)
    r = s.send(req)
    rec = s.recv(2048)

    fwq = fwq if model == 1 and fwq != 0 else random.randint(11, 20)
    s2.connect(('49.234.206.24', 18080))
    packet = [0, 0, 0, 174, 3, 233, *str2, 0, 0, 0, 184, 0, 0, 0, 0, 0, 0, 0, fwq]
    packet += t
    packet = packet + [0, 0, 0, 7, 0, 0, 0, 7, 110, 111, 110, 101, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack('174B', *t1)
    s2.send(req)
    # packet = [0, 0, 0, 38, 3, 236, *str2, 0, 0, 6, 31, 0, 0, 0, 0, 0, 0, 43, 194, 0, 0, 0, 0, 0, 0, 2, 63, 0, 0, 0, 159, 0, 0, 0, 0]
    # t1 = tuple(packet)
    # req = (struct.pack)('38B', *t1)
    # s2.send(req)
    print('%d登录成功,当前服务器%d' % (uid, fwq))

    return s, s2, str2


def kaipai(uid, pwd, model, fwq=0):

    s, s2, str2 = login_taomi(uid, pwd, model, fwq)

    if model == 1:
        m = 1
        while m != 0:
            m = int(input(
                ['请输入要使用的功能：1砸罐子,2分经验,3开书/丸子包/箱子,4清理背包,5丢仓库宠物,6洗点,7开蛋,8兑换水晶,9兑换奖牌/礼物,0退出']))
            if m == 1:
                zgz(s2, str2)
            if m == 2:
                fjy(s2, str2, 0)
            if m == 3:
                type = int(input(['请输入要开启的物品：1经验书,2丸子包,3基姆箱子,4职业箱子,0其他']))
                if type == 1:
                    openbook(s2, str2)
                elif type == 2:
                    openjmbox(s2, str2, 360037)
                elif type == 3:
                    openjmbox(s2, str2, 300100)
                elif type == 4:
                    openzybox(s2, str2)
                else:
                    id = int(input(['请输入要开启的物品代码']))
                    openjmbox(s2, str2, id)
            if m == 4:
                clearbag(s2, str2)
                cleanequipment(s2, str2)
            if m == 5:
                fscw(s2, str2)
            if m == 6:
                xd(s2, str2, -1, -1)
            if m == 7:
                kd(s2, str2)
            if m == 8:
                excrystal(s2, str2)
            if m == 9:
                type = int(input(['请输入要兑换的物品：1巨石碎片->奖牌,2奖牌->宝物,3巨石->大丸子']))
                count = int(input(['请输入兑换数量']))
                exchangelb(s2, str2, type, count)
            if m == 123:
                position = int(input(['请输入地点：1海滩，2草木树海']))
                battle(s2, str2, position)
        s.close()
        s2.close()
        print('成功退出')
    if model == 2:
        zgz(s2, str2)
        print('%d成功砸罐子翻牌' % uid)
        clearbag(s2, str2)
        cleanequipment(s2, str2)
        time.sleep(3)
        s.close()
        s2.close()
    if model == 3:
        print("开始分经验")
        fjy(s2, str2, 1)
        time.sleep(3)
        s.close()
        s2.close()
        print('%d分经验完毕' % uid)


def zgz(s, str2):
    packet = [0, 0, 0, 38, 3, 236, *str2, 0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 198, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1,
              84, 0,
              0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 168]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2, 0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 197, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 52, 0, 0, 0, 0, 0, 0, 19, 166]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 115, 0, 0, 0, 0, 0, 0, 19, 167]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 194, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 162]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 195, 0, 0, 0, 0, 0, 0, 19, 161]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 61, 0, 0, 0, 0, 0, 0, 19, 163]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 138, 0, 0, 0, 0, 0, 0, 19, 164]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 195, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 165]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 193, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 159]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 160]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 202, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 171]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 38, 3, 236, *str2,
              0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 201, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
              0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 170]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 212, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 172]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 173]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 210, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 174]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 175]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 176]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 211, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 177]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 178]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 179]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 212, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 180]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 181]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 214, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 182]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 183]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 215, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 184]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 185]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 94, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 153]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 154]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 155]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 156]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 95, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 157]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    time.sleep(2)
    packet = [0, 0, 0, 38, 3, 236, *str2,
              0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 110, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
              0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 137]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 138]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 139]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 140]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 141]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 142]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 143]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 144]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 82, 111, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 145]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 146]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 147]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 148]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 149]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 150]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 151]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 152]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 84, 247, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 241]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 242]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 243]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 244]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 245]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 246]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 247]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 248]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 83, 253, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 226]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 227]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 228]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 83, 254, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 229]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 230]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 231]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 83, 255, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 232]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 233]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 234]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 83, 153, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 237]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 238]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 239]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 240]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 137, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 211]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 212]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 213]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 214]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 215]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    time.sleep(1)
    packet = [0, 0, 0, 38, 3, 236, *str2,
              0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 139, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
              0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 218]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 219]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    time.sleep(0.5)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 143, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 224]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 225]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 138, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 216]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 217]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 142, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 223]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 141, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 221]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 222]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 140, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 220]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 144, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 235]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 53, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 186]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 187]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 188]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 54, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 189]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    time.sleep(1)
    packet = [0, 0, 0, 38, 3, 236, *str2,
              0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 55, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
              0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 192]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 193]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 194]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 57, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 195]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 196]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 197]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 198]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 58, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 199]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 200]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 201]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 62, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 202]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 203]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 204]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 205]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 83, 63, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 206]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 207]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 208]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 209]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 210]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 6, 103, 0, 0, 0, 0, 0, 0, 44, 237, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 236]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 200, 0, 0, 0, 0, 0, 0, 0, 145, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 7, 99, 0, 0, 0, 0, 0, 0, 19, 169]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    packet = [
        0, 0, 0, 38, 3, 236, *str2,
        0, 0, 5, 165, 0, 0, 0, 0, 0, 0, 43, 96, 0, 0, 0, 0, 0, 0, 1, 216, 0, 0, 1, 84, 0,
        0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('38B',), *t1)
    s.send(req)
    packet = [0, 0, 0, 22, 6, 164, *str2, 0, 0, 6, 121, 0, 0, 0, 0, 0, 0, 19, 158]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    print('砸罐子完成')
    time.sleep(0.5)
    packet = [0, 0, 0, 18, 4, 18, *str2, 0, 0, 5, 207, 0, 0, 0, 0]
    t1 = tuple(packet)
    for x in range(15):
        req = struct.pack(*('18B',), *t1)
        s.send(req)
    print('开牌成功')
    time.sleep(0.5)
    packet = [0, 0, 0, 22, 6, 172, *str2, 0, 0, 5, 141, 0, 0, 0, 0, 0, 0, 0, 1]
    t1 = tuple(packet)
    for x in range(3):
        req = struct.pack(*('22B',), *t1)
        s.send(req)
    packet = [0, 0, 0, 22, 6, 172, *str2, 0, 0, 5, 141, 0, 0, 0, 0, 0, 0, 0, 2]
    t1 = tuple(packet)
    for x in range(3):
        req = struct.pack(*('22B',), *t1)
        s.send(req)
    print('幸运卡片翻牌成功')
    time.sleep(0.5)
    packet = [0, 0, 0, 22, 6, 84, *str2, 0, 0, 5, 176, 0, 0, 0, 0, 0, 0, 140, 160]
    t1 = tuple(packet)
    for x in range(10):
        req = struct.pack(*('22B',), *t1)
        s.send(req)
    print('炼金术之路抽奖次数增加成功')
    packet = [0, 0, 0, 18, 6, 87, *str2, 0, 0, 4, 190, 0, 0, 0, 0]
    t1 = tuple(packet)
    for x in range(60):
        req = struct.pack(*('18B',), *t1)
        s.send(req)
    print('炼金术之路抽奖成功')


def getpetlist(s, str2):

    packet = [0, 0, 0, *[0x12, 0x06, 0x12], *str2, 0, 0, 4, random.randint(0, 255), 0, 0, 0, 0]
    req = struct.pack(*('18B',), *packet)
    s.send(req)
    rec = s.recv(2048)
    r = tuple(rec)
    times = 0
    while r.__len__() < 22 or r[4] * 256 + r[5] != 1554:
        s.send(req)
        rec = s.recv(2048)
        r = tuple(rec)
        time.sleep(0.5)
        if times < 20:
            times += 1
        else:
            print('%s加载宠物列表失败' % str2)
            exit(0)

    i = r[21]
    x = 0
    a = [[] for b in range(i)]
    b = 22
    k = 0
    t = 999
    while b < r.__len__():
        if k == t:
            if x < i - 1:
                x += 1
                k = 0
                t = 999
            else:
                break
        a[x].append(int(r[b]))
        if k == 99:
            t = 106 + int(r[b]) * 9
        b += 1
        k += 1

    # pet_position_dict = {
    #     1 : "宠物背包",
    #     2 : "待命",
    #     3 : "主战",
    #     4 : "辅助"
    # }
    #
    #
    # for x in range(i):
    #     print(
    #         f'您的第{x + 1}个宠物是：{getname(a[x][13:31])},等级是{a[x][32]},宠物所在位置为[{pet_position_dict[a[x][67]]}],转生次数{a[x][-5]},'
    #         f'已分配经验{getexp(a[x][33:37])},转生所需经验{jsexp(a[x][-5], 0) - getexp(a[x][33:37])}')

    return a, i





def fjy(s, str2, num):

    a, i = getpetlist(s,str2)

    pet_position_dict = {
        1 : "宠物背包",
        2 : "待命",
        3 : "主战",
        4 : "辅助"
    }

    if num == 0:
        for x in range(i):
            print(
                f'共有{i}只宠物\n',
                f'您的第{x + 1}个宠物是：{getname(a[x][13:31])},等级是{a[x][32]},宠物所在位置为[{pet_position_dict[a[x][67]]}],转生次数{a[x][-5]},'
                f'已分配经验{getexp(a[x][33:37])},转生所需经验{jsexp(a[x][-5], 0) - getexp(a[x][33:37])}')

    packet = [0, 0, 0, 22, 7, 208, *str2, 0, 0, 5, 179, 0, 0, 0, 0, *str2]
    req = struct.pack(*('22B',), *packet)
    s.send(req)
    rec = s.recv(2048)
    r1 = tuple(rec)
    while r1[4] * 256 + r1[5] != 2000:
        s.send(req)
        rec = s.recv(2048)
        r1 = tuple(rec)

    exp = getexp(r1[(-8):-4])
    x = 0
    if num == 0:
        print('经验树剩余经验：%d' % exp)
        a2 = input('请输入要分配经验的宠物:(按0退出)')
        x = int(a2) - 1
        if x == -1:
            return
        print('您要分配经验的宠物是%s' % getname(a[x][13:31]))
    elif num == 1:
        b = 0
        while b < i and a[b][-5] == 10 and a[b][32] == 99:
            b += 1

        if b < i:
            x = b
        print('您要分配经验的宠物是%s' % getname(a[x][13:31]))
    exp -= yjzs(exp, jsexp(a[x][-5], 0) - getexp(a[x][33:37]), a[x], str2, s)
    i = a[x][-5] + 1
    while exp > 0 and i != 11:
        exp -= yjzs(exp, jsexp(i, 0), a[x], str2, s)
        i += 1

    if exp > 0:
        if num == 1:
            fjy(s, str2, 1)


def getname(name_str):
    list1 = [hex(i)[2:4] for i in name_str]
    list2 = '%'
    for i in range(0, len(list1)):
        if list1[i] == '0':
            list1 = list1[None:i]
            break

    list2 += '%'.join(list1)
    url_data = parse.unquote(list2)
    return url_data


def getexp(str):
    sum = 0
    for i in str:
        sum = sum * 256 + i

    return sum


def yjzs(syexp, exp, pet, uid, s):
    i = 0
    exp1 = 0
    if syexp < exp:
        exp = syexp
        i = 1
    print('目标分配经验为%d' % exp)
    exp1 = exp
    a = 0
    if exp <= 0:
        print('NT?')
    else:
        while exp > 999999:
            fpexp(999999, pet, uid, s)
            exp -= 999999
            a += 1
            if a % 10 == 0:
                time.sleep(0.25)

        fpexp(exp, pet, uid, s)
        print('分配经验完成')
    if i == 0:
        print('正在转生')
        zs(pet, uid, s)
    return exp1


def fpexp(exp, pet, uid, s):
    s1 = list()
    s1.append(int(exp / 65536))
    s1.append(int(exp / 256 % 256))
    s1.append(exp % 256)
    packet = [0, 0, 0, 26, 4, 12, *uid, 0, 0, 5, 63, 0, 0, 0, 0, *pet[0:4], 0, *s1]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)


def zs(pet, uid, s):
    packet = [0, 0, 0, 22, 15, 163, *uid, 0, 0, 5, 187, 0, 0, 0, 0, *pet[0:4]]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    print('转生成功')


def jsexp(tr, low):
    HighLevelList = [
        '1080367', '1088762', '1097386', '1106240', '1115329', '1124654',
        '1134220', '1144028', '1154083', '1164386',
        '1174942',
        '1185752', '1196821', '1208150', '1219744', '1231604', '1243735',
        '1256138', '1268818', '1281776',
        '1295017', '1308542',
        '1322356', '1336460', '1350859', '1365554', '1380550', '1395848',
        '1411453', '1427366',
        '1443592', '1460132', '1476991',
        '1494170', '1511674']
    Section = ['17850625', '21420750', '25704900', '30845879', '37015057', '44418067',
               '53301681', '63962019', '76754417', '92105299',
               '110526369']
    tr = int(tr)
    low = int(low)
    if tr != 10:
        high = int(50 + 5 * tr)
    else:
        high = 99
    exphigh = 0
    explow = 0
    if low >= high:
        print('等级下限不能超过等级上限！')
    else:
        if low < 65 and high < 65:
            explow = int(low ** 4 * 1.2 ** tr + 0.5)
            exphigh = int(high ** 4 * 1.2 ** tr + 0.5)
            exp = exphigh - explow
        else:
            if low < 65 and high > 64:
                explow = int(low ** 4 * 1.2 ** tr + 0.5)
                while high - 65:
                    exphigh += int(int(HighLevelList[high - 66]) * 1.2 ** tr + 0.5)
                    high -= 1

                exp = exphigh - explow + int(Section[tr])
            else:
                while high - 65:
                    exphigh += int(int(HighLevelList[high - 66]) * 1.2 ** tr + 0.5)
                    high -= 1

                while low - 65:
                    explow += int(int(HighLevelList[low - 66]) * 1.2 ** tr + 0.5)
                    low -= 1

                exp = exphigh - explow
        return exp + 10

def fscw(s, str2):
    packet = [0, 0, 0, 26, 6, 23, *str2, 0, 0, 6, 165, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 142]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    rec = s.recv(50000)
    s.send(req)
    rec1 = s.recv(50000)
    r = tuple(rec1)
    times = 0
    while r.__len__() < 30 or r[5] != 23:
        s.send(req)
        rec = s.recv(50000)
        s.send(req)
        rec1 = s.recv(50000)
        r = tuple(rec1)
        time.sleep(0.5)
        if times < 20:
            times += 1
        else:
            print('%s获取宠物仓库列表失败' % str2)
            exit(0)

    # packet = [0, 0, 0, 18, 6, 18, *str2, 0, 0, 6, 83, 0, 0, 0, 0]
    # t1 = tuple(packet)
    # req = (struct.pack)(*('18B', ), *t1)
    # s.send(req)
    # rec = s.recv(30000)
    # r = tuple(rec)
    # print(r.__len__())

    i = getinfo(r[28:30], 2)
    print('共有%d只宠物' % i)
    x = 0
    a = [[] for b in range(i)]
    b = 30
    k = 0
    t = 33
    while b < r.__len__():
        if k == t:
            if x < i - 1:
                x += 1
                k = 0
                t = 33
            else:
                break
        a[x].append(int(r[b]))
        b = b + 1
        k = k + 1

    for x in range(i):
        print('您的第%d个宠物是：%s,等级是%d' % (x + 1, getname(a[x][9:28]), a[x][28]))

    name = input(['请输入要丢弃宠物的名字'])
    dj = int(input(['请输入要丢弃宠物的等级']))

    count = 0
    for x in range(i):
        if (a[x][28] == dj) and getname(a[x][9:28]) == name:
            packet = [0, 0, 0, 22, 6, 25, *str2, 0, 0, 8, 34, 0, 0, 0, 0, *a[x][0:4]]
            t1 = tuple(packet)
            req = struct.pack(*('22B',), *t1)
            s.send(req)
            count += 1
    print('放生成功，共放生%d只宠物' % count)


def clearbag(s, str2):
    print('正在清理背包')
    packet = [0, 0, 0, 18, 4, 85, *str2, 0, 0, 4, 233, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('18B',), *t1)
    s.send(req)
    rec = s.recv(10000)
    s.send(req)
    rec1 = s.recv(10000)
    r = tuple(rec1)
    while r.__len__() < 22 or r[5] != 85:
        s.send(req)
        rec = s.recv(10000)
        s.send(req)
        rec1 = s.recv(10000)
        r = tuple(rec1)
    i = 0
    while i < len(r) - 22:
        inid = getinfo(r[(22 + i):(26 + i)])
        if (inid >= 310000 and inid < 320000) or (inid >= 210000 and inid <= 210011) or inid in (370000, 370002, 370005,
                                                                                                 290011, 290012, 290013,
                                                                                                 300044, 300045, 300046,
                                                                                                 300080, 200002, 180041,
                                                                                                 180042, 230012,
                                                                                                 300002):
            packet = [0, 0, 0, 30, 4, 99, *str2, 0, 0, 5, 15, 0, 0, 0, 0, 0, 0, 0, 1, *r[(22 + i):(26 + i)], 0, 0,
                      r[32 + i], r[33 + i]]
            t1 = tuple(packet)
            req = struct.pack(*('30B',), *t1)
            s.send(req)
            print('代码%d物品已放入仓库' % inid)
            time.sleep(0.1)
        if (inid >= 200004 and inid < 210000) or inid in (180043, 180044):
            packet = [0, 0, 0, 30, 4, 88, *str2, 0, 0, 5, 115, 0, 0, 0, 0, 0, 0, 0, 1, *r[(22 + i):(26 + i)], 0, 0,
                      r[32 + i], r[33 + i]]
            t1 = tuple(packet)
            req = struct.pack(*('30B',), *t1)
            s.send(req)
            print('代码%d物品已出售' % inid)
            time.sleep(0.1)
        i += 12

    print('清理完毕')


def getinfo(str, scale=4):
    sum = 0
    for x in range(scale):
        sum += str[x] * 256 ** ((scale - 1) - x)

    return sum


def cleanequipment(s, str2):
    print('正在清理装备')
    packet = [0, 0, 0, 18, 4, 78, *str2, 0, 0, 4, 201, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('18B',), *t1)
    s.send(req)
    rec = s.recv(10000)
    s.send(req)
    rec1 = s.recv(10000)
    r = tuple(rec1)
    times = 0
    while r.__len__() < 22 or r[5] != 78 or r.__len__() < 22 + 96 * r[21]:
        s.send(req)
        rec = s.recv(10000)
        s.send(req)
        rec1 = s.recv(10000)
        r = tuple(rec1)
        time.sleep(0.5)
        if times < 20:
            times += 1
        else:
            print('%s获取装备列表失败' % str2)
            exit(0)

    num = r[21]
    # print('共有%d件装备' % num)
    x = 0
    a = [[] for b in range(num)]
    b = 22
    k = 0
    t = 96
    while b < r.__len__():
        if k == t:
            if x < num - 1:
                x += 1
                k = 0
                t = 96
            else:
                break
        a[x].append(int(r[b]))
        if k == 95:
            t = 96 + int(r[b]) * 4
        b += 1
        k += 1

    # for x in range(num):
    #         print('您的第%d件装备代码是：%d,编号是' % (x + 1, getinfo(a[x][4:8])), ''.join(hex(i)[2:].zfill(2).upper() for i in a[x][0:4]))

    for x in range(num):
        inid = getinfo(a[x][4:8])
        if (inid >= 80074 and inid <= 80077) or (inid >= 130005 and inid <= 130006) or (
                inid >= 130007 and inid <= 130011) or (inid >= 120001 and inid <= 120004) or (
                inid >= 130001 and inid <= 130004):
            if (inid >= 130007 and inid <= 130011) or (inid >= 120001 and inid <= 120004) or (
                    inid >= 130001 and inid <= 130004):
                packet = [0, 0, 0, 26, 4, 87, *str2, 0, 0, 5, 4, 0, 0, 0, 0, 0, 0, 0, 1, *a[x][0:4]]
                t1 = tuple(packet)
                req = struct.pack(*('26B',), *t1)
                s.send(req)
                print('代码%d装备已出售' % inid)
                time.sleep(0.1)
            else:
                packet = [0, 0, 0, 22, 4, 80, *str2, 0, 0, 6, 81, 0, 0, 0, 0, *a[x][0:4]]
                t1 = tuple(packet)
                req = struct.pack(*('22B',), *t1)
                s.send(req)
                print('代码%d装备已丢弃' % inid)
                time.sleep(0.1)


def openzybox(s, str2):
    zhiye = input(['请输入要开箱的职业拼音首字母，如 剑士:js'])
    if zhiye == 'sy':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 75]
        weapon_id = 142040
        shoes_id = [142036, 142037, 142038, 142039]
    elif zhiye == 'cj':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 71]
        weapon_id = 140170
        shoes_id = [140164, 140166, 140167, 140168]
    elif zhiye == 'js':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 69]
        weapon_id = 140161
        shoes_id = [140157, 140158, 140159, 140160, 140162]
    elif zhiye == 'gj':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 70]
        weapon_id = 140169
        shoes_id = [140163, 140165, 140167, 140168]
    elif zhiye == 'rz':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 72]
        weapon_id = 140303
        shoes_id = [140301, 140302, 140167, 140168]
    elif zhiye == 'kz':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 73]
        weapon_id = 141040
        shoes_id = [141036, 141037, 141038, 141039]
    elif zhiye == 'hm':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 74]
        weapon_id = 141540
        shoes_id = [141536, 141537, 141538, 141539]
    elif zhiye == 'ws':
        packet_xz = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 212, 0, 0, 0, 0, 0, 4, 148, 76]
        weapon_id = 142540
        shoes_id = [142536, 142537, 142538, 142539]
    else:
        return
    expect = input(['请输入期望的数值(攻击 魔攻 精神/恢复 速度 防御),不追求的输入0'])
    expect = expect.split(' ')
    expect = [int(x) for x in expect]
    con = ''
    while con == '':
        for i in range(8):
            t1 = tuple(packet_xz)
            req = struct.pack(*('22B',), *t1)
            s.send(req)

        packet = [0, 0, 0, 18, 4, 78, *str2, 0, 0, 4, 201, 0, 0, 0, 0]
        t1 = tuple(packet)
        req = struct.pack(*('18B',), *t1)
        s.send(req)
        rec = s.recv(10000)
        s.send(req)
        rec1 = s.recv(10000)
        r = tuple(rec1)
        times = 0
        while r.__len__() < 22 or r[5] != 78 or r.__len__() < 22 + 96 * r[21]:
            s.send(req)
            rec = s.recv(10000)
            s.send(req)
            rec1 = s.recv(10000)
            r = tuple(rec1)
            time.sleep(0.5)
            if times < 20:
                times += 1
            else:
                print('%s获取装备列表失败' % str2)
                exit(0)

        num = r[21]
        # print('共有%d件装备' % num)
        x = 0
        a = [[] for b in range(num)]
        b = 22
        k = 0
        t = 96
        while b < r.__len__():
            if k == t:
                if x < num - 1:
                    x += 1
                    k = 0
                    t = 96
                else:
                    break
            a[x].append(int(r[b]))
            if k == 95:
                t = 96 + int(r[b]) * 4
            b += 1
            k += 1

        weapon = 0
        shoes = 0
        expect_weapon = 0
        expect_shoes = 0
        if zhiye == 'sy':
            for x in range(num):
                inid = getinfo(a[x][4:8])
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d，魔攻为%d，恢复力为%d' % (weapon, getinfo(a[x][34:36], 2),
                                                                          getinfo(a[x][36:38], 2),
                                                                          getinfo(a[x][46:48], 2)))
                    if getinfo(a[x][34:36], 2) >= expect[0] and getinfo(a[x][36:38], 2) >= expect[1] and getinfo(
                            a[x][46:48], 2) >= expect[2]:
                        expect_weapon += 1
        elif zhiye in ['cj', 'hm']:
            for x in range(num):
                inid = getinfo(a[x][4:8])
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d，魔攻为%d，精神为%d' % (weapon, getinfo(a[x][34:36], 2),
                                                                        getinfo(a[x][36:38], 2),
                                                                        getinfo(a[x][44:46], 2)))
                    if getinfo(a[x][34:36], 2) >= expect[0] and getinfo(a[x][36:38], 2) >= expect[1] and getinfo(
                            a[x][44:46], 2) >= expect[2]:
                        expect_weapon += 1
        elif zhiye in ['js', 'gj', 'kz', 'rz', 'ws']:
            for x in range(num):
                inid = getinfo(a[x][4:8])
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d' % (weapon, getinfo(a[x][34:36], 2)))
                    if getinfo(a[x][34:36], 2) >= expect[0]:
                        expect_weapon += 1
        else:
            exit(0)
        print('共有%d件武器符合要求' % expect_weapon)

        if not zhiye in ['js', 'kz']:
            for x in range(num):
                inid = getinfo(a[x][4:8])
                if inid == shoes_id[-1]:
                    shoes += 1
                    print('您的第%d双鞋子速度为%d,防御为%d' % (shoes, getinfo(a[x][42:44], 2), getinfo(a[x][38:40], 2)))
                    if getinfo(a[x][42:44], 2) >= expect[3] and getinfo(a[x][38:40], 2) >= expect[4]:
                        expect_shoes += 1
        print('共有%d双鞋子符合要求' % expect_shoes)

        if expect_weapon != 0 or expect_shoes != 0:
            m = int(input(['是否清理背包? 1.清理 0.退出']))
            if m == 1:
                for x in range(num):
                    inid = getinfo(a[x][4:8])
                    if (inid in shoes_id) or (inid == weapon_id):
                        packet = [0, 0, 0, 26, 4, 87, *str2, 0, 0, 5, 4, 0, 0, 0, 0, 0, 0, 0, 1, *a[x][0:4]]
                        t1 = tuple(packet)
                        req = struct.pack(*('26B',), *t1)
                        s.send(req)
                        # print('代码%d装备已出售' % inid)
                        time.sleep(0.1)
                print('清理完毕')
            elif m == 0:
                exit(0)
            con = input(['是否继续? 回车继续 0.退出'])
        else:
            for x in range(num):
                inid = getinfo(a[x][4:8])
                if (inid in shoes_id) or (inid == weapon_id):
                    packet = [0, 0, 0, 26, 4, 87, *str2, 0, 0, 5, 4, 0, 0, 0, 0, 0, 0, 0, 1, *a[x][0:4]]
                    t1 = tuple(packet)
                    req = struct.pack(*('26B',), *t1)
                    s.send(req)
                    # print('代码%d装备已出售' % inid)
                    time.sleep(0.1)
            print('清理完毕')


def excrystal(s, str2):
    md = int(input(['请输入水晶兑换的物品:1基姆箱子,2五项丸子']))
    if md == 1:
        packet = [0, 0, 0, 26, 4, 104, *str2, 0, 0, 5, 92, 0, 0, 0, 0, 0, 0, 39, 70, 0, 0]
    elif md == 2:
        packet = [0, 0, 0, 26, 4, 104, *str2, 0, 0, 5, 198, 0, 0, 0, 0, 0, 0, 39, 72, 0, 0]
    else:
        return
    num = int(input(['请输入兑换的数量']))
    num = hex(num)[2:].zfill(4)
    packet = packet + [int(num[0:2], base=16), int(num[2:4], base=16)]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    print('兑换成功')


def openjmbox(s, str2, id=300100):
    id = hex(id)[2:].zfill(6)
    packet = [0, 0, 0, 22, 4, 103, *str2, 0, 0, 5, 251, 0, 0, 0, 0, 0, int(id[0:2], base=16), int(id[2:4], base=16),
              int(id[4:6], base=16)]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    num = int(input('请输入开启数量'))
    for i in range(num):
        s.send(req)
        if i % 50 == 0:
            time.sleep(0.5)


def openbook(s, str2):
    packet = [0, 0, 0, 26, 4, 105, *str2, 0, 0, 5, 149, 0, 0, 0, 0, 0, 5, 87, 98, 0, 0, 0, 1]
    t1 = tuple(packet)
    req = struct.pack('26B', *t1)
    num = int(input('请输入开启数量'))
    for i in range(num):
        s.send(req)
        if i % 50 == 0:
            time.sleep(0.5)


def xd(s, str2, xz, num):
    global cz
    global wx
    packet = [0, 0, 0, 18, 6, 18, *str2, 0, 0, 4, 227, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('18B',), *t1)
    s.send(req)
    rec = s.recv(2048)
    s.send(req)
    rec1 = s.recv(2048)
    r = tuple(rec1)
    times = 0
    while r.__len__() < 22 or r[4] * 256 + r[5] != 1554:
        s.send(req)
        rec = s.recv(2048)
        s.send(req)
        rec1 = s.recv(2048)
        r = tuple(rec1)
        time.sleep(0.5)
        if times < 20:
            times += 1
        else:
            print('%s加载宠物列表失败' % str2)
            exit(0)

    i = r[21]

    x = 0
    a = [[] for b in range(i)]
    b = 22
    k = 0
    t = 999
    while b < r.__len__():
        if k == t:
            if x < i - 1:
                x += 1
                k = 0
                t = 999
            else:
                break
        a[x].append(int(r[b]))
        if k == 99:
            t = 106 + int(r[b]) * 9
        b += 1
        k += 1

    if xz == -1:
        print('共有%d只宠物' % i)
        for x in range(i):
            print('您的第%d个宠物是：%s,等级是%d,转生次数%d,已分配经验%d,转生所需经验%d' % (x + 1, getname(a[x][13:31]),
                                                                                           a[x][32], a[x][-5],
                                                                                           getexp(a[x][33:37]),
                                                                                           jsexp(a[x][-5], 0) - getexp(
                                                                                               a[x][33:37])))

        xz = int(input('[请选择要洗点的精灵]')) - 1

    print('成长%s\n体力%s\t生命值%s\n力量%s\t攻击力%s\n耐力%s\t防御%s\n敏捷%s\t速度%s\n智力%s\t魔力%s' % (
        a[xz][-29], getinfo(a[xz][37:39], 2), getinfo(a[xz][70:72], 2), getinfo(a[xz][39:41], 2),
        getinfo(a[xz][76:78], 2), getinfo(a[xz][41:43], 2), getinfo(a[xz][78:80], 2), getinfo(a[xz][43:45], 2),
        getinfo(a[xz][80:82], 2), getinfo(a[xz][45:47], 2), getinfo(a[xz][74:76], 2)))

    if num == -1:
        num = int(input('选择丸子1绿色成长2红色成长3大成长4紫色五项5红色五项(按0退出)')) - 1

    if num == 0 or num == 1:
        if cz == 0:
            cz = int(input(['请输入目标成长']))
            eatwz(s, str2, a[xz], num, xz)
        else:
            if a[xz][-29] < cz:
                eatwz(s, str2, a[xz], num, xz)
            else:
                print('洗成长成功')
                cz = 0
                return 0
    if num == 3 or num == 4:
        dqwx = [getinfo(a[xz][70:72], 2), getinfo(a[xz][76:78], 2), getinfo(a[xz][78:80], 2), getinfo(a[xz][80:82], 2),
                getinfo(a[xz][74:76], 2)]
        if wx == [0, 0, 0, 0, 0]:
            b = input(['请输入五项'])
            wx = [int(n) for n in b.split(' ')]
            eatwz(s, str2, a[xz], num, xz)
        else:
            b = 0
            for i in range(0, 4):
                if wx[i] > dqwx[i] and wx[i] != 0:
                    print('不满足')
                    b = 1
                    break

            if wx[4] < dqwx[4] and wx[4] != 0:
                if b != 1:
                    print('不满足')
                    b = 1

            if b == 1:
                eatwz(s, str2, a[xz], num, xz)
            else:
                print('洗点成功')
                return 0


def eatwz(s, str2, pet, num, xz):
    wanzi = [350013, 360008, 360038, 350014, 360009]
    packet = [0, 0, 0, 26, 6, 34, *str2, 0, 0, 5, 172, 0, 0, 0, 0, *pet[0:4], 0, int(wanzi[num] / 65536),
              int(wanzi[num] % 65536 / 256), int(wanzi[num] % 256)]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    time.sleep(0.2)
    xd(s, str2, xz, num)


def kd(s, str2):
    petid = int(input(['请输入开蛋的编号']))
    packet = [0, 0, 0, 22, 7, 208, *str2, 0, 0, 5, 179, 0, 0, 0, 0, *str2]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    rec = s.recv(2048)
    r1 = tuple(rec)
    while r1[4] * 256 + r1[5] != 2000:
        s.send(req)
        rec = s.recv(2048)
        r1 = tuple(rec)
    exp = getexp(r1[(-8):(-4)])
    print('开蛋编号:%d,经验树剩余经验:%d' % (petid, exp))
    expectwx = input(['请输入期望的数值(成长 生命 攻击 防御 速度 魔力),不追求的输入0，防御和魔力反向'])
    expectwx = expectwx.split(' ')
    expectwx = [int(x) for x in expectwx]

    s1 = list()
    s1.append(int(petid / 65536))
    s1.append(int(petid / 256 % 256))
    s1.append(petid % 256)
    con = ''
    petcount = 0
    while con == '':
        packet = [0, 0, 0, 30, 4, 99, *str2, 0, 0, 6, 31, 0, 0, 0, 0, 0, 0, 0, 0, 0, *s1, 0, 0, 0, 6]
        t1 = tuple(packet)
        req = struct.pack(*('30B',), *t1)
        s.send(req)
        packet = [0, 0, 0, 22, 4, 106, *str2, 0, 0, 5, 77, 0, 0, 0, 0, 0, *s1]
        for i in range(6):
            t1 = tuple(packet)
            req = struct.pack(*('22B',), *t1)
            s.send(req)
        petcount += 6

        packet = [0, 0, 0, 18, 6, 18, *str2, 0, 0, 4, 227, 0, 0, 0, 0]
        t1 = tuple(packet)
        req = struct.pack(*('18B',), *t1)
        s.send(req)
        rec = s.recv(2048)
        s.send(req)
        rec1 = s.recv(2048)
        r = tuple(rec1)
        times = 0
        while r.__len__() < 22 or rec1[4] * 256 + rec1[5] != 1554:
            s.send(req)
            rec = s.recv(2048)
            s.send(req)
            rec1 = s.recv(2048)
            r = tuple(rec1)
            time.sleep(0.5)
            if times < 20:
                times += 1
            else:
                print('%s加载宠物列表失败' % str2)
                exit(0)
        i = r[21]
        print('共有%d只宠物' % i)
        x = 0
        a = [[] for b in range(i)]
        b = 22
        k = 0
        t = 999
        while b < r.__len__():
            if k == t:
                if x < i - 1:
                    x += 1
                    k = 0
                    t = 999
                else:
                    break
            a[x].append(int(r[b]))
            if k == 99:
                t = 106 + int(r[b]) * 9
            b += 1
            k += 1

        num = 0
        for x in range(i):
            print('您的第%d个宠物是：%s,等级是%d,转生次数%d,成长值%s' % (x + 1, getname(a[x][13:31]), a[x][32], a[x][-5],
                                                                        a[x][-29]))
            if (a[x][-29] >= expectwx[0] or expectwx[0] == 0) and getinfo(a[x][70:72], 2) >= expectwx[1] and getinfo(
                    a[x][76:78], 2) >= expectwx[2] and (
                    expectwx[3] == 0 or getinfo(a[x][78:80], 2) <= expectwx[3]) and getinfo(a[x][80:82], 2) >= expectwx[
                4] and (expectwx[5] == 0 or getinfo(a[x][74:76], 2) <= expectwx[5]):
                print('体力%s\t生命值%s\n力量%s\t攻击力%s\n耐力%s\t防御%s\n敏捷%s\t速度%s\n智力%s\t魔力%s' % (
                    getinfo(a[x][37:39], 2), getinfo(a[x][70:72], 2), getinfo(a[x][39:41], 2), getinfo(a[x][76:78], 2),
                    getinfo(a[x][41:43], 2), getinfo(a[x][78:80], 2), getinfo(a[x][43:45], 2), getinfo(a[x][80:82], 2),
                    getinfo(a[x][45:47], 2), getinfo(a[x][74:76], 2)))
                print('\n\n')
                num += 1

        print('共有%d只符合要求的宠物,成长:%d,五项:(%d,%d,%d,%d,%d)' % (num, expectwx[0], expectwx[1], expectwx[2],
                                                                        expectwx[3], expectwx[4], expectwx[5]))

        packet = [0, 0, 0, 22, 7, 208, *str2, 0, 0, 5, 179, 0, 0, 0, 0, *str2]
        t1 = tuple(packet)
        req = struct.pack(*('22B',), *t1)
        s.send(req)
        rec = s.recv(2048)
        r1 = tuple(rec)
        while r1[4] * 256 + r1[5] != 2000:
            s.send(req)
            rec = s.recv(2048)
            r1 = tuple(rec)

        exp = getexp(r1[(-8):(-4)])

        if num > 0:
            print('累计开了%d个蛋,经验树剩余经验%d' % (petcount, exp))
            clean = int(input(['是否进行清理，按1清理，按0退出']))
        elif num == 0:
            clean = 1
        else:
            clean = 0
        if clean == 1:
            for b in range(i):
                if a[b][32] > 1:
                    print('当前背包中有等级大于1的精灵，是否继续碰蛋')
                    if int(input(['按1继续，按0退出：'])) == 0:
                        return

            if exp < 3750:
                print('经验不足，是否继续。当前经验：%d' % exp)
                if int(input(['按1继续，按0退出：'])) == 0:
                    return
            for b in range(i):
                fpexp(625, a[b], str2, s)
                fanghui(a[b], str2, s)
                if b % 2 == 1:
                    print('进行碰蛋')
                    pengdan(a[b], a[b - 1], str2, s)
            clearbag(s, str2)
            if num > 0:
                con = input(['是否继续开%d,回车继续,按0退出' % petid])
        else:
            con = 0


def fanghui(pet, str2, s):
    packet = [0, 0, 0, 26, 6, 15, *str2, 0, 0, 5, 93, 0, 0, 0, 0, *pet[0:4], 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)


def pengdan(pet1, pet2, str2, s):
    packet = [0, 0, 0, 26, 6, 23, *str2, 0, 0, 5, 141, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    rec = s.recv(250)
    r = tuple(rec)
    while r.__len__() != 63:
        s.send(req)
        rec = s.recv(250)
        r = tuple(rec)

    len1 = r[20] * 256 + r[21]
    packet = [0, 0, 0, 26, 6, 23, *str2, 0, 0, 5, 141, 0, 0, 0, 0, 0, 0, int((len1 - 2) / 256), (len1 - 2) % 256, 0, 0,
              0, 2]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    rec = s.recv(250)
    packet = [0, 0, 0, 30, 6, 79, *str2, 0, 0, 6, 235, 0, 0, 0, 0, *pet1[0:4], *pet2[0:4], 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('30B',), *t1)
    s.send(req)


def battle(s, str2, position):
    global mmh, mmh_mm
    battle_times = 0
    battle_load_wait = 0.1

    a, i = getpetlist(s, str2)
    pet_flag = False
    for x in range(i):
        if a[x][67] == 3 :
            pet_id = a[x][0:4]
            pet_flag = True
            print(f"找到主战宠物{getname(a[x][13:31])}")
        else:
            pass
    if not pet_flag:
        pet_id = [0, 0, 0, 0]
        print("没有主战宠物！")

    time.sleep(0.1)

    while True:
        try:
            if position == 1:
                skill_time = 8
                # 传送海滩
                packet = [0, 0, 0, *[0x26, 0x03, 0xec], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0,
                          *[0x56, 0x55], 0, 0, 0, 0, 0, 0, *[0x0, 0x5a], 0, 0, *[0x01, 0x8e], 0, 0, 0, 0]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.1)

                # 刷明雷
                packet = [0, 0, 0, 30, 5, 20, *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 9, 0,
                          0, 0, 0, 0, 0, 0, 0]
                req = struct.pack(*('30B',), *packet)
                s.send(req)
                time.sleep(0.1)

            elif position == 2:
                skill_time = 3
                # 草木树海
                packet = [0, 0, 0, *[0x26, 0x03, 0xec], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0,
                          *[0x2c, 0xef], 0, 0, 0, 0, 0, 0, *[0x05, 0x66], 0, 0, *[0x03, 0xee], 0, 0, 0, 0]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.1)

                # 刷食人花
                packet = [0, 0, 0, *[0x1a, 0x05, 0x18], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0,
                          0x1e, 0, 0, 0, 0]
                req = struct.pack(*('26B',), *packet)
                s.send(req)

            elif position == 3:
                skill_time = 3
                # 吉普豆3号地道
                packet = [0, 0, 0, *[0x26, 0x03, 0xec], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0,
                          *[0x54, 0xf7], 0, 0, 0, 0, 0, 0, *[0x0, 0xac], 0, 0, *[0x0, 0xcf], 0, 0, 0, 0]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.1)

                # 刷暗雷
                packet = [0, 0, 0, *[0x1e, 0x05, 0x14], *str2, 0, 0, 6, random.randint(0, 255), *([0] * 16)]
                req = struct.pack(*('30B',), *packet)
                s.send(req)
                time.sleep(0.1)


            for battle_load_percent in range(5, 101, 5):
                # 进入战斗读秒（0-100）
                packet = [0, 0, 0, 22, 5, 26, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, 0,
                          0,
                          0, battle_load_percent]
                req = struct.pack(*('22B',), *packet)
                s.send(req)
                time.sleep(battle_load_wait)

            # 不知道干啥用的，大概是进入战斗
            packet = [0, 0, 0, 22, 5, 37, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1]
            req = struct.pack(*('22B',), *packet)
            s.send(req)
            time.sleep(0.1)

            # packet = [0, 0, 0, 18, 6, 28, *str2, 0, 0, 5, 221, 0, 0, 0, 0, 0, 0, 0, 0]
            # t1 = tuple(packet)
            # req = (struct.pack)(*('22B', ), *t1)
            # s.send(req)
            # time.sleep(0.2)

            # 自动释放技能
            for i in range(0, skill_time):
                # 人物自动攻击
                packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                          0,
                          255, 255, 255, 255, 0, 15, 66, 64, 0, 0, 0, 1]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.05)

                # 宠物自动攻击
                packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, *pet_id, 0, 0,
                          0, 0, 255, 255, 255, 255, 0, 15, 66, 64, 0, 0, 0, 1]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.05)

                # #原版有'h12064a头的包，不知道干什么用的
                # packet = [0, 0, 0, 18, 6, 74, *str2, 0, 0, 5, random.randint(0,255), 0, 0, 0, 0]
                # t1 = tuple(packet)
                # req = (struct.pack)(*('18B', ), *t1)
                # s.send(req)
                # time.sleep(0.2)

            # 大概是结束战斗（1a0406）
            packet = [0, 0, 0, 26, 4, 6, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
            t1 = tuple(packet)
            req = struct.pack(*('26B',), *t1)
            s.send(req)
            time.sleep(0.1)

            # 星豆治疗
            packet = [0, 0, 0, 22, 4, 1, *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 5]
            req = struct.pack(*('22B',), *packet)
            s.send(req)

            battle_times = battle_times + 1
            print(time.strftime('%H:%M:%S ') + f"完成第{battle_times}次战斗")

            time.sleep(0.1)
        except (ConnectionAbortedError, ConnectionResetError):
            _, s, str2 = login_taomi(mmh, mmh_mm, model=1, fwq=0)

def exchangelb(s, str2, type, count):
    if type == 1:
        packet = [0, 0, 0, 0x1a, 0x04, 0x68, *str2, 0, 0, 0x05, 0x1a, 0, 0, 0, 0, 0, 0, 0x4e, 0x72, 0, 0, 0, 0x01]
    elif type == 2:
        packet = [0, 0, 0, 0x1a, 0x04, 0x68, *str2, 0, 0, 0x06, 0x59, 0, 0, 0, 0, 0, 0, 0x27, 0x79, 0, 0, 0, 0x01]
    elif type == 3:
        packet = [0, 0, 0, 0x1a, 0x04, 0x68, *str2, 0, 0, 0x04, 0x8b, 0, 0, 0, 0, 0, 0, 0x4e, 0x74, 0, 0, 0, 0x01]
    else:
        print('兑换类型错误')
        return
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    for i in range(count):
        s.send(req)
    print('兑换成功')


if __name__ == '__main__':
    login_interface('account.txt')
