import cv2
import numpy as np
import math
import copy
from imutils.perspective import four_point_transform
from imutils import contours
import imutils

ENABLE_DEBUG = 1
ENABLE_GRID  = 1

def showImage(caption, image):
    if ENABLE_DEBUG:
        cv2.namedWindow(caption, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(caption, 300,300)
        cv2.imshow(caption, image)

debug_window_dict = {}
def debugWindowAppend(caption, image):
    if ENABLE_DEBUG:
        debug_window_dict[caption] = image

def random_color():
    rgbl=[255,0,0]
    np.random.shuffle(rgbl)
    return tuple(rgbl)

def debugWindowRender(title='Debug_Window', scale = 0.15):
    if ENABLE_DEBUG:
        size = len(debug_window_dict)
        width = int(round(np.sqrt(size)))
        im_list_2d = []
        temp = []
        img_shape = []
        index = 0
        for img_name in debug_window_dict:
            if index == 0:
                img_shape = debug_window_dict[img_name].shape
            else:
                if img_shape < debug_window_dict[img_name].shape:
                    img_shape = debug_window_dict[img_name].shape
            index += 1

        index = 0
        for img_name in debug_window_dict:
            dummy_img = np.full(img_shape, 125, np.uint8)
            if index%width == 0 and index!=0:
                im_list_2d.append(temp)
                temp = []
            last_image = debug_window_dict[img_name]
            centralPIP(dummy_img,last_image)
            temp.append(dummy_img)
            index = index + 1
        # img1.paste(img, box=(x1, y1, x2, y2), mask=img)
        tot_dummies = width - len(temp)
        dummy_img = np.full(img_shape, 125, np.uint8)
        for i in range(0, tot_dummies):
            temp.append(dummy_img)
        im_list_2d.append(temp)
        if (size < 20):
            cv2.imshow(title, concat_tile(im_list_2d, scale))

def centralPIP(bkg_img, frg_img, autoFit=True):
    bw, bh, bc = bkg_img.shape
    fw, fh, fc = frg_img.shape
    scale_factor = 1
    front = frg_img
    if autoFit:
        rw = bw/fw
        rh = bh/fh
        r = min(rw, rh)
        front = cv2.resize(frg_img, dsize=(int(fh*r), int(fw*r)), interpolation=cv2.INTER_CUBIC)
        fw, fh, fc = front.shape
    x = int(bw/2) - int(fw/2)
    y = int(bh/2) - int(fh/2)
    bkg_img[x:x+fw, y:y+fh] = front

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

def detectMark(frame, list_of_bounds, CV2_VERSION, scale = 0.1):
    frame_cpy = copy.deepcopy(frame)
    frame_hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    frame_hsv_gauss = cv2.GaussianBlur(frame_hsv,(5,5),cv2.BORDER_DEFAULT)
    # define range of color in HSV
    list_of_masks = []
    for bnd in list_of_bounds:
        list_of_masks.append({'tag':bnd['tag'],
        'mask': cv2.inRange(frame_hsv_gauss, np.array(bnd['lower']), np.array(bnd['upper']))})

    coords = {}
    for mask in list_of_masks:
        # extract the maze image only
        if CV2_VERSION == '3.4.3':
            _, contours, hierarchy = cv2.findContours(mask['mask'], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, hierarchy = cv2.findContours(mask['mask'], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(contours, key=cv2.contourArea, reverse=True)
        if len(cnts) > 0:
            # compute the center of the contour
            M = cv2.moments(cnts[0])
            area = cv2.contourArea(cnts[0])
            if area > 10000: # for radius of 50
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                clr = random_color()
                # cv2.drawContours(frame_cpy, cnts[0], -1, (0, 255, 0), 2)
                cv2.circle(frame_cpy, (cX, cY), 10, clr, -1)
                cv2.circle(frame_cpy, (cX, cY), int(np.sqrt(area)/2), clr, 8) #area as the circle size for confidence measure
                cv2.putText(frame_cpy, mask['tag'], (cX - 70, cY - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, clr, 5)
            else:
                cX = -1
                cY = -1
                area = -1
            coords[mask['tag']] = [cX, cY, area]

    merged_mask = list_of_masks[0]['mask']
    for mask in list_of_masks:
        merged_mask = merged_mask | mask['mask']
    res = cv2.bitwise_and(frame, frame, mask= merged_mask)

    debugWindowAppend('highlighted', frame_cpy)
    debugWindowAppend('mask', cv2.cvtColor(merged_mask, cv2.COLOR_GRAY2BGR))
    debugWindowAppend('result', res)
    return coords

def extractMaze(frame, cv2_version):
    frame_cpy = copy.deepcopy(frame)
    # Gray image op
    frame_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    frame_gray_gauss = cv2.GaussianBlur(frame_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh = cv2.threshold(frame_gray_gauss, 75, 255, cv2.THRESH_BINARY_INV)

     # extract the maze image only
    if cv2_version == '3.4.3':
        _, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    else:
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(contours, key=cv2.contourArea, reverse=True)
    displayCnt = None

    for c in cnts:
    	# approximate the contour
    	peri = cv2.arcLength(c, True)
    	approx = cv2.approxPolyDP(c, 0.02 * peri, True)

    	if len(approx) == 4:
            displayCnt = approx
            cv2.drawContours(frame, displayCnt, -1, (0,255,0), 3)
            showImage('approx', frame)
            break

    maze_extracted = four_point_transform(frame, displayCnt.reshape(4, 2))
    showImage('maze_extracted', maze_extracted)
    return maze_extracted

def grid_on(frame_grid, pixel_step_size):
    #assign grid to maze
    maze_pixel_height = frame_grid.shape[0]
    maze_pixel_width  = frame_grid.shape[1]
    #this is just for debug purpose -> not necessary to show in operation
    # horizontal line
    for i in range(0, maze_pixel_height, pixel_step_size):
        frame_grid = cv2.line(frame_grid,(0,i),(maze_pixel_width, i),(169,169,169),1)

    #vertical line
    for j in range(0, maze_pixel_width, pixel_step_size):
        frame_grid = cv2.line(frame_grid,(j,0),(j, maze_pixel_height),(169,169,169),1)

    showImage('grid', frame_grid)

def mapMaze_Array(frame, feature_coord):

    maze_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    maze_gray_gauss = cv2.GaussianBlur(maze_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh_maze = cv2.threshold(maze_gray_gauss, 60, 255, cv2.THRESH_BINARY_INV)
    # Kernel
    ke = 60
    kernel = np.ones((ke, ke), np.uint8)
    # Dilation
    dilation_maze = cv2.dilate(thresh_maze, kernel, iterations=1)

    ke = 50
    kernel = np.ones((ke, ke), np.uint8)
    # Erosion
    filtered_maze = cv2.erode(dilation_maze, kernel, iterations=1)

    showImage('filtered', filtered_maze)

    #grid size in pixel

    grid_size = 100

    if ENABLE_GRID:
        grid_image = filtered_maze
        grid_on(grid_image, grid_size)

    filter_maze_pixel_height = filtered_maze.shape[0]
    filter_maze_pixel_width  = filtered_maze.shape[1]

    start_coord = feature_coord['start'][0:2]
    end_coord   = feature_coord['end'][0:2]
    ball_coord  = feature_coord['ball'][0:2]
    map_array = []
    start_array = [ (math.floor( start_coord[0] /grid_size)) , (math.floor(start_coord[1] /grid_size)) ]
    end_array = [(math.floor( end_coord[0] /grid_size)) , (math.floor(end_coord[1] /grid_size))]


    for j in range(0, filter_maze_pixel_width, grid_size):
        map_array_1D = []
        for i in range(0, filter_maze_pixel_height, grid_size):

            roi = filtered_maze[j: j + grid_size , i: i + grid_size]
            if ( np.sum(roi) > (255 * grid_size * grid_size / 6) ):
            #filtered_maze[grid_size, grid_size] = (0, 255,0)
                cv2.rectangle(frame,(i,j),(i+grid_size, j+grid_size),(0,0,255),-1)
                map_array_1D.append(0)
            else:
                map_array_1D.append(1)

        map_array.append(map_array_1D)

    #add start and end color fill
    start_x_pixel = start_array[0] * grid_size
    start_y_pixel = start_array[1] * grid_size
    end_x_pixel = end_array[0] * grid_size
    end_y_pixel = end_array[1] * grid_size

    cv2.rectangle(frame,(start_x_pixel , start_y_pixel),( start_x_pixel + grid_size, start_y_pixel + grid_size),(0,255,255),-1)
    cv2.rectangle(frame,(end_x_pixel , end_y_pixel),( end_x_pixel + grid_size, end_y_pixel + grid_size),(0,255,255),-1)

    showImage('obstacle', frame)

    return map_array, start_array, end_array

def mazeSolver_Phase1(frame, cv2_version):
    #maze extraction from captured image
    maze_frame = extractMaze(frame, cv2_version)

    # marker detection
    list_of_bounds =[   {'tag': 'end', 'lower':[53,27,0], 'upper':[97, 70, 153]},
                        {'tag': 'start','lower':[1,56,0],  'upper':[8, 255, 180]},
                        {'tag': 'ball', 'lower':[0,0,215], 'upper':[255,255,255]},
                    ]
    coord = detectMark(maze_frame, list_of_bounds, cv2_version)
    #print(coord)

    #create 2D binarized array of maze (1-> path, 0->obstacle)
    maze_array = mapMaze_Array(maze_frame, coord)
    print(maze_array)

    debugWindowRender()

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

def showUtilities(properties):
    # Create a black image, a window
    img = np.zeros((300,512,3), np.uint8)
    cv2.namedWindow('calibrate_window')
    # create trackbars for color change
    for prop in properties:
        cv2.createTrackbar(prop,'calibrate_window',0,255,nothing)
    return 'calibrate_window'

def obtainSlides(properties):
    vals = []
    for prop in properties:
        vals.append(cv2.getTrackbarPos(prop,'calibrate_window'))
    return vals

def main():
    CV2_VERSION = cv2.__version__
    print('CV2 VERSION:' ,CV2_VERSION)
    ## MODE SELECTION ##
    # MODE = "CALIBRATION_HSV"
    # MODE = "TESTING_RUN"
    MODE = "TESTING_STATIC"

    ##### FOR TESTING RUN_TIME ######
    if "TESTING_RUN" == MODE:
        cam = init_webCam()
        while True:
            frame = grab_webCam_feed(cam, mirror=True)
            mazeSolver_Phase1(frame, CV2_VERSION)
            debugWindowRender()
            if cv2.waitKey(1) == 27:
                break  # esc to quit
        cam.release() # kill camera

    ##### FOR TESTING STATIC ######
    elif "TESTING_STATIC" == MODE:
        while True:
            test_frame = cv2.imread('test1.png')
            # mirror the image
            test_frame = cv2.flip(test_frame, 0);
            # extract maze bndry
            mazeSolver_Phase1(test_frame, CV2_VERSION)
            if cv2.waitKey(1) == 27:
                break  # esc to quit

    ##### FOR CALIBRATION ######
    elif "CALIBRATION_HSV" == MODE:
        SLIDE_NAME = ['HL', 'SL', 'VL', 'H', 'S', 'V']
        windowName = showUtilities(SLIDE_NAME)
        while True:
            test_frame = cv2.imread('test1.png')
            # extract maze bndry
            maze_frame = extractMaze(test_frame, CV2_VERSION)
            # marker runing
            [Hl_val,Sl_val,Vl_val,H_val,S_val,V_val] = obtainSlides(SLIDE_NAME)
            bound = [ {'tag':'DEBUG', 'lower':[Hl_val,Sl_val,Vl_val], 'upper':[H_val,S_val,V_val]} ]
            coord = detectMark(maze_frame, bound, CV2_VERSION)
            print(coord)
            debugWindowRender(windowName, scale=0.1)
            if cv2.waitKey(1) == 27:
                break  # esc to quit

    cv2.destroyAllWindows() # close all windows


if __name__ == '__main__':
    main()
