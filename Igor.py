import pymurapi as mur
import cv2 as cv
import time
import numpy as np

auv = mur.mur_init()
cap = cv.VideoCapture(0)
bin = cv.VideoCapture(1)
mur_view = auv.get_videoserver()
low_hsv_yellow = (20, 70, 30)
max_hsv_yellow = (70, 255, 255)

def show():
    ok, frame = cap.read()
    return frame

def clamp(val):
    if val > 100:
        return 100
    if val < -100:
        return -100
    return int(val)


def clamp_angle(angle):
    if angle > 180:
        return angle - 360
    if angle < - 180:
        return angle + 360
    return int(angle)


def keep_yaw(yaw_to_set, speed, k = 1):
    current_yaw = auv.get_yaw()
    e = clamp_angle(current_yaw - yaw_to_set)
    print(e)
    res = e * k
    auv.set_motor_power(1, clamp(res) + speed)
    auv.set_motor_power(0, clamp(-res) - speed)
    time.sleep(0.01)
    return e

def gate():
    list = find_shape(show(), low_hsv_yellow, max_hsv_yellow)
    if len(list) > 2:
        _, x1 = list[0]
        _, x2 = list[1]
        x = (x2 + x1) // 2
        print("ураб2", x)
        return x


def find_shape(img, hsv_min, hsv_max, area1=400):  # Поиск Фигур
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    img_bin = cv.inRange(img_hsv, hsv_min, hsv_max)
    mur_view.show(img_bin, 1)
    cnt, _ = cv.findContours(img_bin, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    list_cont = [0,None]
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

                list_cont.append([cv.contourArea(c), x])
                list_cont.sort(reverse=True)
            except ZeroDivisionError:
                pass
    mur_view.show(img, 0)
    return list_cont

def go_yaw(yaw, speed, sec):
    time_flag = time.time()
    while time.time() - time_flag < sec:
        keep_yaw(yaw,speed)
        cv.waitKey(1)

def go_center_to_x(x, xcenter = 320,sec = 1, k = 1):
    time_flag = time.time()
    while time.time() - time_flag < sec:
        e = xcenter - x
        print(e)
        res = e * k
        auv.set_motor_power(1, clamp(res))
        auv.set_motor_power(0, clamp(-res))
        time.sleep(0.01)
    return auv.get_yaw()

while True:
    list = gate()
    cnt, x = list
    if x is not None:
        yaw = go_center_to_x(x)
        go_yaw(yaw, 50, 5)


