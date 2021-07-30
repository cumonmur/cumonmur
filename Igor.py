import pymurapi as mur
import cv2 as cv
import math
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
                y = int(moments["m01"] / moments["m00"])

                list_cont.append([cv.contourArea(c), x])
                list_cont.sort(reverse=True)
            except ZeroDivisionError:
                pass
    mur_view.show(img, 0)
    return list_cont

while True:
    gate()