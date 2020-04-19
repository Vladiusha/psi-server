import socket
from math import sqrt

SERVER_KEY = 54621
CLIENT_KEY = 45328
TIMEOUT = 1
TIMEOUT_RECHARGING = 5
coordinates_base = [
    (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),
    (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
    (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2)
]

coordinates_visited = []

global client_messages


# Function
def find_nearest_coordinates(robot):
    coordinates_visited.append((robot.x, robot.y))
    coordinates_with_dist = []
    for x, y in coordinates_base:
        if (x, y) not in coordinates_visited:
            coordinates_with_dist.append((sqrt((x - robot.x) ** 2 + (y - robot.y) ** 2), x, y))

    coordinates_with_dist.sort()
    if len(coordinates_with_dist) == 0:
        print(coordinates_visited )
    return coordinates_with_dist[0][1], coordinates_with_dist[0][2]


messeges = {
    'SERVER_MOVE': b'102 MOVE\a\b',
    'SERVER_TURN_LEFT': b'103 TURN LEFT\a\b',
    'SERVER_TURN_RIGHT': b'104 TURN RIGHT\a\b',
    'SERVER_PICK_UP': b'105 GET MESSAGE\a\b',
    'SERVER_LOGOUT': b'106 LOGOUT\a\b',
    'SERVER_OK': b'200 OK\a\b',
    'SERVER_LOGIN_FAILED': b'300 LOGIN FAILED\a\b',
    'SERVER_SYNTAX_ERROR': b'301 SYNTAX ERROR\a\b',
    'SERVER_LOGIC_ERROR': b'302 LOGIC ERROR\a\b'
}


def my_isdigit(number):
    if number[0] == '-':
        return str(number[1:]).isdigit()
    else:
        return str(number).isdigit()

def my_recv(client_socket, client_messages, to_do, rechargin):  # to_do это какое сообщение мы хотим получить
    data = ''
    message = ''
    while True:
        if rechargin == 'RECHARGING':
            client_socket.settimeout(TIMEOUT_RECHARGING)
        else:
            client_socket.settimeout(TIMEOUT)
        try:
            message = client_socket.recv(100)
            if rechargin == 'RECHARGING' and 'FULL POWER' not in message.decode('ascii'):
                client_socket.sendall(messeges['SERVER_LOGIC_ERROR'])
                raise socket.timeout
        except socket.timeout:
            client_socket.close()
            return client_messages, True

        client_socket.settimeout(None)
        data += message.decode('ascii')

        # Когда ожидаем имя при аунтификации
        if to_do == 'AUNT' and '\a\b' not in data and len(
                data) >= 12:  # Больше равно 12 потому чтот максимальная длина 12 , тоесть 12 может быть но в этой ситуации не может быть 12 так как нету \a\b значит прибавиться минимум еще один символ
            client_socket.sendall(messeges['SERVER_SYNTAX_ERROR'])
            client_socket.close()
            return client_messages, True
        # Когда ожидаем сообщение при его поднятие
        if to_do == 'GET_MESSAGE' and '\a\b' not in data and len(data) >= 100:
            client_socket.sendall(messeges['SERVER_SYNTAX_ERROR'])
            client_socket.close()
            return client_messages, True
        # Когда ожидаем координаты
        if to_do == 'MOVE' and '\a\b' not in data and len(data) >= 12:
            client_socket.sendall(messeges['SERVER_SYNTAX_ERROR'])
            client_socket.close()
            return client_messages, True

        if '\a\b' in data:
            break

    print('Line 93: ')
    print(client_messages)

    # Если в буффере было сообщение без \a\b то дополняем его
    if len(client_messages) == 1:
        if '\a\b' not in client_messages[0]:
            client_messages[0] += data[0:data.find('\a\b') + 2]
            data = data[data.find('\a\b') + 2:]

    # Добавляю сообщения у которых есть \a\b
    while data.find('\a\b') != -1:
        client_messages.append(data[0:data.find('\a\b') + 2])
        data = data[data.find('\a\b') + 2:]
    # Добавляю сообщение если осталось какое-то без \a\b
    if data != '':
        client_messages.append(data)

    print('Line 110: ')
    print(client_messages)

    return client_messages, False


class Robot:
    def __init__(self, x=0, y=0, direction=None):
        self.x = x
        self.y = y
        self.direction = direction


def check_client_confirmation(client_socket, name, client_messages):
    # Получаю от клиента хэш вместе с КЛИЕНТ_КЛЮЧ
    print('Line 116: ')
    print(client_messages)
    hash = 0
    if len(client_messages) == 0:
        client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'NO')
        if timeout:
            return 'TIMEOUT', client_messages

    while '\a\b' not in client_messages[0]:
        client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'NO')
        if timeout:
            return 'TIMEOUT', client_messages

    hash_ascii = client_messages[0]
    hash_ascii = hash_ascii[:-2]
    client_messages.remove(client_messages[0])

    if hash_ascii == 'RECHARGING':
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'RECHARGING')
            if timeout:
                return 'TIMEOUT', client_messages

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'NO')
            if timeout:
                return 'TIMEOUT', client_messages

        print('Line 144: ')
        print(client_messages)

        hash_ascii = client_messages[0]
        hash_ascii = hash_ascii[:-2]
        client_messages.remove(client_messages[0])

        if hash_ascii != 'FULL POWER':
            return 'TIMEOUT', client_messages
        else:
            if len(client_messages) == 0:
                client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'NO')
                if timeout:
                    return 'TIMEOUT', client_messages

            while '\a\b' not in client_messages[0]:
                client_messages, timeout = my_recv(client_socket, client_messages, 'HASH', 'NO')
                if timeout:
                    return 'TIMEOUT', client_messages

            hash_ascii = client_messages[0]
            hash_ascii = hash_ascii[:-2]
            client_messages.remove(client_messages[0])


    # Если хэш не число
    if not hash_ascii.isdigit() or len(hash_ascii) > 5:
        return 'SYNTAX ERROR', client_messages

    hash = int(hash_ascii)

    hash = (hash - CLIENT_KEY) % 65536
    if hash == name_to_hash(name):
        return "OK", client_messages
    else:
        return 'NOT EQUAL', client_messages


def accept_code_server(hash):
    return (hash + SERVER_KEY) % 65536


def name_to_hash(name):
    hash = 0
    for symbol in name:
        hash += ord(symbol)
    hash = (hash * 1000) % 65536
    return hash


def auntification(client_socket, client_messages):
    # Получаю имя робота
    if len(client_messages) == 0:
        client_messages, timeout = my_recv(client_socket, client_messages, 'AUNT', 'NO')
        if timeout:
            return False, client_messages, True

    while '\a\b' not in client_messages[0]:
        client_messages, timeout = my_recv(client_socket, client_messages, 'AUNT', 'NO')
        if timeout:
            return False, client_messages, True

    name = client_messages[0]
    name = name[:-2]  # Удаляю \a\b в конце
    if len(name) > 10:
        client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
        return False, client_messages, False

    # Удаляю сообщение из списка
    client_messages.remove(client_messages[0])
    # ============================================
    # Возможно можно удалить
    errors = False
    if '\a\b' in name:
        errors = True
    # ============================================
    hashCodeServer = str(accept_code_server(name_to_hash(name))) + '\a\b'  # Получаю хэщ имени вместе с СЕРВЕР_КЛЮЧ
    client_socket.sendall(hashCodeServer.encode('ascii'))  # Отправляю хэш клиенту

    # Получаю от клиента хэш вместе с КЛИЕНТ_КЛЮЧ
    compare_client_hash, client_messages = check_client_confirmation(client_socket, name, client_messages)

    if compare_client_hash == 'OK':  # Сравниваю хэш клиента и тот что считает моей сервер
        if errors is True:
            client_socket.send(messeges['SERVER_LOGIN_FAILED'])
            return False, client_messages, False
        client_socket.send(messeges['SERVER_OK'])
        return True, client_messages, False
    elif compare_client_hash == 'NOT EQUAL':
        client_socket.send(messeges['SERVER_LOGIN_FAILED'])
        return False, client_messages, False
    elif compare_client_hash == 'TIMEOUT':
        return False, client_messages, True
    else:  # Если хэщ клиента который прислал пользователь не верен, например состоит не только из цифр
        client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
        return False, client_messages, False


def get_coordinates(data):
    messege = data.split(' ')
    if len(messege) != 3:
        return 0, 0, True
    ok_ascii = str(messege[0])
    x_ascii = str(messege[1])
    y_ascii = str(messege[2])

    if ok_ascii != 'OK' or not my_isdigit(x_ascii) or not my_isdigit(y_ascii):
        return 0, 0, True
    x, y = list(map(int, messege[1:3]))
    return x, y, False


def get_direction(x1, y1, x2, y2):
    if x1 == x2:
        if y1 < y2:
            return 'UP'
        elif y1 > y2:
            return 'BOTTOM'
        else:
            return False
    elif y1 == y2:
        if x1 < x2:
            return 'RIGHT'
        elif x1 > x2:
            return 'LEFT'
        else:
            return False


def get_dest_direction(x1, y1, x2, y2):
    if x1 == -2 and y1 == 11:
        if x1 < x2:
            return 'RIGHT'
        elif x1 > x2:
            return 'LEFT'
        else:
            if y1 > y2:
                return 'BOTTOM'
            elif y1 < y2:
                return 'UP'
            else:
                return 'EQUAL'
    else:
        if x1 < x2:
            return 'RIGHT'
        elif x1 > x2:
            return 'LEFT'
        else:
            if y1 > y2:
                return 'BOTTOM'
            elif y1 < y2:
                return 'UP'
            else:
                return 'EQUAL'


def get_dest_coordinates(x, y):
    to_upper_left_corner = abs(x - (-2)) + abs(y - 2)
    to_bottom_left_corner = abs(x - (-2)) + abs(y - (-2))
    to_bottom_right_corner = abs(x - 2) + abs(y - (-2))
    to_upper_right_corner = abs(x - 2) + abs(y - 2)
    if min(to_bottom_left_corner, to_bottom_right_corner, to_upper_left_corner,
           to_upper_right_corner) == to_bottom_left_corner:
        return -2, -2
    elif min(to_bottom_left_corner, to_bottom_right_corner, to_upper_left_corner,
             to_upper_right_corner) == to_bottom_right_corner:
        return 2, -2
    elif min(to_bottom_left_corner, to_bottom_right_corner, to_upper_left_corner,
             to_upper_right_corner) == to_upper_left_corner:
        return -2, 2
    else:
        return 2, 2


def choose_movement(direction, dest_direction):
    if direction == 'UP' and (dest_direction == 'RIGHT' or dest_direction == 'BOTTOM'):
        return 'RIGHT', messeges['SERVER_TURN_RIGHT']
    elif direction == 'UP' and dest_direction == 'LEFT':
        return 'LEFT', messeges['SERVER_TURN_LEFT']
    elif direction == 'RIGHT' and (dest_direction == 'BOTTOM' or dest_direction == 'LEFT'):
        return 'BOTTOM', messeges['SERVER_TURN_RIGHT']
    elif direction == 'RIGHT' and dest_direction == 'UP':
        return 'UP', messeges['SERVER_TURN_LEFT']
    elif direction == 'BOTTOM' and (dest_direction == 'LEFT' or dest_direction == 'UP'):
        return 'LEFT', messeges['SERVER_TURN_RIGHT']
    elif direction == 'BOTTOM' and dest_direction == 'RIGHT':
        return 'RIGHT', messeges['SERVER_TURN_LEFT']
    elif direction == 'LEFT' and (dest_direction == 'UP' or dest_direction == 'RIGHT'):
        return 'UP', messeges['SERVER_TURN_RIGHT']
    elif direction == 'LEFT' and dest_direction == 'BOTTOM':
        return 'BOTTOM', messeges['SERVER_TURN_LEFT']
    else:
        return direction, messeges['SERVER_MOVE']


def find_message(robot, client_socket, client_messages):
    client_socket.sendall(messeges['SERVER_PICK_UP'])

    # Получение cooбщения
    if len(client_messages) == 0:
        client_messages, timeout = my_recv(client_socket, client_messages, 'GET_MESSAGE', 'NO')
        if timeout:
            return True

    while '\a\b' not in client_messages[0]:
        client_messages, timeout = my_recv(client_socket, client_messages, 'GET_MESSAGE', 'NO')
        if timeout:
            return True

    data = client_messages[0]
    data = data[:-2]
    client_messages.remove(client_messages[0])

    if len(data) > 0:
        client_socket.sendall(messeges['SERVER_LOGOUT'])
        return False
    # Coordinates where robot need to go
    x_dest, y_dest = find_nearest_coordinates(robot)
    dest_direction = get_dest_direction(robot.x, robot.y, x_dest, y_dest)

    while True:
        if dest_direction == 'EQUAL':  # Если не подняли сообщение но пришли к нужной точке, то меняем точку куда идти
            # Coordinates where robot need to go
            x_dest, y_dest = find_nearest_coordinates(robot)
            dest_direction = get_dest_direction(robot.x, robot.y, x_dest, y_dest)

        # Что робот должен делать
        robot.direction, movement = choose_movement(robot.direction, dest_direction)
        client_socket.send(movement)

        # Получение информации
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        data = client_messages[0]
        data = data[:-2]
        client_messages.remove(client_messages[0])

        if data == 'RECHARGING':
            # Получение информации
            if len(client_messages) == 0:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            while '\a\b' not in client_messages[0]:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            data = client_messages[0]
            data = data[:-2]

            if data != 'FULL POWER':
                return True
            else:
                client_messages.remove(client_messages[0])
                data = client_messages[0]
                data = data[:-2]
                client_messages.remove(client_messages[0])


        # Где я сейчас
        robot.x, robot.y, syntax_error = get_coordinates(data)

        # Если что то не так с координатами
        if syntax_error:
            #print('Error in line 329\n')
            client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
            client_socket.close()
            return True  # Тру потому что чтоб программа закрлась максимально быстро и не закрывала еще раз сокет

        # В каком направление двигаться
        dest_direction = get_dest_direction(robot.x, robot.y, x_dest, y_dest)

        # Если я пришел в нужную точку, то попробовать получить сообщение
        if dest_direction == 'EQUAL':
            client_socket.sendall(messeges['SERVER_PICK_UP'])
            # Получение информации
            if len(client_messages) == 0:
                client_messages, timeout = my_recv(client_socket, client_messages, 'GET_MESSAGE', 'NO')
                if timeout:
                    return True

            while '\a\b' not in client_messages[0]:
                client_messages, timeout = my_recv(client_socket, client_messages, 'GET_MESSAGE', 'NO')
                if timeout:
                    return True


            data = client_messages[0]
            data = data[:-2]
            client_messages.remove(client_messages[0])
            if len(data) > 0:
                break
    client_socket.sendall(messeges['SERVER_LOGOUT'])
    return False


def movement_of_robot(client_socket, client_messages):
    # First step
    client_socket.send(messeges['SERVER_MOVE'])
    data = ''

    # Получение информации
    if len(client_messages) == 0:
        client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
        if timeout:
            return True

    while '\a\b' not in client_messages[0]:
        client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
        if timeout:
            return True

    data = client_messages[0]
    data = data[:-2]
    client_messages.remove(client_messages[0])
    print('Line 464: ')
    print(client_messages)

    if data == 'RECHARGING':
        # Получение информации
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
            if timeout:
                return True

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
            if timeout:
                return True

        data = client_messages[0]
        data = data[:-2]

        if data != 'FULL POWER':
            return True
        else:
            client_messages.remove(client_messages[0])
            data = client_messages[0]
            data = data[:-2]
            client_messages.remove(client_messages[0])


    x0, y0, syntax_error = get_coordinates(data)

    # Если что то не так с координатами
    if syntax_error:
        client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
        return False

    print('Line 499: ')
    print(client_messages)

    # Second step
    client_socket.send(messeges['SERVER_MOVE'])

    # Получение информации
    if len(client_messages) == 0:
        client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
        if timeout:
            return True

    while '\a\b' not in client_messages[0]:
        client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
        if timeout:
            return True

    data = client_messages[0]
    data = data[:-2]
    client_messages.remove(client_messages[0])

    print('Line 520: ')
    print(client_messages)

    if data == 'RECHARGING':
        # Получение информации
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
            if timeout:
                return True

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
            if timeout:
                return True

        data = client_messages[0]
        data = data[:-2]

        if data != 'FULL POWER':
            return True
        else:
            client_messages.remove(client_messages[0])
            data = client_messages[0]
            data = data[:-2]
            client_messages.remove(client_messages[0])

    x1, y1, syntax_error = get_coordinates(data)

    # Если что то не так с координатами
    if syntax_error:
        client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
        return False

    print('Line 550: ')
    print(client_messages)

    # Если робот после приказа MOVE не пошивилился
    while x0 == x1 and y0 == y1:
        client_socket.send(messeges['SERVER_MOVE'])

        # Получение информации
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        data = client_messages[0]
        data = data[:-2]
        client_messages.remove(client_messages[0])

        if data == 'RECHARGING':
            # Получение информации
            if len(client_messages) == 0:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            while '\a\b' not in client_messages[0]:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            data = client_messages[0]
            data = data[:-2]

            if data != 'FULL POWER':
                return True
            else:
                client_messages.remove(client_messages[0])
                data = client_messages[0]
                data = data[:-2]
                client_messages.remove(client_messages[0])

        x1, y1, syntax_error = get_coordinates(data)

        # Если что то не так с координатами
        if syntax_error:
            client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
            return False


        # Start direction
    direction = get_direction(x0, y0, x1, y1)

    # If robot already in base
    if (x1, y1) in coordinates_base:
        robot = Robot(x1, y1, direction)
        timeout = find_message(robot, client_socket, client_messages)
        if timeout:
            return True
        else:
            return False

    # dest = destination
    x_dest, y_dest = get_dest_coordinates(x1, y1)

    print('WHERE I MUST TO GO')
    print(x_dest)
    print(y_dest)

    # Куда я должен идти
    dest_direction = get_dest_direction(x1, y1, x_dest, y_dest)

    robot = Robot(x1, y1, direction)

    while dest_direction != 'EQUAL':
        robot.direction, movement = choose_movement(robot.direction, dest_direction)
        client_socket.send(movement)

        # Получение информации
        if len(client_messages) == 0:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        while '\a\b' not in client_messages[0]:
            client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'NO')
            if timeout:
                return True

        data = client_messages[0]
        data = data[:-2]
        client_messages.remove(client_messages[0])

        print('Line: 641')
        print(client_messages)

        if data == 'RECHARGING':
            # Получение информации
            if len(client_messages) == 0:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            while '\a\b' not in client_messages[0]:
                client_messages, timeout = my_recv(client_socket, client_messages, 'MOVE', 'RECHARGING')
                if timeout:
                    return True

            print('Line: 653')
            print(client_messages)

            data = client_messages[0]
            data = data[:-2]

            print('Line: 662')
            print(data)

            if data != 'FULL POWER':
                return True
            else:
                client_messages.remove(client_messages[0])
                data = client_messages[0]
                data = data[:-2]
                client_messages.remove(client_messages[0])
                print('Line: 662')
                print(client_messages)


        # Где я сейчас
        robot.x, robot.y, syntax_error = get_coordinates(data)

        # Если что то не так с координатами
        if syntax_error:
            client_socket.send(messeges['SERVER_SYNTAX_ERROR'])
            return False

            # Куда я должен идти
        dest_direction = get_dest_direction(robot.x, robot.y, x_dest, y_dest)
    print('I AM HERE')
    timeout = find_message(robot, client_socket, client_messages)
    if timeout:
        return True
    else:
        return False


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 9945))
server_socket.listen(1)

while True:
    # Бесконечно обрабатываем входящие подключения
    client_socket, client_address = server_socket.accept()
    print('Connected by', client_address)
    while True:
        # Очищаю массив хранящий уже посещяемые координаты
        coordinates_visited.clear()
        # Пока клиент не отключился, читаем передаваемые
        # им данные и отправляем их обратно
        client_messages = []
        client_messages, timeout = my_recv(client_socket, client_messages, 'AUNT', 'NO')

        # Проверка чтоб если приняли мы сообщение за 1 секунду
        if timeout:
            break

        aunt_good, client_messages, timeout = auntification(client_socket, client_messages)

        # Проверка чтоб если приняли мы сообщение за 1 секунду
        if timeout:
            break

        if not aunt_good:
            client_socket.close()  # Если LOGIN FAILED
            break

        timeout = movement_of_robot(client_socket, client_messages)

        # Проверка чтоб если приняли мы сообщение за 1 секунду
        if timeout:
            break

        client_socket.close()  # КОНЕЦ
        break

