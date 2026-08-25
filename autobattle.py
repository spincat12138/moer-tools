from urllib import parse
import time, struct, random, socket, hashlib, logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_account(myfile='account.txt'):
    account = {}
    try:
        with open(myfile, 'r') as file:
            for line in file:
                if ':' in line:
                    uid, pwd = line.strip().split(':')
                    account[uid] = hashlib.md5(pwd.encode()).hexdigest()
    except Exception as e:
        logging.error(f"读取账号文件失败: {e}")
    return account

def login_taomi(uid, pwd):
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
    try:
        s.connect(('49.234.206.24', 8989))
        # 登录握手包
        req = struct.pack('148B', 0, 0, 0, 148, 0, 103, *str2, *(0, 0, 0, 1, 0, 0, 0, 0), *pwd1,
                      *(0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 110, 111, 110, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0))
        s.send(req)
        rec = s.recv(2048)
        if len(rec) < 42: raise Exception("登录验证失败")
        
        t = rec[22:38] # 提取 Token
        
        # 二次确认包
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
        
        # 建立游戏连接
        s2.connect(('49.234.206.24', 18080))
        fwq = random.randint(11, 20)
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
        
        logging.info(f"账号 {uid} 登录成功，服务器: {fwq}")
        return s, s2, str2
    except Exception as e:
        logging.error(f"连接过程异常: {e}")
        return None, None, None
        
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

def battle_loop(s2, str2):
    """海滩刷怪逻辑"""
    battle_times = 0
    battle_load_wait = 0.1
    skill_time = 8

    a, i = getpetlist(s2, str2)
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

    # time.sleep(0.1)
    while True:
        # # 1. 传送至海滩 (固定包头)
        # packet = [0, 0, 0, 38, 3, 236, *str2, 0, 0, 5, 200, 0, 0, 0, 0, 0, 0, 0x56, 0x55, 0, 0, 0, 0, 0, 0, 0, 0x5a, 0, 0, 0x01, 0x8e, 0, 0, 0, 0]
        # s2.send(struct.pack('38B', *packet))
        # time.sleep(0.1)
        
        # # 2. 刷明雷战斗
        # packet = [0, 0, 0, 30, 5, 20, *str2, 0, 0, 5, 100, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0]
        # s2.send(struct.pack('30B', *packet))
        # time.sleep(0.1)
        
        # 1. 传送至新生巨石蟹 (固定包头)
        packet = [0, 0, 0, 0x26, 3, 0xec, *str2, 0, 0, 5, 0xc8, 0, 0, 0, 0, 0, 0, 0x75, 0xfb, 0, 0, 0, 0, 0, 0, 0, 0x8b, 0, 0, 0x01, 0x5d, 0, 0, 0, 0]
        s2.send(struct.pack('38B', *packet))
        time.sleep(0.1)
        
        # 2. 刷明雷战斗
        packet = [0, 0, 0, 0x1a, 0x05, 0x18, *str2, 0, 0, 5, 0xbb, 0, 0, 0, 0, 0, 0, 0x09, 0xc8, 0, 0, 0, 0]
        s2.send(struct.pack('26B', *packet))
        time.sleep(0.1)
        
        # 3. 进入战斗
        for battle_load_percent in range(5, 101, 5):
            # 进入战斗读秒（0-100）
            packet = [0, 0, 0, 22, 5, 26, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, 0,
                      0,
                      0, battle_load_percent]
            req = struct.pack(*('22B',), *packet)
            s2.send(req)
            time.sleep(battle_load_wait)

        # 不知道干啥用的，大概是进入战斗
        packet = [0, 0, 0, 22, 5, 37, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1]
        req = struct.pack(*('22B',), *packet)
        s2.send(req)
        time.sleep(0.1)
        
        # 自动释放技能
        for i in range(0, skill_time):
            # 人物自动攻击
            packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0,
                      255, 255, 255, 255, 0, 15, 66, 64, 0, 0, 0, 1]
            req = struct.pack(*('38B',), *packet)
            s2.send(req)
            time.sleep(0.05)

            # 宠物自动攻击
            packet = [0, 0, 0, 38, 5, 28, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, *pet_id, 0, 0,
                      0, 0, 255, 255, 255, 255, 0, 15, 66, 64, 0, 0, 0, 1]
            req = struct.pack(*('38B',), *packet)
            s2.send(req)
            time.sleep(0.05)

        # 大概是结束战斗（1a0406）
        packet = [0, 0, 0, 26, 4, 6, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1]
        t1 = tuple(packet)
        req = struct.pack(*('26B',), *t1)
        s2.send(req)
        time.sleep(0.1)

        # 星豆治疗
        packet = [0, 0, 0, 22, 4, 1, *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 5]
        req = struct.pack(*('22B',), *packet)
        s2.send(req)

        battle_times = battle_times + 1
        if (battle_times % 10 == 0):
            clearbag(s2, str2)
        logging.info(f"成功完成第 {battle_times} 次战斗")
        time.sleep(0.5)
       
def run_bot():
    accounts = get_account()
    if not accounts: 
        logging.error("没有可用账号，请检查 account.txt")
        return
    
    uid_str = list(accounts.keys())[0]
    pwd_md5 = accounts[uid_str]
    
    # 修复：确保传入 login_taomi 的是整数 UID
    s, s2, str2 = login_taomi(int(uid_str), pwd_md5)
    
    if s:
        try:
            # 修复：需要将 s 也传递进战斗循环，因为 battle_loop 中用到了 s
            battle_loop(s2, str2)
        finally:
            s.close()
            s2.close()

if __name__ == '__main__':
    while True:
        try:
            logging.info("服务启动中...")
            run_bot()
        except Exception as e:
            logging.warning(f"发生致命错误，5秒后重启: {e}")
            time.sleep(5)