import cv2
import numpy as np
import math
import copy

def imageScale(img, factor):
    return cv2.resize(img, (0,0), fx=factor, fy=factor)

def concat_tile(im_list_2d, scale):
    im_list_v = []
    for im_list_h in im_list_2d:
        newim_list_h = []
        for im_ in im_list_h:
            newim_list_h.append(imageScale(im_, scale))
        im_list_v.append(cv2.hconcat(newim_list_h))
    return cv2.vconcat(im_list_v)

def detectMaze(frame, hsvl_param, hsv_param, scale = 0.1, ifdetectBall=False):
    frame_hsv = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)
    frame_hsv_gauss = cv2.GaussianBlur(frame_hsv,(5,5),cv2.BORDER_DEFAULT)
    frame_gray = cv2.cvtColor(frame_hsv_gauss,cv2.COLOR_RGB2GRAY)
    # define range of blue color in HSV
    lower_blue = np.array(hsvl_param)
    upper_blue = np.array(hsv_param)
    mask = cv2.inRange(frame_hsv_gauss, lower_blue, upper_blue)
    res = cv2.bitwise_and(frame, frame, mask= mask)
    # cv2.imshow('hsv', imageScale(frame_hsv,scale))
    if(ifdetectBall):
        detectBall(frame_hsv_gauss, frame_gray)
    cv2.imshow('calibrate_window', concat_tile([[imageScale(frame,scale), cv2.cvtColor(imageScale(frame_gray,scale),cv2.COLOR_GRAY2RGB)]
    , [cv2.cvtColor(imageScale(mask,scale),cv2.COLOR_GRAY2RGB), imageScale(res,scale)]]))

def detectMazeV2(frame, scale = 0.1):
    frame_cpy = copy.deepcopy(frame)
    frame_hsv = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)
    # Gray image op
    frame_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    frame_gray_gauss = cv2.GaussianBlur(frame_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh = cv2.threshold(frame_gray_gauss, 75, 255, cv2.THRESH_BINARY_INV) 
    # Kernel
    ke = 10
    kernel = np.ones((ke, ke), np.uint8)
    # Dilation
    dilation = cv2.dilate(thresh, kernel, iterations=1)
    # Erosion
    erosion = cv2.erode(dilation, kernel, iterations=1)

    # find largest contour
    cnt_img, contours, hierarchy = cv2.findContours(erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cntsSorted = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    rect = cv2.minAreaRect(cntsSorted[0])
    box = cv2.boxPoints(rect)
    box = np.int0(box)

    # bounding contour & generate mask & merge mask
    region_mask_new = np.zeros(erosion.shape, np.uint8)
    cv2.drawContours(frame,[box],0, 255, 3)
    cv2.drawContours(region_mask_new,[box],0, 255, -1)
    merged_mask_new = erosion & region_mask_new

    # apply final mask & see result
    res = cv2.bitwise_and(frame, frame, mask= region_mask_new)

    # Line detection
    # merged_mask_new_cpy = cv2.cvtColor(merged_mask_new,cv2.COLOR_GRAY2RGB)
    # edges = cv2.Canny(merged_mask_new,50,150,apertureSize = 3)
    # minLineLength = 100
    # maxLineGap = 10
    # lines = cv2.HoughLines(edges,1,np.pi/180,100,minLineLength,maxLineGap)
    # for x1,y1,x2,y2 in lines[0]:
    #     cv2.line(merged_mask_new_cpy,(x1,y1),(x2,y2),(0,255,0),2)
    #     cv2.line(frame_cpy,(x1,y1),(x2,y2),(0,255,0),2)
    # for line in lines:
    #     for rho,theta in line:
    #         a = np.cos(theta)
    #         b = np.sin(theta)
    #         x0 = a*rho
    #         y0 = b*rho
    #         x1 = int(x0 + 1000*(-b))
    #         y1 = int(y0 + 1000*(a))
    #         x2 = int(x0 - 1000*(-b))
    #         y2 = int(y0 - 1000*(a))
    #     cv2.line(merged_mask_new_cpy,(x1,y1),(x2,y2),(0,0,255),5)
    #     cv2.line(frame_cpy,(x1,y1),(x2,y2),(0,0,255),5)

    cv2.imshow('calibrate_window', concat_tile(
        [
        [frame,                                     cv2.cvtColor(frame_gray,cv2.COLOR_GRAY2RGB)], 
        [cv2.cvtColor(thresh,cv2.COLOR_GRAY2RGB),   cv2.cvtColor(dilation,cv2.COLOR_GRAY2RGB)],
        [frame,                                     cv2.cvtColor(erosion,cv2.COLOR_GRAY2RGB)],
        [res,                                       cv2.cvtColor(merged_mask_new,cv2.COLOR_GRAY2RGB)],
        # [frame_cpy,                                 merged_mask_new_cpy],
        ], scale))


def detectBall(frame_out, frame_gray):
    # detect circles in the image
    circles = cv2.HoughCircles(frame_gray, cv2.HOUGH_GRADIENT, 1.2, 100)
    # ensure at least some circles were found
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")
    
        # loop over the (x, y) coordinates and radius of the circles
        for (x, y, r) in circles:
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv2.circle(frame_out, (x, y), r, (0, 255, 0), 4)
            cv2.rectangle(frame_out, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
    
        # show the output image
        # cv2.imshow("output", imageScale(np.hstack([frame, output]),scale))

def init_webCam():
    cam = cv2.VideoCapture(1)
    if not cam.isOpened():
        raise IOError("Cannot open webcam")
    return cam

def grab_webCam_feed(cam, mirror=False):
    ret_val, img = cam.read()
    if mirror: 
        img = cv2.flip(img, 1)
    return img

def nothing(x):
    pass

def showUtilities():
    # Create a black image, a window
    img = np.zeros((300,512,3), np.uint8)
    cv2.namedWindow('calibrate_window')

    # create trackbars for color change
    cv2.createTrackbar('Hl','calibrate_window',0,255,nothing)
    cv2.createTrackbar('Sl','calibrate_window',0,255,nothing)
    cv2.createTrackbar('Vl','calibrate_window',0,255,nothing)
    cv2.createTrackbar('H','calibrate_window',0,255,nothing)
    cv2.createTrackbar('S','calibrate_window',0,255,nothing)
    cv2.createTrackbar('V','calibrate_window',0,255,nothing)

def doHSVCalibration(test_frame):
    Hl_val = cv2.getTrackbarPos('Hl','calibrate_window')
    Sl_val = cv2.getTrackbarPos('Sl','calibrate_window')
    Vl_val = cv2.getTrackbarPos('Vl','calibrate_window')
    H_val = cv2.getTrackbarPos('H','calibrate_window')
    S_val = cv2.getTrackbarPos('S','calibrate_window')
    V_val = cv2.getTrackbarPos('V','calibrate_window')
    detectMaze(test_frame, [Hl_val,Sl_val,Vl_val], [H_val,S_val,V_val], ifdetectBall=False)

def main():
    ## MODE SELECTION ##
    MODE = "TESTING_STATIC"

    ##### FOR TESTING RUN_TIME ######
    if "TESTING_RUN" == MODE:
        cam = init_webCam()
        while True:
            frame = grab_webCam_feed(cam, mirror=True)
            maze_lower_bound = [0,0,0]
            maze_upper_bound = [51,115,77]
            # detectMaze(frame, maze_lower_bound, maze_upper_bound, scale = 0.3)
            detectMazeV2(test_frame)
            if cv2.waitKey(1) == 27: 
                break  # esc to quit
        cam.release() # kill camera
   
    ##### FOR TESTING STATIC ######
    elif "TESTING_STATIC" == MODE:
        while True:
            test_frame = cv2.imread('test1.png')
            # obj to detect
            maze_lower_bound = [0,0,0]
            maze_upper_bound = [51,115,77]

            # obj to remove
            blue_mount_lower_bound = [0,160,0]
            blue_mount_bound = [79,255,255]
            
            # detectMaze(test_frame, blue_mount_lower_bound, blue_mount_bound)
            detectMazeV2(test_frame)
            if cv2.waitKey(1) == 27: 
                break  # esc to quit
   
    ##### FOR CALIBRATION ######
    elif "CALIBRATION" == MODE:
        showUtilities()
        while True:
            test_frame = cv2.imread('test1.png')
            doHSVCalibration(test_frame)
            if cv2.waitKey(1) == 27: 
                break  # esc to quit
    
    cv2.destroyAllWindows() # close all windows


if __name__ == '__main__':
    main()




    '''
    ## DEPRECATED CODE ###
def DEPRECATED_detectScope():
    frame_hsv = cv2.cvtColor(frame,cv2.COLOR_RGB2HSV)
    frame_hsv_gauss = cv2.GaussianBlur(frame_hsv,(5,5),cv2.BORDER_DEFAULT)
    # define range of blue color in HSV
    lower_blue = np.array(hsvl_param)
    upper_blue = np.array(hsv_param)
    mask = cv2.inRange(frame_hsv_gauss, lower_blue, upper_blue)
    # res = cv2.bitwise_and(frame, frame, mask= mask)

    # Gray image op
    frame_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    frame_gray_gauss = cv2.GaussianBlur(frame_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh = cv2.threshold(frame_gray_gauss, 75, 255, cv2.THRESH_BINARY_INV) 
    # Kernel
    ke = 10
    kernel = np.ones((ke, ke), np.uint8)
    # Dilation
    dilation = cv2.dilate(thresh, kernel, iterations=1)
    # Erosion
    erosion = cv2.erode(dilation, kernel, iterations=1)
    mask_eroded = cv2.erode(mask, kernel, iterations=2)

    frame_cnt = frame

    --- Extract scope circle based on blue support at the corner of the stewart platform ----
    cnt_img1, contours1, hierarchy1 = cv2.findContours(mask_eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(frame_cnt, contours1, -1, (0, 0, 255), 3)

    cnts1 = contours1
    cnts1Sorted = sorted(cnts1, key=lambda x: cv2.contourArea(x), reverse=True)
    index = 0
    centroid = [0, 0]
    vertices = []
    area_sum = 0
    for cnt in cnts1Sorted:
        x, y, w, h = cv2.boundingRect(cnt)
        vertices.append([x,y])
        centroid[0] = centroid[0]+x
        centroid[1] = centroid[1]+y
        index = index + 1
        area_sum = area_sum + cv2.contourArea(cnt)
        if index >= 3:
            break;
    centroid[0] = centroid[0]/3 + math.sqrt(area_sum)/2
    centroid[1] = centroid[1]/3 + math.sqrt(area_sum)/2
    temp_dx = vertices[0][0] - centroid[0]
    temp_dy = vertices[0][1] - centroid[1]
    radius = math.sqrt(temp_dx*temp_dx + temp_dy*temp_dy + area_sum)
    # print(temp_dx, temp_dy, radius)
    cv2.circle(frame_cnt, (int(centroid[0]), int(centroid[1])), int(radius), (0, 0, 255), 4)

    region_mask = np.zeros(erosion.shape, np.uint8)
    cv2.circle(region_mask, (int(centroid[0]), int(centroid[1])), int(radius), 255, -1)
    merged_mask = erosion & region_mask
'''