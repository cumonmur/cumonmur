import pymurapi as mur
import cv2
import numpy as np

auv = mur.mur_init()

def detect_red_objects(image):
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    lower_red = np.array([150, 50, 75])
    upper_red = np.array([255, 255, 255])
    mask0 = cv2.inRange(image_hsv, lower_red, upper_red)
    
    # lower_red = np.array([140, 70, 5])
    # upper_red = np.array([180, 255, 255])
    # mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
    
    mask = mask0
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    drawing = image.copy()
    
    if contours:
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < 100:
                auv.set_motor_power(0, 0)
                auv.set_motor_power(1, 0)
                try:
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    #расчёт площадей и центра
                    center = (int(rect[0][0]), int(rect[0][1]))
                    area = int(rect[1][0] * rect[1][1])
                    square_area = w * h
                    ((_, _), (w, h), _) = cv2.minAreaRect(contour)
                    cv2.drawContours(drawing, [box], 0, (0, 0, 255), 0)

                    M = cv2.moments(contour)
                    x = int(M['m10'] / M['m00'])
                    y = int(M['m01'] / M['m00'])
                    x1 = x + w
                    y1 = y + h
                    #cv2.circle(drawing, (int(cx), int(cy)), 1, (0, 255, 0), 2)
                    #cv2.putText(drawing, "red", (cx, cy - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2, cv2.LINE_AA)
                    cv2.rectangle(contours, (x, y), (x1, y1), (100, 0, 0), 2) 
                    inCnt = contours[y:y1, x:x1]
                    hsv2 = cv2.cvtColor(inCnt, cv.Color_BGR2HSV)
                except:
                    pass
         
    cv2.imshow("red_bin_img", mask)
    cv2.imshow("red_contours", drawing)
    cv2.waitKey(5)

def numbers(image):
    print('Loading...')

if __name__ == '__main__':
    while True:
        detect_red_objects(auv.get_image_front())
        
        
