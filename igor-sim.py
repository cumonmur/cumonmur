import pymurapi as mur
import cv2 as cv
import time

auv = mur.mur_init()
low_hsv_yellow = (20, 70, 30)
max_hsv_yellow = (70, 255, 255)

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
    res = e * k
    auv.set_motor_power(1, clamp(res) + speed)
    auv.set_motor_power(0, clamp(-res) - speed)
    time.sleep(0.01)
    return e

def gate(xcenter = 160, k = 0.3):
    frame = auv.get_image_front()
    list = find_shape(frame, low_hsv_yellow, max_hsv_yellow)
    if len(list) > 1:
        _, x1 = list[0]
        _, x2 = list[1]
        x = (x2 + x1) // 2
        cv.circle(frame, (x, 120), 5, (0,255,255), -1)
        e = xcenter - x
        print(e, xcenter, x)
        res = e * k
        auv.set_motor_power(1, clamp(res))
        auv.set_motor_power(0, clamp(-res))
        return e
    cv.waitKey(1)
    return 0


def find_shape(img, hsv_min, hsv_max, area1=100):  # Поиск Фигур
    img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

    img_bin = cv.inRange(img_hsv, hsv_min, hsv_max)
    cv.imshow("bin", img_bin)
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
    cv.imshow("img", img)
    cv.waitKey(1)
    return list_cont

def go_yaw(yaw, speed, sec):
    time_flag = time.time()
    while time.time() - time_flag < sec:
        keep_yaw(yaw,speed)
    
    
print("start")
while True:
    time_flag = time.time()
    while time.time() - time_flag < 2:
        e = gate()
        if e > 10:
            time_flag = time.time()
    yaw = auv.get_yaw()
    print(yaw)
    break
    


