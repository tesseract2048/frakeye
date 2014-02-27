import numpy as np
import random
import cv2

MOD_VAMPIRE  = [0,  0,  234, 150]
MOD_HOLLOW   = [0,  0,  0  , 210]
MOD_CATARACT = [255,255,255, 170]
MOD_ALL = [MOD_VAMPIRE, MOD_HOLLOW, MOD_CATARACT]

def getkern(w, h):
    if w >= 65:
        return (7, 7)
    if w >= 40:
        return (4, 4)
    return (3, 3)

def getkern2(w, h):
    if w >= 65:
        return (13, 13)
    if w >= 40:
        return (9, 9)
    return (7, 7)

def getblocksize(w, h):
    if w >= 65:
        return 7
    if w >= 40:
        return 5
    return 3

def blend(x, y):
    alpha = float(y[3]) / 255.0
    beta = 1.0 - alpha
    b = x[0] * beta + y[0] * alpha
    g = x[1] * beta + y[1] * alpha
    r = x[2] * beta + y[2] * alpha
    return [b, g, r]

def verifycontour(c, (px, py)):
    ret = cv2.pointPolygonTest(c, (px, py), False)
    if ret >= 0:
        return True
    return False

def painteye(roi, fullpic, (ex, ey), colormod):
    h, w, depth = roi.shape
    enchanced = cv2.medianBlur(roi, 7)
    window = cv2.min(cv2.boxFilter(enchanced, -1, (5, 9)), cv2.boxFilter(enchanced, -1, (9, 5)))
    single = cv2.split(window)[1]
    px, py = (w/2, h/2)
    gamma = 2
    # this falling back decreases accuracy but though it works
    while gamma > 0:
        dst = cv2.adaptiveThreshold(single, 255, cv2.cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv2.cv.CV_THRESH_BINARY_INV, getblocksize(w, h), gamma)
        kern = np.ones(getkern(w, h), dtype=np.uint8)
        dst = cv2.dilate(dst, kern)
        contours, hierarchy = cv2.findContours(dst, cv2.cv.CV_RETR_EXTERNAL, cv2.cv.CV_CHAIN_APPROX_NONE)
        maxc = None
        for c in contours:
            if not verifycontour(c, (px, py)):
                continue
            if maxc is None or len(c) > len(maxc):
                maxc = c
        if maxc is None:
            gamma -= 1
            continue
        mask = np.zeros((h+22,w+20,4), dtype=np.uint8)
        cv2.fillConvexPoly(mask[10:,10:], maxc, colormod)
        mask = cv2.GaussianBlur(mask, getkern2(w, h), 3.4)
        for x in range(ex-10, ex+w+10):
            for y in range(ey-10, ey+h+10):
                fullpic[y, x] = blend(fullpic[y, x], mask[y-ey+9, x-ex+10])
        break

def removeduplicate(a1, a2):
    arr = []
    for obj1 in a1:
        arr.append(obj1)
    for obj2 in a2:
        skip = False
        for obj1 in a1:
            if intersect(obj1, obj2):
                skip = True
                break
        if not skip:
            arr.append(obj2)
    return arr

def range_overlap(a_min, a_max, b_min, b_max):
    return (a_min <= b_max) and (b_min <= a_max)

def intersect(s1, s2):
    return range_overlap(s1[0], s1[0]+s1[2], s2[0], s2[0]+s2[2]) and range_overlap(s1[1], s1[1]+s1[3], s2[1], s2[1]+s2[3])

face_cascade = cv2.CascadeClassifier('/homebrew-master/Cellar/opencv/2.4.7.1/share/OpenCV/haarcascades/haarcascade_frontalface_alt2.xml')
eyeglass_cascade = cv2.CascadeClassifier('/homebrew-master/Cellar/opencv/2.4.7.1/share/OpenCV/haarcascades/haarcascade_eye_tree_eyeglasses.xml')
eye_cascade = cv2.CascadeClassifier('/homebrew-master/Cellar/opencv/2.4.7.1/share/OpenCV/haarcascades/haarcascade_eye.xml')

def process(img, colormod):
    ht, wt, depth = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray)
    totalcount = 0
    for (x,y,w,h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]
        detect1 = eye_cascade.detectMultiScale(roi_gray)
        detect2 = eyeglass_cascade.detectMultiScale(roi_gray)
        eyes = sorted(removeduplicate(detect1, detect2), cmp=lambda x,y: cmp(x[1],y[1]))
        count = 0
        for (ex,ey,ew,eh) in eyes:
            painteye(roi_color[ey:ey+eh,ex:ex+ew], img, (x+ex, y+ey), colormod)
            count += 1
            if count == 2:
                break
        totalcount += count
    return img, wt, ht, totalcount
