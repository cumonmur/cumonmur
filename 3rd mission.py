import pymurapi as mur
import cv2 as cv
import numpy as np
import time

auv = mur.mur_init()

def crop(image, x, y, x1, y1):
    croppedimage = image[y:y1, x:x1]
    cv.rectangle(image, (x, y), (x1, y1), (0, 0, 255), 0)
    return croppedimage

def numbers(image):
    hsvimage = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    #hsv mask init for
    #for red
    lowred = np.array([150, 50, 75])
    highred = np.array([255, 255, 255])
    #for black
    lowblack = np.array([0, 0, 0])
    highblack = np.array([255, 255, 50])
    
    redmask = cv.inRange(hsvimage, lowred, highred)
    #Drawing red contours
    redcontours, _ = cv.findContours(redmask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    
    
    Contours, croppedimage = image.copy(), image.copy()
    redarea, blackarea, relation = 0, 0, 0
    low2area, high2area = 0, 0
    
    if redcontours:
        for redcontour in redcontours:
            x, y, w, h = cv.boundingRect(redcontour)
            x1, y1 = x + w, y + h
            if w < 100:
                auv.set_motor_power(0, 0)
                auv.set_motor_power(1, 0)
                try:                    
                    rect = cv.minAreaRect(redcontour)
                    box = cv.boxPoints(rect)
                    box = np.int0(box)
                    redarea = int(rect[1][0] * rect[1][1])               
                    M = cv.moments(redcontour)
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    #Draw red contours
                    cv.drawContours(Contours, [box], 0, (0, 0, 255), 0)
                    
                    #Draw center of red contour
                    cv.circle(Contours, (int(cx), int(cy)), 1, (0, 255, 0), 0)
                    
                    #Start working with in contour space and numbers
                    croppedimage = crop(image, x, y, x1, y1)
                    
                    hsvcroppedimage = cv.cvtColor(croppedimage, lowblack, highblack)
                    blackmask = cv.inRange(hsvcroppedimage, lowblack, highblack)
                    blackcontours, _ = cv.findContours(blackmask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
                    if blackcontours:
                        for blackcontours in blackcontours:
                            blackX, blackY, blackW, blackH = cv.boundingRect(blackcontour)
                            blackX1, blackY1 = blackX + blackW, blackY + blackH
                            if blackW <  100:
                                try:
                                    blackRect = cv.minAreaRect(blackcontour)
                                    blackBox = cv.boxPoints(blackRect)
                                    blackBox = np.int0(blackBox)
                                    blackarea = int(blackRect[1][0] * blackRect[1][1]) 
                                    cv.drawContours(Contours, [blackBox], 0, (100, 110, 100), 0)
                                except:
                                    pass
                                
#                    if low2area <= relation and relation >= high2area:
#                        return cx
#                        break
                except:
                    pass
                
    cv.imshow("All Contours", Contours)
    cv.imshow("Red Image.bin", redmask)
    cv.imshow("Black Image.bin", blackmask)
    cv.imshow("cropped image", croppedimage)
    print(redarea, '  ', blackarea)
    cv.waitKey(5)
            
    

#def detect_red_objects(image):
#    image_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
#    
#    lower_red = np.array([150, 50, 75])
#    upper_red = np.array([255, 255, 255])
#    mask0 = cv.inRange(image_hsv, lower_red, upper_red)
#    
#    # lower_red = np.array([140, 70, 5])
#    # upper_red = np.array([180, 255, 255])
#    # mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
#    
#    mask = mask0
#    contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
#    drawing = image.copy()
#    
#    if contours:
#        for contour in contours:
#            x, y, w, h = cv.boundingRect(contour)
#            if w < 100:
#                auv.set_motor_power(0, 0)
#                auv.set_motor_power(1, 0)
#                try:
#                    rect = cv.minAreaRect(contour)
#                    box = cv.boxPoints(rect)
#                    box = np.int0(box)
#                    #расчёт площадей и центра
#                    center = (int(rect[0][0]), int(rect[0][1]))
#                    area = int(rect[1][0] * rect[1][1])
#                    square_area = w * h
#                    ((_, _), (w, h), _) = cv.minAreaRect(contour)
#                    cv2.drawContours(drawing, [box], 0, (0, 0, 255), 0)
#
#                    M = cv.moments(contour)
#                    x = int(M['m10'] / M['m00'])
#                    y = int(M['m01'] / M['m00'])
#                    x1 = x + w
#                    y1 = y + h
#                    
#                    
#                    cv.putText(drawing, "red", (cx, cy - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2, cv.LINE_AA)
#                    cv.rectangle(contours, (x, y), (x1, y1), (100, 0, 0), 2) 
#                except:
#                    pass
#    print(len(contours))
#    cv.imshow("red_bin_img", mask)
#    cv.imshow("red_contours", drawing)
#    cv.waitKey(5)



if __name__ == '__main__':
    while True:
        numbers(auv.get_image_front())
        
        
        