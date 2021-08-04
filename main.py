import time
import math
import pymurapi as mur
import cv2 as cv
import numpy as np

auv = mur.mur_init()

low_hsv_red = (0, 70, 5)
max_hsv_red = (30, 255, 255)

low_hsv_red2 = (140, 70, 5)
max_hsv_red2 = (180, 255, 255)

low_hsv_yellow = (20, 70, 30)
max_hsv_yellow = (70, 255, 255)

low_hsv_blue = (106, 174, 88)
max_hsv_blue = (255, 255, 255)

low_hsv_green = (0, 0, 0) #?
max_hsv_green = (255, 255, 255) #?

left_motor = 1
right_motor = 2
speed_left = -1
speed_right = -1

x1, y1 = 0, 0
x2, y2 = 30, 240

cap0 = cv.VideoCapture(0)
mur_view = auv.get_videoserver()

#........ОБЩИЕ........

class PD(object):  # Класс ПД регулятора
    _kd = 0
    _kp = 0
    _timer = 0
    _prev = 0

    def __init__(self): pass

    def set_p(self, val):  # Прапорциональный
        self._kp = val

    def set_d(self, val):  # Дифферинсальный
        self._kd = val

    def process(self, e):
        timer = int(round(time.time() * 1000))
        out = self._kp * e + self._kd * (e - self._prev) / (timer - self._timer)
        self._timer = timer
        self._prev = e
        return out

        # ДЛЯ МОТОРОВ И ДВИЖЕНИЯ

def show():
    ok, frame = cap0.read()
    return frame

def clamp(e, max = 100, min = -100):  # Функция
    if e > max:
        return max
    if e < min:
        return min
    return e

def clamp_to180(angle):  # 180 градусов
    if angle > 180:
        return angle - 360
    if angle < -180:
        return angle + 360
    return angle

def frame_crop(frame, x1, y1, x2, y2):
    frame_crop = frame[y1:y2, x1:x2]
    cv.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
    return frame_crop

def keep_yaw(yaw_to_set, speed, k = 1):
    current_yaw = auv.get_yaw()
    e = clamp_to180(current_yaw - yaw_to_set)
    res = e * k
    res = clamp(res)
    auv.set_motor_power(0, -res + speed)
    auv.set_motor_power(1, res + speed)
    return e

def keep_x(set_yaw, stab_yaw, speed=0):  # стабилизация по углу центра контура
    try:
        error = set_yaw - stab_yaw
        output = keep_x.regulator.process(error)
        output = clamp(output, 100, -100)
        auv.set_motor_power(left_motor, output * speed_left + speed * speed_left)
        auv.set_motor_power(right_motor, -output * speed_right + speed * speed_right)
        return error
    except AttributeError:
        keep_x.regulator = PD()
        keep_x.regulator.set_p(0.15)
        keep_x.regulator.set_d(0.25)
    return 0

def stable_x(set_yaw, stab_yaw):  # Проверка функции keep_x()
    counter = 0
    while counter < 10:
        errore = keep_x(set_yaw, stab_yaw)
        if abs(errore) < 3.0:
            counter += 1
        else:
            counter = 0

def keep_area(area, area_to_set):  # Регуляровка по площади
    try:
        error = area - area_to_set
        output = keep_area.regulator.process(error)
        output = clamp(output, 20, -20)
        return error, int(output)
    except AttributeError:
        keep_area.regulator = PD()
        keep_area.regulator.set_p(0.02)
        keep_area.regulator.set_d(0.05)
        return 0
    except ZeroDivisionError:
        time.sleep(0.001)
        return 0

def stab_area(area, area_to_set):  # Проверка функции keep_area()
    counter = 0
    while counter < 10:
        errore, _ = keep_area(area, area_to_set)
        if abs(errore) < 3.0:
            counter += 1
        else:
            counter = 0

def find_contour(frame, low1=None, max1=None, mask6=None):  # поиск контуров
    if low1 is not None and max1 is not None:
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        mask = cv.inRange(hsv, low1, max1)
        cnt, _ = cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    else:
        cnt, _ = cv.findContours(mask6, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    return cnt

def add_mask(img):  # Склеивание* масок (я просто не знаю как сделать в функции find_x_of_moment() аргументы и др.)
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask_r1 = cv.inRange(hsv, low_hsv_red, max_hsv_red)
    mask_r2 = cv.inRange(hsv, low_hsv_red2, max_hsv_red2)
    mask_r = mask_r1 + mask_r2
    mask_g = cv.inRange(hsv, low_hsv_green, max_hsv_green)
    mask_y = cv.inRange(hsv, low_hsv_yellow, max_hsv_yellow)
    # mask_bl = cv.inRange(hsv, low_hsv_red, max_hsv_red)
    mask = mask_r + mask_g + mask_y
    return mask

def find_x_of_moment(img, area1=400):  # Поиск x координаты у Момента Буя, а так же площадь Этого же Буя
    mask = add_mask(img)
    cnt, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    if cnt:
        for c in cnt:
            area = cv.contourArea(c)
            if abs(area) < area1:
                continue
            moments = cv.moments(c)
            cv.drawContours(img, c, -1, (255, 0, 0), 3)
            try:
                x = int(moments["m10"] / moments["m00"])
                y = int(moments["m01"] / moments["m00"])
                return x, area
            except ZeroDivisionError:
                pass

# def go_yaw(yaw, speed = 50):
#     while True:
#         keep_yaw(yaw, speed)

def go_x(speed = 50, xcenter = 320, k = 0.3, w1 = 47):
    while True:
        x, y, w, h = find_shape_blue()
        e = xcenter - x
        res = e * k
        res = clamp(res)
        print(e, xcenter, x, "rect: ", x, y, w, h)
        auv.set_motor_power(1, res + speed)
        auv.set_motor_power(0, -res + speed)
        if w > w1:
            return

def stop_motors():
    time_flag = time.time()
    while time.time() - time_flag < 0.001:
        auv.set_motor_power(1, -10)
        auv.set_motor_power(0, -10)
    auv.set_motor_power(1, 0)
    auv.set_motor_power(0, 0)

#.......1 миссия......

def protect(x, xcenter = 320):
    cv.waitKey(1)
    if x < 160:
        auv.set_motor_power(0, 10)
    else:
        auv.set_motor_power(1, 10)

def find_shape(img, hsv_min, hsv_max, area1=100):  # Поиск Фигур
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    img_bin = cv.inRange(img_hsv, hsv_min, hsv_max)
    mur_view.show(img_bin, 1)
    cnt, _ = cv.findContours(img_bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    list_cont = []
    if cnt:
        for c in cnt:
            area = cv.contourArea(c)
            if abs(area) < area1:
                continue
            moments = cv.moments(c)
            cv.drawContours(img, c, -1, (255, 0, 0), 3)

            try:
                x = int(moments["m10"] / moments["m00"])
                # y = int(moments["m01"] / moments["m00"])

                list_cont.append([cv.contourArea(c), x])
                list_cont.sort(reverse=True)
            except ZeroDivisionError:
                pass
    mur_view.show(img, 0)
    return list_cont

def find_shape_blue(frameg = None):
    if frameg is None:
        frame = show()
    else:
        frame = frameg
    img_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    img_bin = cv.inRange(img_hsv, low_hsv_blue, max_hsv_blue)
    cnt, _ = cv.findContours(img_bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    mur_view.show(img_bin, 1)
    if cnt:
        for c in cnt:
            area = cv.contourArea(c)
            if area > 1:
                x, y, w, h = cv.boundingRect(c)
                cv.drawContours(frame, c, -1, (0, 0, 0), 3)
                return x, y, w, h
    return 0, 0, 0, 0

def find_shape_green(frameg = None):
    if frameg is None:
        frame = show()
    else:
        frame = frameg
    img_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    img_bin = cv.inRange(img_hsv, low_hsv_green, max_hsv_green)
    cnt, _ = cv.findContours(img_bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    mur_view.show(img_bin, 1)
    if cnt:
        for c in cnt:
            area = cv.contourArea(c)
            if area > 1:
                x, y, w, h = cv.boundingRect(c)
                cv.drawContours(frame, c, -1, (0, 0, 0), 3)
                return x, y, w, h
    return 0, 0, 0, 0

def turn(frame, color = "blue", speed = 25, hcenter = 30, k = 0.3):
    frame_c = frame_crop(frame, x1, y1, x2, y2)
    if color == "blue":
        x, y, w, h = find_shape_blue(frame_c)
        e = hcenter - h
        res = e * k
        res = clamp(res)
        print(e, hcenter, h)
        auv.set_motor_power(1, res + speed)
        auv.set_motor_power(0, -res + speed)

def gate(xcenter = 320, k = 0.3):
    frame = show()
    list = find_shape(frame, low_hsv_yellow, max_hsv_yellow)
    if len(list) > 1:
        _, x1 = list[0]
        _, x2 = list[1]
        x = (x2 + x1) // 2
        cv.circle(frame, (x, 240), 5, (0,255,255), -1)
        e = xcenter - x
        res = e * k
        res = clamp(res)
        auv.set_motor_power(1, res)
        auv.set_motor_power(0, -res)
        return e
    else:
        if len(list) == 1:
            _, x1 = list[0]
            protect(x1)
    return 9

def do_gate():
   time_flag = time.time()
   while time.time() - time_flag < 4:
       e = gate()
       if e > 10:
           time_flag = time.time()
   yaw = auv.get_yaw()
   print(yaw)
   go_x(25)
   stop_motors()
   time_flag = time.time()
   while time.time() - time_flag < 3:
        auv.set_motor_power(1, -10)
        auv.set_motor_power(0, 10)
   while True:
       frame = show()
       turn(frame)
       mur_view.show(frame, 0)

#........2 миссия.......

def define_color_nearest_buoy(image):  # Распознование цвета буйка перед роботом (зелёный, красный, жёлтый)
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    cnt_red = find_contour(hsv, low_hsv_red, max_hsv_red)
    cnt_yellow = find_contour(hsv, low_hsv_yellow, max_hsv_yellow)
    cnt_green = find_contour(hsv, low_hsv_green, max_hsv_green)
    color = "NO_COLOR"
    area = 0
    area_red = []
    area_yellow = []
    area_green = []

    if cnt_red:
        for c in cnt_red:
            area_red.append(cv.contourArea(c))
    elif cnt_yellow:
        for c in cnt_yellow:
            area_yellow.append(cv.contourArea(c))
    elif cnt_green:
        for c in cnt_green:
            area_green.append(cv.contourArea(c))

    area_red.sort()  # Сортировка
    area_yellow.sort()
    area_green.sort()

    if area_red > area_green and area_red > area_yellow:
        color = "red"
        area = area_red
    elif area_yellow > area_red and area_yellow > area_green:
        color = "yellow"
        area = area_yellow
    elif area_green > area_red and area_green > area_yellow:
        color = "green"
        area = area_green

    return area, color  # ЦВЕТ ВОЗРАЩАЕТСЯ В ВИДЕ СТРОКИ!!!

def tuch(img):  # Функция для столкновения к буйку, перед этим Стабилизировавшись!
    x_to_set, _ = find_x_of_moment(img)
    _, area = find_x_of_moment(img)
    stable_x(auv.get_yaw(), x_to_set)
    timer = time.time()
    while time.time() - timer < 1:
        auv.set_motor_power(left_motor, 50)
        auv.set_motor_power(right_motor, 50)
    while time.time() - timer < 1:
        auv.set_motor_power(left_motor, -20)
        auv.set_motor_power(right_motor, -20)
    stab_area(area, 400)  # Здесь Я не Уверен Пацаны, Но это типо Стабилизация по площади чтобы
    # Робот отплыл назад (на чуть-чуть) и стабилизировался после того как столкнулся c буём

def go_left(img, timer=time.time()):  # Функция для движения в функции remember_color()
    x_to_set, _ = find_x_of_moment(img)
    stable_x(auv.get_yaw(), x_to_set)
    go_90_left = auv.get_yaw() - 90
    stable_x(auv.get_yaw(), go_90_left)  # Разворот на 90 градусов налево
    while time.time() - timer < 1:
        auv.set_motor_power(left_motor, 50)
        auv.set_motor_power(right_motor, 50)
    go_90_right = auv.get_yaw() + 90
    stable_x(auv.get_yaw(), go_90_right)  # Разворот на 90 градусов направо   (Вообще, это работает?)
    stable_x(auv.get_yaw(), x_to_set)

def go_right(img, timer = time.time()): #Функция для движения Вправо в search_buoys_in_order()
    x_to_set, _ = find_x_of_moment(img)
    stable_x(auv.get_yaw(), x_to_set)
    go_90_right = auv.get_yaw() + 90
    stable_x(auv.get_yaw(), go_90_right)  # Разворот на 90 градусов налево
    while time.time() - timer < 1:
        auv.set_motor_power(left_motor, 50)
        auv.set_motor_power(right_motor, 50)
    go_90_left = auv.get_yaw() - 90
    stable_x(auv.get_yaw(), go_90_left)  # Разворот на 90 градусов направо   (Вообще, это работает?)
    stable_x(auv.get_yaw(), x_to_set)

def remember_color(img):  # Запоминание цветов и их мест (индексов) (с права на лево)
    color = define_color_nearest_buoy(img)
    remembered_color = []
    remembered_color[0] = " "
    while (3):
        if color == "green":
            remembered_color = "green"
        elif color == "yellow":
            remembered_color = "yellow"
        elif color == "red":
            remembered_color = "red"
        go_left(img) # Плывём В лево
        return remembered_color

def search_buoys_in_order(img):  # Поиск Буёв по порядку (Зелёный, Жёлтый, Красный) и Сразу совместил, что он их косаится (я не русский)
    remembered_color = remember_color(img) #Вспоминаем наш список цветов
    index_now = 3 # Мы на 3-ем буе, значит на 3-ем индексе
    index_green = remembered_color.index("green") # Узнаём индекс Зелёного
    index_yellow = remembered_color.index("yellow") # Узнаём индекс Жёлтого
    index_red = remembered_color.index("red") # Узнаём индекс Красного
    index_to_go = index_now - index_green # Узнаём, сколько нужно проплыть буёв до Зелёного
    while(index_to_go):
        go_right(img)
    if index_yellow > index_green: # Если Буй слева, то налево
        index_to_go = index_yellow - index_green
        while (index_to_go):
            go_left(img)
        if index_red > index_yellow:
            index_to_go = index_red - index_yellow
            while (index_to_go):
                go_left(img)
        elif index_red < index_yellow:
            index_to_go = index_yellow - index_red
            while (index_to_go):
                go_right(img)
    elif index_yellow < index_green: # Если Буй справа, то направо
        index_to_go = index_green - index_yellow
        while (index_to_go):
            go_right(img)
        if index_red > index_yellow:
            index_to_go = index_red - index_yellow
            while (index_to_go):
                go_left(img)
        elif index_red < index_yellow:
            index_to_go = index_yellow - index_red
            while (index_to_go):
                go_right(img)

while True:
    img = auv.get_image_front()
    do_gate()
    search_buoys_in_order(img)