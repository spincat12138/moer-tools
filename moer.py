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
                position = int(input(['请输入地点：1海滩，2草木树海']))
                battle(s2, str2, position)
            if m == 999:
                jiadian_test(s2, str2,[0x63, 0x22, 0x1D, 0xDE])
        s.close()
        s2.close()
        print('成功退出')
    # if model == 2:
    #     zgz(s2, str2)
    #     print('%d成功砸罐子翻牌' % uid)
    #     clearbag(s2, str2)
    #     cleanequipment(s2, str2)
    #     time.sleep(3)
    #     s.close()
    #     s2.close()
    # if model == 3:
    #     print("开始分经验")
    #     fjy(s2, str2, 1)
    #     time.sleep(3)
    #     s.close()
    #     s2.close()
    #     print('%d分经验完毕' % uid)


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
            exit(0)

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
        'quality': color_id,
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
            exit(0)
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
                exit(0)
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


def battle(s, str2, position):
    global mmh, mmh_mm
    battle_times = 0
    battle_load_wait = 0.1

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
    skill_time = 10

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
                # 进入战斗读秒（0-100） BATTLE_RES_LOAD_PROGRESS 1306
                packet = [0, 0, 0, 22, 5, 26, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, 0,
                          0,
                          0, battle_load_percent]
                req = struct.pack(*('22B',), *packet)
                s.send(req)
                time.sleep(battle_load_wait)

            # BATTLE_INIT_STATE 1317
            packet = [0, 0, 0, 22, 5, 37, *str2, 0, 0, 6, random.randint(0, 255), 0, 0, 0, 0, 0, 0, 0, 1]
            req = struct.pack(*('22B',), *packet)
            s.send(req)
            time.sleep(0.1)

            # 自动释放技能
            for i in range(0, skill_time):
                # 人物自动攻击 BATTLE_ROUND_ACTION 1308
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

            # PERSON_STATUS_CHANGE_NOTICE, 1030
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

def jiadian_test(s, str2, pet_id):
    packet = [0, 0, 0, 0x20, 0x06, 0x46, *str2, 0, 0, random.randint(5, 6), random.randint(0, 255), 0, 0, 0, 0, *pet_id, 0, 0,
              0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    t1 = tuple(packet)
    req = struct.pack(*('32B',), *t1)
    for i in range(150):
        print(f'第{i + 1}次测试')            
        s.send(req)
        rev = tuple(s.recv(2048))
        print('返回结果:', rev)
        print('-------------------------------')
        time.sleep(0.1)

    print('测试完成')

if __name__ == '__main__':
    login_interface('account.txt')

