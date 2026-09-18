from urllib import parse
import time, struct, random, socket, hashlib, threading, weakref
from collections import deque

from uncompyle6.parsers.reducecheck import tryexcept

cz = 0
wx = [0, 0, 0, 0, 0]
xd_count = 0
xd_max_count = 0
mmh = 0
mmh_mm = 0

# 与客户端 ProfessionType 中的职业编号保持一致。
_PROFESSION_NAMES = {
    0: '无',
    1: '剑士',
    2: '弓箭手',
    3: '魔法师',
    4: '传教士',
    5: '忍者',
    6: '狂战士',
    7: '黑魔导士',
    8: '圣言使',
    9: '巫术士',
}


class SocketSession:
    """为一条 TCP 连接维护持久化的拆包缓冲区和待处理响应。"""

    _MIN_PACKET_LENGTH = 18
    _MAX_PACKET_LENGTH = 10 * 1024 * 1024

    def __init__(self, sock):
        self.sock = sock
        self._recv_buffer = bytearray()
        self._pending_by_command = {}
        self._recv_lock = threading.Lock()

    def recv_packet(self, expected_command=None, timeout=None):
        """读取一个完整网络帧；不匹配 expected_command 的帧会暂存。"""
        with self._recv_lock:
            pending = self._pending_by_command.get(expected_command)
            if expected_command is not None and pending:
                packet = pending.popleft()
                if not pending:
                    del self._pending_by_command[expected_command]
                return packet

            original_timeout = self.sock.gettimeout()
            if timeout is not None:
                self.sock.settimeout(timeout)
            try:
                while True:
                    packet = self._pop_complete_packet()
                    if packet is None:
                        received_data = self.sock.recv(10000)
                        if not received_data:
                            raise ConnectionError('socket连接已关闭')
                        self._recv_buffer.extend(received_data)
                        continue

                    command_id = int.from_bytes(packet[4:6], byteorder='big')
                    if expected_command is None or command_id == expected_command:
                        return packet
                    self._pending_by_command.setdefault(command_id, deque()).append(packet)
            finally:
                if timeout is not None:
                    self.sock.settimeout(original_timeout)

    def _pop_complete_packet(self):
        if len(self._recv_buffer) < 4:
            return None

        packet_length = int.from_bytes(self._recv_buffer[:4], byteorder='big')
        if not self._MIN_PACKET_LENGTH <= packet_length <= self._MAX_PACKET_LENGTH:
            raise ValueError('响应包长度无效（%d）' % packet_length)
        if len(self._recv_buffer) < packet_length:
            return None

        packet = bytes(self._recv_buffer[:packet_length])
        del self._recv_buffer[:packet_length]
        if len(packet) < 6:
            raise ValueError('响应包头不完整')
        return packet


_SOCKET_SESSIONS = weakref.WeakKeyDictionary()
_SOCKET_SESSIONS_LOCK = threading.Lock()


def _get_socket_session(sock):
    """返回与 socket 绑定的会话，确保接收缓冲区不会随函数调用丢失。"""
    with _SOCKET_SESSIONS_LOCK:
        session = _SOCKET_SESSIONS.get(sock)
        if session is None:
            session = SocketSession(sock)
            _SOCKET_SESSIONS[sock] = session
        return session


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
                    return
            elif i > account_len:
                print('?')
            else:
                return
        if md == 2:
            print('正在一键砸罐子')
            threads = []
            for x in range(account_len):
                try:
                    thread = threading.Thread(
                        target=kaipai,
                        args=(int(mmh_list[x]), account[mmh_list[x]], 2),
                    )
                    thread.start()
                    threads.append(thread)
                except Exception as e:
                    try:
                        print('%d砸罐子失败：%s' % (int(mmh_list[x]), e))
                    finally:
                        e = None
                        del e
            for thread in threads:
                thread.join()
            return
        elif md == 3:
            print('正在一键分经验')
            threads = []
            for x in range(account_len):
                try:
                    thread = threading.Thread(
                        target=kaipai,
                        args=(int(mmh_list[x]), account[mmh_list[x]], 3),
                    )
                    thread.start()
                    threads.append(thread)
                except Exception as e:
                    try:
                        print('%d分经验失败：%s' % (int(mmh_list[x]), e))
                    finally:
                        e = None
                        del e
            for thread in threads:
                thread.join()
            return
        else:
            return


def get_account(myfile='account.txt'):
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

def login_taomi(uid, pwd, model=1, fwq=0):
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
    # # CREATE_ROLE 107 可忽略
    # packet = [0, 0, 0, 162, 0, 107, *str2, 0, 0, 0, 2, 0, 0, 0, 0]
    # packet += t
    # packet = packet + [110, 111, 110, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    #                    0, 0]
    # t1 = tuple(packet)
    # req = struct.pack('162B', *t1)
    # s.send(req)
    # rec = s.recv(2048)
    packet2 = [0, 0, 0, 38, 0, 105, *str2, 0, 0, 0, 1, 0, 0, 0, 0]
    packet2 += t
    packet2 = packet2 + [0, 0, 0, 0]
    t1 = tuple(packet2)
    req = struct.pack('38B', *t1)
    r = s.send(req)
    rec = s.recv(2048)

    fwq = fwq if model == 1 and fwq != 0 else random.randint(11, 20)
    if fwq in range(11, 21):
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
    elif fwq in range(1, 11):
        s2.connect(('49.234.206.24', 28080))
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
    else:
        print('服务器选择错误')
        return

    user_info = _get_more_userinfo(s2, str2)
    profession = _PROFESSION_NAMES.get(user_info['profession'], str(user_info['profession']))
    # packet = [0, 0, 0, 38, 3, 236, *str2, 0, 0, 6, 31, 0, 0, 0, 0, 0, 0, 43, 194, 0, 0, 0, 0, 0, 0, 2, 63, 0, 0, 0, 159, 0, 0, 0, 0]
    # t1 = tuple(packet)
    # req = (struct.pack)('38B', *t1)
    # s2.send(req)
    print('%d登录成功,当前服务器%d' % (uid, fwq))
    print('昵称：%s，职业：%s，等级：%s' % (
        user_info['nick'], profession, user_info['level']))

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
                xd_menu(s2, str2)
            if m == 7:
                kd(s2, str2)
            if m == 8:
                excrystal(s2, str2)
            if m == 9:
                type = int(input(['请输入要兑换的物品：1巨石碎片->奖牌,2巨石碎片->宝物,3巨石碎片->大丸子']))
                count = int(input(['请输入兑换数量']))
                exchangelb(s2, str2, type, count)
            if m == 123:
                position = int(input(['请输入地点：1海滩，2草木树海，3吉普豆3号地道，4新生巨石蟹']))
                battle(s2, str2, position, login_socket=s,  reconnect_fwq=fwq)
            if m == 666:
                tp_test(s2, str2)
        s.close()
        s2.close()
        print('成功退出')
    if model == 2:
        zgz(s2, str2)
        print('%d成功砸罐子翻牌' % uid)
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

    time.sleep(1)
    clearbag(s, str2)
    time.sleep(1)
    cleanequipment(s, str2)


def _get_pet_bag(s, str2):
    """请求并解析 1554（PET_GETLIST）宠物背包信息。"""
    pet_position_dict = {
        1: '宠物背包',
        2: '待命',
        3: '主战',
        4: '辅助',
    }
    packet = [0, 0, 0, 18, 6, 18, *str2, 0, 0, 4, random.randint(0, 255), 0, 0, 0, 0]
    s.send(struct.pack('18B', *packet))
    response = _receive_bag_response(s, str2, 1554, '宠物列表')
    offset = 18

    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        if offset + size > len(response):
            raise ValueError('%s获取宠物列表失败：宠物记录被截断' % str2)
        value = struct.unpack_from(fmt, response, offset)[0]
        offset += size
        return value

    def read_bytes(size):
        nonlocal offset
        if offset + size > len(response):
            raise ValueError('%s获取宠物列表失败：宠物记录被截断' % str2)
        value = response[offset:offset + size]
        offset += size
        return value

    pet_count = read('>I')
    pets = []
    for _ in range(pet_count):
        pet_id = read('>I')
        type_id = read('>I')
        pet = {
            'pet_id': pet_id,
            'pet_id_bytes': tuple(pet_id.to_bytes(4, byteorder='big')),
            'type_id': type_id,
            'race': read('>B'),
            'flag': read('>I'),
            'nick': read_bytes(16).split(b'\x00', 1)[0].decode('utf-8', errors='replace'),
            'level': read('>I'),
            'experience': read('>I'),
            'physique': read('>H'),
            'strength': read('>H'),
            'endurance': read('>H'),
            'quick': read('>H'),
            'intelligence': read('>H'),
            'attr_point_remaid': read('>H'),
            'attr_point_applied': read('>H'),
            'hp': read('>I'),
            'mp': read('>I'),
            'earth': read('>B'),
            'water': read('>B'),
            'fire': read('>B'),
            'wind': read('>B'),
            'injury_level': read('>I'),
            'status': pet_position_dict.get(read('>B'), '未知'),
            'hp_max': read('>I'),
            'mp_max': read('>I'),
            'attack': read('>H'),
            'defense': read('>H'),
            'speed': read('>H'),
            'spirit': read('>H'),
            'resume': read('>H'),
            'hit_rate': read('>H'),
            'avoid_rate': read('>H'),
            'critical': read('>H'),
            'fight_back': read('>H'),
            'grow_value': read('>H'),
        }

        skill_count = read('>I')
        if skill_count > (len(response) - offset - 5) // 9:
            raise ValueError('%s获取宠物列表失败：技能数量与包长不匹配' % str2)
        skills = []
        for _ in range(skill_count):
            skills.append({
                'skill_id': read('>I'),
                'level': max(1, read('>B')),
                'experience': read('>I'),
            })
        pet['skill_count'] = skill_count
        pet['skills'] = skills
        pet['is_reincarnation_enable'] = bool(read('>?'))
        pet['reincarnation_degree'] = read('>B')
        pet['additional_growth'] = read('>I')
        pets.append(pet)

    if offset != len(response):
        raise ValueError('%s获取宠物列表失败：包尾存在未解析数据' % str2)
    return {'pet_count': pet_count, 'pets': pets}


def fjy(s, str2, num):

    pet_data = _get_pet_bag(s, str2)
    a = pet_data['pets']
    i = pet_data['pet_count']

    if num == 0:
        for x in range(i):
            pet = a[x]
            print(
                f'共有{i}只宠物\n',
                f"您的第{x + 1}个宠物是：{pet['nick']},等级是{pet['level']},宠物所在位置为[{pet['status']}],转生次数{pet['reincarnation_degree']},"
                f"已分配经验{pet['experience']},转生所需经验{jsexp(pet['reincarnation_degree'], 0) - pet['experience']}")

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
        print('您要分配经验的宠物是%s' % a[x]['nick'])
    elif num == 1:
        b = 0
        while b < i and a[b]['reincarnation_degree'] == 10 and a[b]['level'] == 99:
            b += 1

        if b < i:
            x = b
        print('您要分配经验的宠物是%s' % a[x]['nick'])
    pet = a[x]
    exp -= yjzs(exp, jsexp(pet['reincarnation_degree'], 0) - pet['experience'], pet['pet_id_bytes'], str2, s)
    i = pet['reincarnation_degree'] + 1
    while exp > 0 and i != 11:
        exp -= yjzs(exp, jsexp(i, 0), pet['pet_id_bytes'], str2, s)
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
    pet_id = pet['pet_id_bytes'] if isinstance(pet, dict) else pet[0:4]
    packet = [0, 0, 0, 26, 4, 12, *uid, 0, 0, 5, 63, 0, 0, 0, 0, *pet_id, 0, *s1]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)


def zs(pet, uid, s):
    pet_id = pet['pet_id_bytes'] if isinstance(pet, dict) else pet[0:4]
    packet = [0, 0, 0, 22, 15, 163, *uid, 0, 0, 5, 187, 0, 0, 0, 0, *pet_id]
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
            return

    # packet = [0, 0, 0, 18, 6, 18, *str2, 0, 0, 6, 83, 0, 0, 0, 0]
    # t1 = tuple(packet)
    # req = (struct.pack)(*('18B', ), *t1)
    # s.send(req)
    # rec = s.recv(30000)
    # r = tuple(rec)
    # print(r.__len__())

    i = _byte_to_int(r[28:30], 2)
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


def _prop_backto_store(s, str2, item_id, quantity):
    """将指定数量的道具放入仓库。"""
    item_id_bytes = item_id.to_bytes(4, byteorder='big')
    quantity_bytes = quantity.to_bytes(4, byteorder='big')
    packet = [0, 0, 0, 30, 4, 99, *str2, 0, 0, 5, 15, 0, 0, 0, 0, 0, 0, 0, 1, *item_id_bytes,
              *quantity_bytes]
    t1 = tuple(packet)
    req = struct.pack(*('30B',), *t1)
    s.send(req)
    time.sleep(0.1)


def _prop_sell(s, str2, item_id, quantity):
    """出售指定数量的道具。"""
    item_id_bytes = item_id.to_bytes(4, byteorder='big')
    quantity_bytes = quantity.to_bytes(4, byteorder='big')
    packet = [0, 0, 0, 30, 4, 88, *str2, 0, 0, 5, 115, 0, 0, 0, 0, 0, 0, 0, 1, *item_id_bytes,
              *quantity_bytes]
    t1 = tuple(packet)
    req = struct.pack(*('30B',), *t1)
    s.send(req)
    time.sleep(0.1)


def _equipment_sell(s, str2, item_id, instance_id):
    """出售指定实例的装备。"""
    packet = [0, 0, 0, 26, 4, 87, *str2, 0, 0, 5, 4, 0, 0, 0, 0, 0, 0, 0, 1, *instance_id]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    print('代码%d装备已出售' % item_id)
    time.sleep(0.1)


def _equipment_discard(s, str2, item_id, instance_id):
    """丢弃指定实例的装备。"""
    packet = [0, 0, 0, 22, 4, 80, *str2, 0, 0, 6, 81, 0, 0, 0, 0, *instance_id]
    t1 = tuple(packet)
    req = struct.pack(*('22B',), *t1)
    s.send(req)
    print('代码%d装备已丢弃' % item_id)
    time.sleep(0.1)


def clearbag(s, str2):
    print('正在清理背包')
    prop_info, _ = _get_prop_bag_info(s, str2)
    for prop in prop_info:
        inid = prop['item_id']
        if (inid >= 310000 and inid < 320000) or (inid >= 210000 and inid <= 210011) or inid in (370000, 370002, 370005,
                                                                                                 290011, 290012, 290013,
                                                                                                 300044, 300045, 300046,
                                                                                                 300080, 200002, 180041,
                                                                                                 180042, 230012,
                                                                                                 300002):
            _prop_backto_store(s, str2, inid, prop['quantity'])
            print('代码%d物品已放入仓库' % inid)
        if (inid >= 200004 and inid < 210000) or inid in (180043, 180044):
            _prop_sell(s, str2, inid, prop['quantity'])
            print('代码%d物品已出售' % inid)

    print('清理完毕')


def _byte_to_int(data, scale=4):
    return int.from_bytes(data[:scale], byteorder="big")


def _receive_bag_response(s, str2, command_id, description):
    """从 socket 中取出指定命令的一个完整网络帧。"""
    try:
        return _get_socket_session(s).recv_packet(expected_command=command_id)
    except ConnectionError as exc:
        raise ConnectionError('%s获取%s失败：连接已关闭' % (str2, description)) from exc
    except ValueError as exc:
        raise ValueError('%s获取%s失败：%s' % (str2, description, exc)) from exc


def _parse_equipment_record(data, offset, str2):
    """按 SingleItemInfo.setEquipInfo 解析一条装备记录。"""
    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        if offset + size > len(data):
            raise ValueError('%s解析装备信息失败：装备记录被截断' % str2)
        value = struct.unpack_from(fmt, data, offset)[0]
        offset += size
        return value

    unique_id = read('>I')
    good_id = read('>I')
    grid_id = read('>I')
    level = read('>H')
    color_id = read('>I')
    validday = read('>I')
    max_durability = read('>H')
    durability = read('>H')
    max_hp = read('>i')
    max_mp = read('>i')

    attack = read('>h')
    magic_attack = read('>h')
    defense = read('>h')
    magic_defense = read('>h')
    speed = read('>h')
    spirit = read('>h')
    recovery = read('>h')
    hit = read('>h')
    dodge = read('>h')
    critical = read('>h')
    counter = read('>h')
    resistances = [read('>h') for _ in range(6)]

    crystal_attr = read('>I')
    bless_type = read('>I')
    activated = read('>I')
    add_bless_value = read('>I')

    gem_count = read('>I')
    if gem_count > (len(data) - offset) // 4:
        raise ValueError('%s解析装备信息失败：宝石数量与包长不匹配' % str2)
    gem_ids = [read('>I') for _ in range(gem_count)]

    equip_kind_identified = read('>I')
    stone_count = read('>I')
    if stone_count > (len(data) - offset) // 4:
        raise ValueError('%s解析装备信息失败：镶嵌石数量与包长不匹配' % str2)
    stone_ids = [read('>I') for _ in range(stone_count)]

    return {
        'instance_id': tuple(unique_id.to_bytes(4, byteorder='big')),
        'item_id': good_id,
        'grid_id': grid_id,
        'level': level,
        'equip_color_id': color_id,
        'validday': validday,
        'durability': durability,
        'max_durability': max_durability,
        'max_hp': max_hp,
        'max_mp': max_mp,
        'attack': attack,
        'magic_attack': magic_attack,
        'defense': defense,
        'magic_defense': magic_defense,
        'speed': speed,
        'spirit': spirit,
        'recovery': recovery,
        'hit': hit,
        'dodge': dodge,
        'critical': critical,
        'counter': counter,
        'resist_poison': resistances[0],
        'resist_stone': resistances[1],
        'resist_sleep': resistances[2],
        'resist_inebriation': resistances[3],
        'resist_confusion': resistances[4],
        'resist_oblivion': resistances[5],
        'crystal_attr': crystal_attr,
        'bless_type': bless_type,
        'activated': activated,
        'add_bless_value': add_bless_value,
        'gem_identification_status': equip_kind_identified,
        'equip_kind_identified': equip_kind_identified,
        'socket_count': gem_count,
        'gem_count': gem_count,
        'gem_ids': gem_ids,
        'equip_level_identify': stone_count,
        'stone_count': stone_count,
        'stone_ids': stone_ids,
    }, offset


def _get_equipment_bag_info(s, str2):
    """
    获取并解析背包内装备信息。
    :param s: socket连接
    :param str2: 米米号
    :return: 结构化装备信息列表和装备数量
    """
    packet = [0, 0, 0, 18, 4, 78, *str2, 0, 0, 4, 201, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('18B',), *t1)
    s.send(req)

    response = _receive_bag_response(s, str2, 1102, '装备列表')
    offset = 18

    if offset + 4 > len(response):
        raise ValueError('%s获取装备列表失败：缺少装备数量' % str2)
    equipment_count = struct.unpack_from('>I', response, offset)[0]
    offset += 4
    if equipment_count > (len(response) - offset) // 96:
        raise ValueError('%s获取装备列表失败：装备数量与包长不匹配' % str2)

    equipment_info = []
    for _ in range(equipment_count):
        item, offset = _parse_equipment_record(response, offset, str2)
        equipment_info.append(item)

    if offset != len(response):
        raise ValueError('%s获取装备列表失败：包尾存在未解析数据' % str2)
    return equipment_info, equipment_count


def _get_more_userinfo(s, str2):
    """请求并解析 1006（GET_MORE_USERINFO）的人物详细信息。"""
    packet = [0, 0, 0, 22, 3, 238, *str2, 0, 0, 5, 175, 0, 0, 0, 0, *str2]
    s.send(struct.pack('22B', *packet))

    response = _receive_bag_response(s, str2, 1006, '人物信息')
    offset = 18

    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        if offset + size > len(response):
            raise ValueError('%s获取人物信息失败：响应包被截断' % str2)
        value = struct.unpack_from(fmt, response, offset)[0]
        offset += size
        return value

    def read_bytes(size):
        nonlocal offset
        if offset + size > len(response):
            raise ValueError('%s获取人物信息失败：响应包被截断' % str2)
        value = response[offset:offset + size]
        offset += size
        return value

    user_id = read('>I')
    nick = read_bytes(16).split(b'\x00', 1)[0].decode('utf-8', errors='replace')
    fields = {
        'user_id': user_id,
        'nick': nick,
        'flag': read('>I'),
        'vip_level': read('>I'),
        'vip_energy': read('>I'),
        'vip_begin': read('>I'),
        'vip_end': read('>I'),
        'hero_cup_team_id': read('>I'),
        'color': read('>I'),
        'reg_time': read('>I'),
        'race': read('>B'),
        'profession': read('>B'),
        'profession_phase': read('>I'),
        'honor': read('>I'),
        'xiaomee': read('>I'),
        'pk_point': read('>I'),
        'energy': read('>I'),
        'level': read('>I'),
        'experience': read('>I'),
        'physique': read('>H'),
        'strength': read('>H'),
        'endurance': read('>H'),
        'quick': read('>H'),
        'intelligence': read('>H'),
        'attr_add': read('>H'),
        'hp': read('>I'),
        'mp': read('>I'),
        'earth': read('>B'),
        'water': read('>B'),
        'fire': read('>B'),
        'wind': read('>B'),
        'injured_level': read('>I'),
        'change_body_id': read('>I'),
        'map_id': read('>I'),
        'map_type': read('>I'),
        'pos_x': read('>I'),
        'pos_y': read('>I'),
        'base_action': read('>I'),
        'adv_action': read('>I'),
        'direction': read('>B'),
        'battle_in_front': read('>B'),
        'team_id': read('>I'),
        'team_member_index': read('>I'),
        'hp_max': read('>I'),
        'mp_max': read('>I'),
        'attack': read('>H'),
        'defense': read('>H'),
        'magic_defense': read('>H'),
        'speed': read('>H'),
        'spirit': read('>H'),
        'restore': read('>H'),
        'hit_rate': read('>H'),
        'avoid_rate': read('>H'),
        'critical': read('>H'),
        'attack_back': read('>H'),
        'anti_poison': read('>H'),
        'anti_stone': read('>H'),
        'anti_sleep': read('>H'),
        'anti_curse': read('>H'),
        'anti_confusion': read('>H'),
        'anti_forget': read('>H'),
    }

    # 客户端读取并丢弃 32 字节保留区，不能把它误当成装备数量。
    fields['reserved'] = read_bytes(32)
    suit_item_count = read('>B')
    if suit_item_count > (len(response) - offset) // 96:
        raise ValueError('%s获取人物信息失败：装备数量与包长不匹配' % str2)

    suit_items = []
    for _ in range(suit_item_count):
        item, offset = _parse_equipment_record(response, offset, str2)
        suit_items.append(item)

    if offset != len(response):
        raise ValueError('%s获取人物信息失败：包尾存在未解析数据' % str2)
    fields['suit_item_count'] = suit_item_count
    fields['suit_items'] = suit_items
    fields['detail_equip_item_list'] = suit_items
    return fields


def _get_prop_bag_info(s, str2):
    """
    获取并解析道具背包中的物品信息。
    :param s: socket连接
    :param str2: 米米号
    :return: 结构化物品信息列表和物品数量
    """
    packet = [0, 0, 0, 18, 4, 85, *str2, 0, 0, 4, 233, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('18B',), *t1)
    s.send(req)

    response = _receive_bag_response(s, str2, 1109, '道具列表')
    offset = 18
    if len(response) - offset < 4:
        raise ValueError('%s获取道具列表失败：缺少物品数量' % str2)
    prop_count = struct.unpack_from('>I', response, offset)[0]
    offset += 4
    if prop_count > (len(response) - offset) // 12:
        raise ValueError('%s获取道具列表失败：物品数量与包长不匹配' % str2)

    prop_info = []
    for _ in range(prop_count):
        good_id, grid_id, quantity = struct.unpack_from('>IIi', response, offset)
        offset += 12
        prop_info.append({
            'item_id': good_id,
            'grid_id': grid_id,
            # setGoodInfo 使用 readInt()，客户端对负数数量按 0 处理。
            'quantity': max(0, quantity),
        })

    if offset != len(response):
        raise ValueError('%s获取道具列表失败：包尾存在未解析数据' % str2)
    return prop_info, prop_count


def cleanequipment(s, str2):
    print('正在清理装备')
    equipment_info, num = _get_equipment_bag_info(s, str2)

    for x in range(num):
        item = equipment_info[x]
        inid = item['item_id']
        if (inid >= 80074 and inid <= 80077) or (inid >= 130005 and inid <= 130006) or (
                inid >= 130007 and inid <= 130011) or (inid >= 120001 and inid <= 120004) or (
                inid >= 130001 and inid <= 130004):
            if (inid >= 130007 and inid <= 130011) or (inid >= 120001 and inid <= 120004) or (
                    inid >= 130001 and inid <= 130004):
                _equipment_sell(s, str2, inid, item['instance_id'])
            else:
                _equipment_discard(s, str2, inid, item['instance_id'])
    print('装备清理完成')

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

        equipment_info, num = _get_equipment_bag_info(s, str2)

        weapon = 0
        shoes = 0
        expect_weapon = 0
        expect_shoes = 0
        if zhiye == 'sy':
            for item in equipment_info:
                inid = item['item_id']
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d，魔攻为%d，恢复力为%d' % (
                        weapon, item['attack'], item['magic_attack'], item['recovery']))
                    if item['attack'] >= expect[0] and item['magic_attack'] >= expect[1] and item['recovery'] >= expect[2]:
                        expect_weapon += 1
        elif zhiye in ['cj', 'hm']:
            for item in equipment_info:
                inid = item['item_id']
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d，魔攻为%d，精神为%d' % (
                        weapon, item['attack'], item['magic_attack'], item['spirit']))
                    if item['attack'] >= expect[0] and item['magic_attack'] >= expect[1] and item['spirit'] >= expect[2]:
                        expect_weapon += 1
        elif zhiye in ['js', 'gj', 'kz', 'rz', 'ws']:
            for item in equipment_info:
                inid = item['item_id']
                if inid == weapon_id:
                    weapon += 1
                    print('您的第%d把武器攻击为%d' % (weapon, item['attack']))
                    if item['attack'] >= expect[0]:
                        expect_weapon += 1
        else:
            return
        print('共有%d件武器符合要求' % expect_weapon)

        if not zhiye in ['js', 'kz']:
            for item in equipment_info:
                inid = item['item_id']
                if inid == shoes_id[-1]:
                    shoes += 1
                    print('您的第%d双鞋子速度为%d,防御为%d' % (
                        shoes, item['speed'], item['defense']))
                    if item['speed'] >= expect[3] and item['defense'] >= expect[4]:
                        expect_shoes += 1
        print('共有%d双鞋子符合要求' % expect_shoes)

        if expect_weapon != 0 or expect_shoes != 0:
            m = int(input(['是否清理背包? 1.清理 0.退出']))
            if m == 1:
                for item in equipment_info:
                    inid = item['item_id']
                    if (inid in shoes_id) or (inid == weapon_id):
                        _equipment_sell(s, str2, inid, item['instance_id'])
                print('清理完毕')
            elif m == 0:
                return
            con = input(['是否继续? 回车继续 0.退出'])
        else:
            for item in equipment_info:
                inid = item['item_id']
                if (inid in shoes_id) or (inid == weapon_id):
                    _equipment_sell(s, str2, inid, item['instance_id'])
            print('清理完毕')


def _exchange_item(s, str2, npc_id, item_index, quantity):
    '''
    兑换物品(水晶、巨石碎片等)
    :param s: socket连接
    :param str2: 玩家米米号
    :param npc_id: NPC ID
    :param item_index: 物品索引
    :param quantity: 数量
    '''
    quantity_byte = [quantity // 256, quantity % 256]
    packet = [0, 0, 0, 0x1a, 0x04, 0x68, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, 0, 0,
              npc_id, item_index, 0, 0, *quantity_byte]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)


def excrystal(s, str2):
    md = int(input(['请输入水晶兑换的物品:1基姆箱子,2五项丸子']))
    if md == 1:
        item_index = 0x46
    elif md == 2:
        item_index = 0x48
    else:
        return
    quantity = int(input(['请输入兑换的数量']))
    _exchange_item(s, str2, 0x27, item_index, quantity)
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


def _reset_xd_state():
    """清理一次洗点流程的临时状态，避免下一次洗点继承上次目标。"""
    global cz, wx, xd_count, xd_max_count
    cz = 0
    wx = [0, 0, 0, 0, 0]
    xd_count = 0
    xd_max_count = 0


def _should_retry_xd():
    """洗点结束后等待用户选择：回车重试，0 返回宠物列表。"""
    while True:
        choice = input('[按回车使用相同设置重试，按0返回]').strip()
        if choice == '':
            return True
        if choice == '0':
            return False
        print('请直接按回车重试，或输入0返回')


def xd_menu(s, str2):
    """洗点子菜单；每次结束后重新选择宠物，输入 0 返回主功能菜单。"""
    while not xd(s, str2, -1, -1):
        pass


def xd(s, str2, xz, num):
    global cz
    global wx
    global xd_count
    global xd_max_count

    # xz == -1 只出现在一次新的洗点流程开始时；递归刷新宠物数据时保留状态。
    if xz == -1:
        _reset_xd_state()

    while True:
        pet_data = _load_xd_pets(s, str2)
        a = pet_data['pets']

        if xz == -1:
            print('共有%d只宠物' % pet_data['pet_count'])
            for x in range(len(a)):
                listed_pet = a[x]
                print('您的第%d个宠物是：%s,等级是%d,转生次数%d,已分配经验%d,转生所需经验%d' % (
                    x + 1, listed_pet['nick'], listed_pet['level'], listed_pet['reincarnation_degree'],
                    listed_pet['experience'],
                    jsexp(listed_pet['reincarnation_degree'], 0) - listed_pet['experience']))

            pet_number = int(input('[请选择要洗点的精灵，按0退出]'))
            if pet_number == 0:
                _reset_xd_state()
                return True
            if pet_number < 1 or pet_number > len(a):
                print('宠物编号不存在')
                continue
            xz = pet_number - 1

        pet = a[xz]
        print('成长%s\n体力%s\t生命值%s\n力量%s\t攻击力%s\n耐力%s\t防御%s\n敏捷%s\t速度%s\n智力%s\t魔力%s' % (
            pet['grow_value'], pet['physique'], pet['hp_max'], pet['strength'], pet['attack'],
            pet['endurance'], pet['defense'], pet['quick'], pet['speed'], pet['intelligence'], pet['spirit']))

        if num == -1:
            num = int(input('选择丸子1绿色成长2红色成长3大丸子4紫色五项5红色五项(按0退出)')) - 1
            if num == -1:
                _reset_xd_state()
                return False

        if num == 0 or num == 1:
            if cz == 0:
                cz = int(input(['请输入目标成长']))
            if pet['grow_value'] >= cz:
                print('洗成长成功，一共洗点%d次' % xd_count)
                _reset_xd_state()
                return False
            eatwz(s, str2, pet, num)
            continue

        if num == 3 or num == 4 or num == 2:
            dqwx = [pet['physique'], pet['attack'], pet['defense'], pet['speed'], pet['spirit']]

            # 用次数是否已设置判断是否为首次进入，允许五项目标全部填写 0。
            if xd_max_count == 0:
                wx = [int(n) for n in input(['请输入五项:(体力/力量/耐力/速度/魔力) 体力/力量/速度为不低于设定数值，耐力/防御/魔力为不高于设定数值，0为不判断']).split(' ')]
                if len(wx) != 5:
                    print('请输入5个用空格分隔的数值')
                    _reset_xd_state()
                    return False
                xd_max_count = int(input('请输入洗点次数'))
                if xd_max_count <= 0:
                    print('洗点次数必须大于0')
                    _reset_xd_state()
                    return False
                eatwz(s, str2, pet, num)
                continue

            is_satisfied = True
            for i in [0, 1, 3]:
                if wx[i] > dqwx[i] and wx[i] != 0:
                    is_satisfied = False
                    break
            if wx[2] < dqwx[2] and wx[2] != 0:
                is_satisfied = False
            if wx[4] < dqwx[4] and wx[4] != 0:
                is_satisfied = False

            if is_satisfied:
                print('洗点成功，一共洗点%d次' % xd_count)
                if _should_retry_xd():
                    xd_count = 0
                    eatwz(s, str2, pet, num)
                    continue
                _reset_xd_state()
                return False
            if xd_count >= xd_max_count:
                print('已达到指定洗点次数，一共洗点%d次' % xd_count)
                if _should_retry_xd():
                    xd_count = 0
                    eatwz(s, str2, pet, num)
                    continue
                _reset_xd_state()
                return False

            print('不满足')
            eatwz(s, str2, pet, num)
            continue

        print('丸子编号不存在')
        _reset_xd_state()
        return False


def _load_xd_pets(s, str2):
    """加载洗点所需的宠物数据，复用统一的宠物背包请求和解析逻辑。

    返回 ``_get_pet_bag`` 的完整结果（包含 ``pet_count`` 和结构化的
    ``pets`` 列表），避免洗点流程再次按字节偏移解析宠物记录。
    """
    return _get_pet_bag(s, str2)


def eatwz(s, str2, pet, num):
    global xd_count
    wanzi = [350013, 360008, 360038, 350014, 360009]
    packet = [0, 0, 0, 26, 6, 34, *str2, 0, 0, 5, 172, 0, 0, 0, 0, *pet['pet_id_bytes'], 0, int(wanzi[num] / 65536),
              int(wanzi[num] % 65536 / 256), int(wanzi[num] % 256)]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)
    xd_count += 1
    time.sleep(0.2)


def _fetch_item_from_store(s, str2, item_id, quantity):
    '''
    从仓库中获取指定id的物品
    :param s: socket连接
    :param str2: 玩家米米号
    :param item_id: 物品ID
    :param quantity: 数量
    '''
    item_id = int(item_id)
    item_id_bytes = [item_id // 65536, item_id // 256 % 256, item_id % 256]
    quantity_bytes = [quantity // 256, quantity % 256]
    packet = [0, 0, 0, 30, 4, 99, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 0, 0, *item_id_bytes, 0, 0,
              *quantity_bytes]
    t1 = tuple(packet)
    req = struct.pack(*('30B',), *t1)
    s.send(req)


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
        _fetch_item_from_store(s, str2, petid, 6)
        packet = [0, 0, 0, 22, 4, 106, *str2, 0, 0, 5, 77, 0, 0, 0, 0, 0, *s1]
        for i in range(6):
            t1 = tuple(packet)
            req = struct.pack(*('22B',), *t1)
            s.send(req)
        petcount += 6

        pet_data = _get_pet_bag(s, str2)
        a = pet_data['pets']
        i = pet_data['pet_count']
        print('共有%d只宠物' % i)

        num = 0
        for x, pet in enumerate(a):
            print('您的第%d个宠物是：%s,等级是%d,转生次数%d,成长值%s' % (
                x + 1, pet['nick'], pet['level'], pet['reincarnation_degree'], pet['grow_value']))
            if (pet['grow_value'] >= expectwx[0] or expectwx[0] == 0) and pet['hp_max'] >= expectwx[1] and pet['attack'] >= expectwx[2] and (
                    expectwx[3] == 0 or pet['defense'] <= expectwx[3]) and pet['speed'] >= expectwx[4] and (
                    expectwx[5] == 0 or pet['spirit'] <= expectwx[5]):
                print('体力%s\t生命值%s\n力量%s\t攻击力%s\n耐力%s\t防御%s\n敏捷%s\t速度%s\n智力%s\t魔力%s' % (
                    pet['physique'], pet['hp_max'], pet['strength'], pet['attack'], pet['endurance'], pet['defense'],
                    pet['quick'], pet['speed'], pet['intelligence'], pet['spirit']))
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
            for pet in a:
                if pet['level'] > 1:
                    print('当前背包中有等级大于1的精灵，是否继续碰蛋')
                    if int(input(['按1继续，按0退出：'])) == 0:
                        return

            if exp < 3750:
                print('经验不足，是否继续。当前经验：%d' % exp)
                if int(input(['按1继续，按0退出：'])) == 0:
                    return
            for b, pet in enumerate(a):
                fpexp(625, pet, str2, s)
                _pet_back_home(s, str2, pet)
                if b % 2 == 1:
                    print('进行碰蛋')
                    pengdan(pet, a[b - 1], str2, s)
            clearbag(s, str2)
            if num > 0:
                con = input(['是否继续开%d,回车继续,按0退出' % petid])
        else:
            con = 0


def _pet_back_home(s, str2, pet):
    '''
    宠物放回仓库
    :param s: socket连接
    :param str2: 玩家米米号
    :param pet: 宠物信息
    '''
    pet_id = pet['pet_id_bytes'] if isinstance(pet, dict) else pet[0:4]
    packet = [0, 0, 0, 0x1a, 0x06, 0x0f, *str2, 0, 0, 5, 93, 0, 0, 0, 0, *pet_id, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('26B',), *t1)
    s.send(req)


def pengdan(pet1, pet2, str2, s):
    packet = [0, 0, 0, 0x1a, 0x06, 0x17, *str2, 0, 0, 5, 141, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
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
    pet1_id = pet1['pet_id_bytes'] if isinstance(pet1, dict) else pet1[0:4]
    pet2_id = pet2['pet_id_bytes'] if isinstance(pet2, dict) else pet2[0:4]
    packet = [0, 0, 0, 30, 6, 79, *str2, 0, 0, 6, 235, 0, 0, 0, 0, *pet1_id, *pet2_id, 0, 0, 0, 0]
    t1 = tuple(packet)
    req = struct.pack(*('30B',), *t1)
    s.send(req)


class _BattlePacketReader:
    """读取战斗协议的网络帧负载（TMF 头固定 18 字节，大端序）。"""

    def __init__(self, packet):
        if len(packet) < 18:
            raise ValueError('战斗响应包头不完整')
        self.packet = packet
        self.offset = 18

    def read(self, fmt):
        size = struct.calcsize(fmt)
        if self.offset + size > len(self.packet):
            raise ValueError('战斗响应包数据被截断（偏移%d）' % self.offset)
        value = struct.unpack_from(fmt, self.packet, self.offset)[0]
        self.offset += size
        return value

    def bytes(self, size):
        if size < 0 or self.offset + size > len(self.packet):
            raise ValueError('战斗响应包数据被截断（偏移%d）' % self.offset)
        value = self.packet[self.offset:self.offset + size]
        self.offset += size
        return value

    @property
    def remaining(self):
        return len(self.packet) - self.offset


def _battle_avatar_id(user_id, pet_id):
    return '%d_%d' % (user_id, pet_id)


def _parse_battle_action_return(packet):
    """解析 1310：fighterCount -> BattleActionInfo -> action loops。"""
    reader = _BattlePacketReader(packet)
    fighters = []
    fighter_count = reader.read('>I')
    if fighter_count > 64:
        raise ValueError('1310 fighterCount异常：%d' % fighter_count)
    for _ in range(fighter_count):
        action = {
            'seq': reader.read('>I'),
            'user_id': reader.read('>I'),
            'pet_id': reader.read('>I'),
            'state1': reader.read('>I'),
            'state2': reader.read('>I'),
            'talk_id': reader.read('>i'),
            'hp_change': reader.read('>i'),
            'mp_change': reader.read('>i'),
            'jisheng_user_id': reader.read('>I'),
            'jisheng_pet_id': reader.read('>I'),
            'jisheng_hp_change': reader.read('>h'),
        }
        action['avatar_id'] = _battle_avatar_id(action['user_id'], action['pet_id'])
        loop_count = reader.read('>H')
        if loop_count > 128:
            raise ValueError('1310 loopCount异常：%d' % loop_count)
        loops = []
        for index in range(loop_count):
            loop = {
                'index': index,
                'atk_user_id': reader.read('>I'),
                'atk_pet_id': reader.read('>I'),
                'rebound_state': reader.read('>B'),
                'atk_type': reader.read('>I'),
                'atk_level': reader.read('>B'),
                'increase_hp': reader.read('>h'),
                'rebound_hp': reader.read('>h'),
                'rebound_mp': reader.read('>h'),
                'use_item_id': reader.read('>I'),
                'apt_user_id': reader.read('>I'),
                'apt_pet_id': reader.read('>I'),
                'protector_pos': reader.read('>B'),
                'state1': reader.read('>I'),
                'state2': reader.read('>I'),
                'change_hp': reader.read('>h'),
                'change_mp': reader.read('>h'),
            }
            loop['atk_avatar_id'] = _battle_avatar_id(loop['atk_user_id'], loop['atk_pet_id'])
            loop['apt_avatar_id'] = _battle_avatar_id(loop['apt_user_id'], loop['apt_pet_id'])
            loops.append(loop)
        action['loops'] = loops
        fighters.append(action)
    if reader.remaining:
        raise ValueError('1310响应存在%d字节未解析数据' % reader.remaining)
    return fighters


def _parse_battle_sync_info(packet):
    """解析 1311：回合参战角色/宠物属性快照。"""
    reader = _BattlePacketReader(packet)

    def read_avatar():
        user_id = reader.read('>I')
        pet_id = reader.read('>I')
        avatar = {
            'user_id': user_id,
            'pet_id': pet_id,
            'pet_type_id': reader.read('>I'),
            'position': reader.read('>I'),
            'nick': reader.bytes(16).split(b'\x00', 1)[0].decode('utf-8', errors='replace'),
            'vip_level': reader.read('>I'),
            'color': reader.read('>I'),
            'level': reader.read('>I'),
            'hp': reader.read('>I'),
            'hp_max': reader.read('>I'),
            'mp': reader.read('>I'),
            'mp_max': reader.read('>I'),
            'health_level': reader.read('>I'),
            'change_body_id': reader.read('>I'),
            'auto_battle_count': reader.read('>I'),
        }
        invalid_count = reader.read('>I')
        if invalid_count > 128:
            raise ValueError('1311 invalidSkillCount异常：%d' % invalid_count)
        avatar['invalid_skill_ids'] = [reader.read('>I') for _ in range(invalid_count)]
        avatar['pet_state'] = reader.read('>B')
        avatar['race'] = reader.read('>B')
        avatar['can_catch'] = reader.read('>h') > 0
        avatar['elements'] = {
            'earth': reader.read('>B'),
            'water': reader.read('>B'),
            'fire': reader.read('>B'),
            'wind': reader.read('>B'),
        }
        avatar['profession'] = reader.read('>B')
        item_count = reader.read('>B')
        if item_count > 64:
            raise ValueError('1311 itemCount异常：%d' % item_count)
        avatar['clothes'] = [
            {'instance_id': reader.read('>I'), 'item_id': reader.read('>I'), 'level': reader.read('>H')}
            for _ in range(item_count)
        ]
        skill_count = reader.read('>B')
        if skill_count > 128:
            raise ValueError('1311 skillCount异常：%d' % skill_count)
        avatar['skills'] = [
            {
                'skill_id': reader.read('>I'),
                'max_level': reader.read('>B'),
                'current_level': reader.read('>B'),
                'disable_left_round': reader.read('>B'),
            }
            for _ in range(skill_count)
        ]
        avatar['avatar_id'] = _battle_avatar_id(user_id, pet_id)
        return avatar

    result = {
        'battle_time_stamp': reader.read('>I'),
        'battle_user_id': reader.read('>I'),
        'challenge_leader_id': reader.read('>I'),
        'sneak_flag': reader.read('>B'),
        'is_pk': reader.read('>B') == 1,
    }
    challenger_count = reader.read('>I')
    if challenger_count > 32:
        raise ValueError('1311 challengerCount异常：%d' % challenger_count)
    result['challengers'] = [read_avatar() for _ in range(challenger_count)]
    result['accept_leader_id'] = reader.read('>I')
    accepter_count = reader.read('>I')
    if accepter_count > 32:
        raise ValueError('1311 accepterCount异常：%d' % accepter_count)
    result['accepters'] = [read_avatar() for _ in range(accepter_count)]
    if reader.remaining:
        raise ValueError('1311响应存在%d字节未解析数据' % reader.remaining)
    return result


def _parse_battle_result_pve(packet):
    """解析 1318：经验变化、技能变化及具体掉落物品。"""
    reader = _BattlePacketReader(packet)
    result = {'avatars': [], 'skills': [], 'items': [], 'is_bag_full': False}
    avatar = {
        'pet_id': reader.read('>I'),
        'change_level': reader.read('>I'),
        # BattleResultAvatarInfo.changeExp 在客户端按有符号 int 读取，
        # 失败或扣减经验时不能截断为 0。
        'change_exp': reader.read('>i'),
        'protect_exp': reader.read('>I'),
        'remain_exp': reader.read('>H'),
    }
    result['avatars'].append(avatar)
    if avatar['pet_id'] == 0:
        skill_count = reader.read('>B')
        if skill_count > 128:
            raise ValueError('1318 skillCount异常：%d' % skill_count)
        result['skills'] = [
            {'skill_id': reader.read('>I'), 'change_level': reader.read('>B'), 'change_exp': reader.read('>I')}
            for _ in range(skill_count)
        ]
        result['is_bag_full'] = reader.read('>B') == 1
        item_count = reader.read('>B')
        if item_count > 128:
            raise ValueError('1318 itemCount异常：%d' % item_count)
        result['items'] = [
            {'item_id': reader.read('>I'), 'count': reader.read('>I')}
            for _ in range(item_count)
        ]
    # 部分服务器版本会在已知字段后追加协议扩展字节（长度并不固定），
    # 客户端当前也不会读取这些字段；保留原始尾部，避免把合法响应误判为损坏。
    result['reserved'] = reader.bytes(reader.remaining)
    return result


def _parse_battle_over_notice(packet):
    """解析 1319：战斗结果、任务统计和经验倍率状态。"""
    reader = _BattlePacketReader(packet)
    result = {
        'battle_type': reader.read('>I'),
        'result': reader.read('>I'),
        'flag': reader.read('>I'),
        'fly_to_map_id': reader.read('>I'),
    }
    task_count = reader.read('>I')
    if task_count > 128:
        raise ValueError('1319 taskCount异常：%d' % task_count)
    result['tasks'] = []
    for _ in range(task_count):
        result['tasks'].append({
            'task_id': reader.read('>I'),
            'node_id': reader.read('>I'),
            'monster_type_id': reader.read('>I'),
            'monster_count': reader.read('>H'),
            'monster_target_count': reader.read('>H'),
            'opponent_count': reader.read('>H'),
            'opponent_target_count': reader.read('>H'),
            'target_skill_used_times': reader.read('>H'),
        })
    result['exp_buff'] = {
        'exp_rate': reader.read('>I'),
        'remain_count': reader.read('>i'),
        'skill_exp_rate': reader.read('>I'),
        'skill_remain_count': reader.read('>i'),
        'pet_exp_rate': reader.read('>I'),
        'pet_remain_count': reader.read('>i'),
        'auto_battle_count': reader.read('>i'),
    }
    result['auto_hp'] = reader.read('>I')
    result['auto_mp'] = reader.read('>I')
    if reader.remaining:
        raise ValueError('1319响应存在%d字节未解析数据' % reader.remaining)
    return result


_BATTLE_ITEM_NAMES = {
    180004: '暗精魄',
    180007: '暗精魄',
    180057: '吉普花朵',
    180058: '吉普草叶',
    210003: '3级生命之息',
    230003: 'M2曲奇',
    240001: '风晶碎片',
    240002: '地晶碎片',
    240003: '水晶碎片',
    240004: '火晶碎片',
    290011: '巨石碎片',
    290012: '魔力水晶',
    340001: '吉普豆叶变身卡',
    340002: '吉普豆花变身卡',
    341007: '寂灭骨龙变身卡',
    341011: '怪盗魔力潘变身卡',
    350050: '精灵经验笔记·改',
    360039: '黑银套装大礼包',
    360037: '重置丸春节礼包',
}


def _format_battle_rewards(rewards):
    """合并多个 1318 结算包中的掉落物品并生成可读文本。"""
    totals = {}
    for reward in rewards:
        for item in reward.get('items', ()):
            item_id = item['item_id']
            totals[item_id] = totals.get(item_id, 0) + item['count']
    if not totals:
        return '无道具掉落'
    return '，'.join('%sx%d' % (_BATTLE_ITEM_NAMES.get(item_id, '物品%d' % item_id), totals[item_id])
                    for item_id in sorted(totals))



def _build_hidden_map_enter_packet(str2, sequence=None):
    """构造进入吉普豆 3 号地道（21102）的 1004 请求。"""
    if len(str2) != 4:
        raise ValueError('str2 必须是 4 字节用户标识')
    sequence = random.randint(0, 255) if sequence is None else sequence
    return bytes([0, 0, 0, 0x26, 0x03, 0xec, *str2, 0, 0, 5,
                  sequence, 0, 0, 0, 0, 0, 0, 0x54, 0xf7,
                  0, 0, 0, 0, 0, 0, 0, 0xac, 0, 0, 0, 0xcf,
                  0, 0, 0, 0])


def _build_walk_packet(str2, start_x, start_y, end_x, end_y, direction,
                       walk_step=0, walk_type=0, sequence=None,
                       timestamp=None, channel=6):
    """构造客户端 WalkModule.sendWalk 使用的 1009 请求。"""
    if len(str2) != 4:
        raise ValueError('str2 必须是 4 字节用户标识')
    sequence = random.randint(0, 255) if sequence is None else sequence
    # 客户端写入的是 getTimer() * 0.001，即启动后的秒数，而不是 Unix 毫秒。
    timestamp = int(time.monotonic()) & 0xffffffff if timestamp is None else timestamp
    payload = struct.pack('>hhIIhIIhI', start_x, start_y, end_x, end_y,
                          walk_step, direction, walk_type, 0, timestamp)
    packet_length = 18 + len(payload)
    # SocketConnection 的 TMF 头：长度、命令、用户标识、会话/序号、保留字段。
    header = struct.pack('>IH4B4B4B', packet_length, 1009, *str2,
                         0, 0, channel, sequence, 0, 0, 0, 0)
    return header + payload


def _build_hidden_monster_invite(str2, sequence=None):
    """构造隐形怪遇敌请求：BATTLE_INVITE(1300, 0, 0, 0)。"""
    if len(str2) != 4:
        raise ValueError('str2 必须是 4 字节用户标识')
    sequence = random.randint(0, 255) if sequence is None else sequence
    # 1300 的参数是 3 个 uint（id、petGroupID、petIndexID）。
    payload = bytes(12)
    packet_length = 18 + len(payload)
    header = struct.pack('>IH4B4B4B', packet_length, 1300, *str2,
                         0, 0, 6, sequence, 0, 0, 0, 0)
    return header + payload


def _parse_player_walk_packet(packet, self_id):
    """解析 1009 回包；只返回自己的行走回包。"""
    if len(packet) < 18 + 22 or int.from_bytes(packet[4:6], 'big') != 1009:
        return None
    user_id, pos_x, pos_y, step, direction, walk_type = struct.unpack_from(
        '>IIIHII', packet, 18)
    if user_id != self_id:
        return None
    return {
        'pos_x': pos_x,
        'pos_y': pos_y,
        'step': step,
        'direction': direction,
        'type': walk_type,
    }


def _trace_hidden_event(enabled, label, packet=None, **fields):
    if not enabled:
        return
    details = ' '.join('%s=%s' % (key, value) for key, value in fields.items())
    if packet is not None:
        packet_hex = bytes(packet).hex(' ')
        details = '%s hex=%s' % (details, packet_hex) if details else 'hex=%s' % packet_hex
    print('[hidden-21102] %s%s' % (label, ' ' + details if details else ''))


def _parse_hidden_spawn_from_enter_map(packet):
    """从 1004 EnterMapProtocol 数据中提取本次出生坐标。"""
    # 该入口的 PersonInfo 中包含 mapID=0x54f7，后面固定跟随 7 个
    # 保留字节和两个坐标 uint。坐标会在两个出生点之间变化。
    marker = b'\x00\x00\x54\xf7'
    offset = packet.find(marker)
    if offset < 0 or offset + 16 > len(packet):
        return None
    start = offset + 8
    pos_x, pos_y = struct.unpack_from('>II', packet, start)
    if not (0 < pos_x < 10000 and 0 < pos_y < 10000):
        return None
    return pos_x, pos_y


# 21102 客户端抓包中的行走序列。walk_step 是客户端本地
# WalkModule 的剩余步数，不是服务器 1009 回包里的 step 字段。
_HIDDEN_CAPTURE_WALKS = (
    # start_x, start_y, end_x, end_y, walk_step, direction, type
    (1454, 802, 1179, 662, 0, 5, 0),
    (1186, 665, 1280, 900, 30, 2, 0),
    (1172, 671, 1277, 899, 25, 1, 0),
    (1272, 889, 1184, 661, 24, 6, 0),
    (1186, 666, 1300, 873, 24, 1, 0),
    (1297, 867, 1182, 654, 23, 5, 0),
    (1240, 761, 1240, 761, 13, 5, 1),
)

_HIDDEN_WALK_INTERVAL = 0.5
_HIDDEN_BATTLE_ATTEMPTS = 10


def _trigger_hidden_monster(s, str2, timeout=10,
                                   trace=True,
                                   max_attempts=_HIDDEN_BATTLE_ATTEMPTS,
                                   start_pos=None):
    """在 21102 中重复行走，直到 1300 命中并出现 1305。"""

    session = _get_socket_session(s)
    self_id = int.from_bytes(bytes(str2), 'big')
    # 保留上一场战斗结束时的角色位置。每次调用本函数都会重新创建
    # 局部状态；如果不传入该位置，下一场会退回抓包首点(1454, 802)，
    # 服务器会认为客户端瞬移并主动断开连接。
    current_pos = start_pos
    # 登录时的 1004/1034 可能已经被前面的请求暂存；首个 1009
    # 必须以服务器记录的当前位置为起点，否则服务端不会回 1009。
    for pending in (session._pending_by_command.get(1004, ()),
                    session._pending_by_command.get(1034, ())):
        for cached in reversed(pending):
            if int.from_bytes(cached[4:6], 'big') == 1004:
                current_pos = _parse_hidden_spawn_from_enter_map(cached)
            elif len(cached) >= 38:
                _, _, _, current_x, current_y = struct.unpack_from('>IIIII', cached, 18)
                if 0 < current_x < 10000 and 0 < current_y < 10000:
                    current_pos = (current_x, current_y)
            if current_pos:
                break
        if current_pos:
            break
    _trace_hidden_event(trace, 'cached map position', pos=current_pos)

    for attempt in range(1, max_attempts + 1):
        _trace_hidden_event(trace, 'begin encounter attempt', attempt=attempt,
                            max_attempts=max_attempts)
        server_steps_remaining = None
        retry_attempt = False
        for walk_index, walk_data in enumerate(_HIDDEN_CAPTURE_WALKS, 1):
            start_x, start_y, end_x, end_y, walk_step, direction, walk_type = walk_data
            # 1009 回包的 step 是服务器剩余遇怪步数。若下一次计划上报
            # 的已走步数足以归零，客户端会在途中停止并立即发起遇怪。
            if (server_steps_remaining is not None and
                    0 < server_steps_remaining <= walk_step):
                # 剩余步数对应的是“即将发送”的这一段路线，不能使用
                # 上一段已经完成的路线，否则停止坐标会落在旧路径上。
                move_start_x, move_start_y = start_x, start_y
                move_end_x, move_end_y = end_x, end_y
                distance = ((move_end_x - move_start_x) ** 2 +
                            (move_end_y - move_start_y) ** 2) ** 0.5
                ratio = min(1.0, server_steps_remaining * 5 / distance) \
                    if distance else 0
                stop_x = round(move_start_x + (move_end_x - move_start_x) * ratio)
                stop_y = round(move_start_y + (move_end_y - move_start_y) * ratio)
                start_x = end_x = stop_x
                start_y = end_y = stop_y
                walk_step = server_steps_remaining
                walk_type = 1
                _trace_hidden_event(
                    trace, 'walkStepIdx reached zero', attempt=attempt,
                    remaining=server_steps_remaining, pos=(stop_x, stop_y))
            if walk_index == 1 and current_pos:
                start_x, start_y = current_pos
            packet = _build_walk_packet(
                str2, start_x, start_y, end_x, end_y,
                direction=direction, walk_step=walk_step, walk_type=walk_type,
                # 只有刚发送 1004 后的第一条 1009 使用 channel=5。
                # 已经在 21102 内继续刷下一场时，客户端抓包使用 channel=6；
                # 每场都重发 channel=5 会被服务端当作旧的进图序列处理，
                # 随后通常表现为 1009 超时或主动断开。
                channel=5 if attempt == 1 and walk_index == 1 else 6)
            s.send(packet)
            label = 'send 1009 STOP_CHECK' if walk_type == 1 else 'send 1009 WALK'
            _trace_hidden_event(trace, label, packet,
                                attempt=attempt, walk_index=walk_index,
                                walk_step=walk_step)

            # 停止检查包后发送 1300，并读取短确认。命中时 1305 可能
            # 已经先到达，暂存给 battle() 的 receive_until 消费。
            if walk_type == 1:
                invite = _build_hidden_monster_invite(str2)
                s.send(invite)
                _trace_hidden_event(trace, 'send 1300 BATTLE_INVITE', invite,
                                    attempt=attempt, trigger='walkStepIdx>0',
                                    step=walk_step)
                invite_deadline = time.monotonic() + timeout
                while time.monotonic() < invite_deadline:
                    try:
                        response = session.recv_packet(
                            timeout=max(0.1, invite_deadline - time.monotonic()))
                    except socket.timeout:
                        break
                    command_id = int.from_bytes(response[4:6], 'big')
                    if command_id == 1305:
                        return {'pos_x': end_x, 'pos_y': end_y,
                                'step': walk_step, 'direction': direction,
                                'type': walk_type, 'battle_started': True}
                    if command_id == 1300 and len(response) == 18:
                        error_id = int.from_bytes(response[14:18], 'big')
                        _trace_hidden_event(trace, 'recv 1300 ACK', response,
                                            attempt=attempt, error=error_id)
                        if error_id == 200076:
                            current_pos = (end_x, end_y)
                            retry_attempt = True
                            break
                        if error_id:
                            raise TimeoutError(
                                '21102 1300 返回错误（error=%d）' % error_id)
                    elif command_id == 1009:
                        # 停步包的自身广播会先于 1300 结果到达。
                        continue
                    else:
                        session._pending_by_command.setdefault(command_id, deque()).append(response)
                if retry_attempt:
                    break
                raise TimeoutError('21102 等待 1300/1305 响应超时')

            deadline = time.monotonic() + timeout
            walk = None
            while time.monotonic() < deadline:
                try:
                    response = session.recv_packet(timeout=max(0.1, deadline - time.monotonic()))
                except socket.timeout as exc:
                    raise TimeoutError('21102 等待 1009 超时') from exc
                command_id = int.from_bytes(response[4:6], 'big')
                if command_id != 1009:
                    session._pending_by_command.setdefault(command_id, deque()).append(response)
                    continue
                walk = _parse_player_walk_packet(response, self_id)
                if walk is not None:
                    break
            if walk is None:
                raise TimeoutError('21102 等待 1009 超时')
            _trace_hidden_event(trace, 'recv 1009 SELF', response,
                                attempt=attempt, step=walk_step,
                                server_remaining=walk['step'],
                                pos=(walk['pos_x'], walk['pos_y']))
            server_steps_remaining = walk['step']
            time.sleep(_HIDDEN_WALK_INTERVAL)

        if retry_attempt:
            continue

    raise TimeoutError('21102 重复行走%d轮仍未遇到隐形怪' % max_attempts)


def battle(s, str2, position, login_socket=None, reconnect_uid=None, reconnect_pwd=None, reconnect_fwq=None):
    """执行自动战斗；断线重连时使用传入的账号凭据。"""
    global mmh, mmh_mm
    if reconnect_uid is None:
        reconnect_uid = mmh
    if reconnect_pwd is None:
        reconnect_pwd = mmh_mm
    battle_times = 0
    battle_load_wait = 0.05
    reconnect_attempts = 0

    pet_data = _get_pet_bag(s, str2)
    a = pet_data['pets']
    i = pet_data['pet_count']
    pet_flag = False
    for x in range(i):
        if a[x]['status'] == '主战':
            pet_id = a[x]['pet_id_bytes']
            pet_flag = True
            print(f"找到主战宠物{a[x]['nick']}")
        else:
            pass
    if not pet_flag:
        pet_id = [0, 0, 0, 0]
        print("没有主战宠物！")

    time.sleep(0.1)

    hidden_position = None
    while True:
        try:
            if position == 1:
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
                # 吉普豆 3 号地道
                packet = [0, 0, 0, 0x26, 0x03, 0xec, *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0x54, 0xf7,
                  0, 0, 0, 0, 0, 0, 0, 0xac, 0, 0, 0, 0xcf, 0, 0, 0, 0]
                req = struct.pack(*('38B',), *packet)
                s.send(req)
                time.sleep(0.1)
                # 隐形怪 21102：当前连接只在第一次循环进入地图，
                # 后续战斗结束后继续在原地图内行走；重连时由
                # hidden_map_entered=False 触发重新传送。
                hidden_result = _trigger_hidden_monster(
                    s,
                    str2,
                    trace=False,
                    start_pos=hidden_position,
                )
                hidden_position = (
                    hidden_result.get('pos_x'), hidden_result.get('pos_y'))
                time.sleep(0.1)
            elif position == 4:
                # 传送新生巨石蟹
                packet = [0, 0, 0, 0x26, 3, 0xec, *str2, 0, 0, random.randint(5, 6),
                  random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0x75, 0xfb, 0,
                  0, 0, 0, 0, 0, 0, 0x8b, 0, 0, 0x01, 0x5d, 0, 0, 0, 0]
                s.send(struct.pack('38B', *packet))
                time.sleep(0.1)

                # 2. 刷明雷战斗
                packet = [0, 0, 0, 0x1a, 0x05, 0x18, *str2, 0, 0, random.randint(5, 6),
                        random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0x09, 0xc7, 0, 0, 0, 0]
                s.send(struct.pack('26B', *packet))
                time.sleep(0.1)

            deferred_end_packets = []
            battle_ended = [False]

            def send_packet(packet):
                s.send(struct.pack('%dB' % len(packet), *packet))

            def receive_until(commands, timeout=10):
                """读取并解析服务器帧，直到收到指定命令集合。"""
                pending = set(commands)
                parsed = []
                while pending:
                    response = _get_socket_session(s).recv_packet(timeout=timeout)
                    command_id = int.from_bytes(response[4:6], byteorder='big')
                    if command_id == 1310:
                        parsed.append((command_id, _parse_battle_action_return(response)))
                        pending.discard(command_id)
                    elif command_id == 1311:
                        parsed.append((command_id, _parse_battle_sync_info(response)))
                        pending.discard(command_id)
                    elif command_id == 1307:
                        parsed.append((command_id, None))
                        pending.discard(command_id)
                    elif command_id == 1300:
                        # BATTLE_INVITE 的 18 字节回包是错误确认，错误码位于
                        # 包尾四字节。200076（0x00030d8c）表示本次移动点
                        # 没有可遇到的黑化精灵；不能把它暂存后继续盲等 1305，
                        # 否则会把一次普通未命中误报成连接超时。
                        error_id = int.from_bytes(response[14:18], byteorder='big') \
                            if len(response) >= 18 else None
                        if len(response) == 18 and error_id:
                            raise TimeoutError(
                                '21102 1300 未命中隐形怪（error=%d）' % error_id)
                        parsed.append((command_id, None))
                        pending.discard(command_id)
                    elif command_id in pending:
                        # 无需结构化解析的确认响应（例如 1165）。
                        parsed.append((command_id, None))
                        pending.discard(command_id)
                    elif command_id in (1308, 1313, 1012):
                        parsed.append((command_id, None))
                    elif command_id == 1003:
                        # LEAVE_MAP：战斗状态已被服务器清除，后续不会再有
                        # 1310/1311；立即走外层重连流程，避免等待超时。
                        raise ConnectionError('服务器要求离开当前地图（1003）')
                    elif command_id in (1318, 1319):
                        # 结算包可能紧跟最后一个回合包到达，不能放入
                        # SocketSession 的待处理队列（recv_packet(None)
                        # 不会主动消费该队列）。
                        deferred_end_packets.append(response)
                        battle_ended[0] = True
                        pending.clear()
                    else:
                        # 其他响应保留给后续调用，避免无声丢包。
                        _get_socket_session(s)._pending_by_command.setdefault(command_id, deque()).append(response)
                return parsed

            # 1300 只是遇敌请求确认；客户端还会等待 1305
            # BATTLE_START，收到后才开始发送 1306 资源加载进度。
            if position == 3 and not hidden_result.get('battle_started'):
                receive_until({1305}, timeout=10)

            for battle_load_percent in range(10, 101, 10):
                # BATTLE_RES_LOAD_PROGRESS 1306：进入战斗读秒（0-100）。
                send_packet([0, 0, 0, 22, 5, 26, *str2, 0, 0, random.randint(5, 6),
                             random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, battle_load_percent])
                # 新生巨石蟹的触发/读秒阶段处理较慢，过快连续发送
                # 1306 会被服务器按异常会话复位连接。
                time.sleep(0.3 if position == 4 else battle_load_wait)

            # BATTLE_INIT_STATE 1317，然后等待 BATTLE_BEGIN_NOTICE 1307。
            send_packet([0, 0, 0, 22, 5, 37, *str2, 0, 0, 5, random.randint(0, 255),
                         0, 0, 0, 0, 0, 0, 0, 1])
            # 新生巨石蟹地图的 1304/1305 触发流程较慢，服务端可能在
            # 1317 确认后持续发送 1306/1316 十几秒才发 1307。
            start_timeout = 30 if position == 4 else 10
            receive_until({1307}, timeout=start_timeout)

            # 持续提交回合行动，直到服务器发来 1318 结算包。
            # 战斗可能在任意回合结束，不能按地点预设回合数截断。
            round_count = 0
            while not battle_ended[0]:
                round_count += 1
                send_packet([0, 0, 0, 38, 5, 28, *str2, 0, 0, 5, random.randint(0, 255),
                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             255, 255, 255, 255, 0, 15, 66, 64, 0, 0, 0, 1])
                time.sleep(0.05)
                send_packet([0, 0, 0, 38, 5, 28, *str2, 0, 0, 5, random.randint(0, 255),
                             0, 0, 0, 0, *pet_id, 0, 0, 0, 0, 255, 255, 255, 255,
                             0, 15, 66, 64, 0, 0, 0, 1])
                time.sleep(0.05)
                # SET_ROLE_FLAG 1012：通知服务器本回合行动已提交。
                send_packet([0, 0, 0, 26, 3, 244, *str2, 0, 0, 5, random.randint(0, 255),
                             0, 0, 0, 0, 0, 0, 0, 0x20, 0, 0, 0, 0])
                receive_until({1310, 1311})
                if battle_ended[0]:
                    break
                # 下一回合不要紧贴上一回合响应发送，给服务端完成回合
                # 状态切换的时间；战斗过程记录中动作间隔约为 50ms。
                time.sleep(0.05)

            # 1318 可能按掉落条目重复返回；1319 才是战斗结束通知。
            rewards = []
            while True:
                if deferred_end_packets:
                    response = deferred_end_packets.pop(0)
                else:
                    response = _get_socket_session(s).recv_packet(timeout=10)
                command_id = int.from_bytes(response[4:6], byteorder='big')
                if command_id == 1318:
                    rewards.append(_parse_battle_result_pve(response))
                elif command_id == 1319:
                    over = _parse_battle_over_notice(response)
                    battle_result = over['result']
                    reward_text = _format_battle_rewards(rewards)
                    break
                elif command_id == 1310:
                    _parse_battle_action_return(response)
                elif command_id == 1311:
                    _parse_battle_sync_info(response)
                else:
                    _get_socket_session(s)._pending_by_command.setdefault(command_id, deque()).append(response)

            # 提交战斗任务进度（TASK_SUBMIT_BUFFER 1165），并确认服务器已接收。
            task_packet = [0, 0, 0, 154, 4, 141, *str2, 0, 0, 6,
                           random.randint(0, 255)] + [0] * 140
            task_packet[20:24] = [0x98, 0x5B, 0x03, 0x0B]
            task_packet[71:75] = [0x0C, 0xFA, 0x00, 0x01]
            send_packet(task_packet)
            receive_until({1165})

            # 战斗退出及角色/背包刷新请求。对应响应暂按需求忽略。
            send_packet([0, 0, 0, 26, 4, 6, *str2, 0, 0, 5,
                         random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])
            send_packet([0, 0, 0, 18, 5, 64, *str2, 0, 0, 5,
                         random.randint(0, 255), 0, 0, 0, 0])
            # 等待 BATTLE_MODULE_EXIT_REPORT (1344) 确认，避免下一场
            # 新生巨石蟹触发包紧贴上一场退出请求发送。
            receive_until({1344}, timeout=10)
            # send_packet([0, 0, 0, 18, 6, 18, *str2, 0, 0, 5,
            #              random.randint(0, 255), 0, 0, 0, 0])
            # send_packet([0, 0, 0, 18, 4, 82, *str2, 0, 0, 5,
            #              random.randint(0, 255), 0, 0, 0, 0])
            # send_packet([0, 0, 0, 22, 3, 238, *str2, 0, 0, 5,
            #              random.randint(0, 255), 0, 0, 0, 0, *str2])

            if battle_result == 1:
                battle_times += 1
                print('%s:战斗结束，累计完成%d次战斗，共%d回合，获得战利品%s' %
                      (time.strftime('%H:%M:%S'), battle_times, round_count, reward_text))
            elif battle_result == 2:
                print('%s:战斗失败，共%d回合' % (time.strftime('%H:%M:%S'), round_count))
            else:
                print('%s:战斗结果%d' % (time.strftime('%H:%M:%S'), battle_result))
            reconnect_attempts = 0
            # 星豆治疗
            packet = [0, 0, 0, 22, 4, 1, *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 5]
            req = struct.pack(*('22B',), *packet)
            s.send(req)
            # 连续无间隔刷战斗会触发服务端连接保护；每场结束后留出
            # 一段冷却时间，避免下一场请求紧贴结算/刷新包。
            if battle_times % 20 == 0:
                prop_info, _ = _get_prop_bag_info(s, str2)
                for prop in prop_info:
                    inid = prop['item_id']
                    if  inid in _BATTLE_ITEM_NAMES:
                        _prop_backto_store(s, str2, inid, prop['quantity'])
                        print('%s已放入仓库,共%d个' % (_BATTLE_ITEM_NAMES.get(inid, '物品%d' % inid), prop['quantity']))
                equipment_info, _ = _get_equipment_bag_info(s, str2)
                for equipment in equipment_info:
                    inid = equipment['item_id']
                    if inid in [
                        142501, 142502, 142503, 142504, 142505, # 紫炼套装
                        142001, 142002, 142003, 142004, 142005, # 祈福套装
                        140280, 140281                          # 狩猎护巾
                        ] :
                        _equipment_sell(s, str2, inid, equipment['instance_id'])
            time.sleep(1)
        # SocketSession 在对端主动关闭时抛出 ConnectionError；与连接重置/
        # 中止一样重新登录，避免战斗循环因未捕获异常直接退出。
        except (ConnectionError, TimeoutError) as exc:
            reconnect_attempts += 1
            delay = min(60, 5 * (2 ** min(reconnect_attempts - 1, 3)))
            print('战斗连接异常：%s，%d秒后重新登录（第%d次）' %
                  (exc, delay, reconnect_attempts))
            for stale_socket in (s, login_socket):
                if stale_socket is None:
                    continue
                try:
                    stale_socket.close()
                except OSError:
                    pass
            time.sleep(delay)
            login_result = login_taomi(reconnect_uid, reconnect_pwd, model=1, fwq=reconnect_fwq if (reconnect_fwq in range(1,11)) else 0)
            if login_result is None:
                raise ConnectionError('战斗重连登录失败') from exc
            login_socket, s, str2 = login_result
            hidden_map_entered = False
            hidden_position = None

def exchangelb(s, str2, type, count):
    if count <= 0:
        print('兑换数量必须大于0')
        return
    if type == 1: # 巨石碎片->奖牌(7:1),2,3巨石->大丸子
        max_batch_size = 50
        remaining_count = count
        while remaining_count > 0:
            batch_size = min(remaining_count, max_batch_size)
            _fetch_item_from_store(s, str2, 290011, batch_size * 7)
            _exchange_item(s, str2, 0x4e, 0x72, batch_size)  
            remaining_count -= batch_size
            time.sleep(0.1)               
    elif type == 2: # 巨石碎片->奖牌->宝物(4*7:1)
        max_batch_size = 50
        remaining_count = count
        while remaining_count > 0:
            batch_size = min(remaining_count, max_batch_size)
            _fetch_item_from_store(s, str2, 290011, batch_size * 28)
            _exchange_item(s, str2, 0x4e, 0x72, batch_size * 4) 
            _exchange_item(s, str2, 0x27, 0x79, batch_size)  
            remaining_count -= batch_size
            time.sleep(0.1)               
    elif type == 3: # 巨石碎片->大丸子(2:1)
        max_batch_size = 50
        remaining_count = count
        while remaining_count > 0:
            batch_size = min(remaining_count, max_batch_size)
            _fetch_item_from_store(s, str2, 290011, batch_size * 2)
            _exchange_item(s, str2, 0x4e, 0x74, batch_size)
            remaining_count -= batch_size
            time.sleep(0.1) 
    else:
        print('兑换类型错误')
        return

    print('兑换成功')

def tp_test(s, str2):
    # packet = [0, 0, 0, *[0x26, 0x03, 0xec], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0,
    #                       *[0x2b, 0xc2], 0, 0, 0, 0, 0, 0, *[0x03, 0x84], 0, 0, *[0x02, 0x8a], 0, 0, 0, 0]
    packet = [0, 0, 0, *[0x26, 0x03, 0xec], *str2, 0, 0, 5, random.randint(0, 255), 0, 0, 0, 0, 0, 0,
                        *[0x2b, 0xc2], 0, 0, 0, 0, 0, 0, *[0x04, 0x7e], 0, 0, *[0x02, 0x58], 0, 0, 0, 0]
    req = struct.pack(*('38B',), *packet)
    s.send(req)
    time.sleep(0.1)

    print('测试完成')

if __name__ == '__main__':
    login_interface('account.txt')

