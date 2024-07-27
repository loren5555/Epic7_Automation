import cv2
import numpy as np

from .hsv_filter import HsvFilter


class Vision:

    # region some preprocess functions
    TRACKBAR_WINDOW = "Trackbars"

    def init_control_gui(self):
        cv2.namedWindow(self.TRACKBAR_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.TRACKBAR_WINDOW, 350, 700)

        def nothing(position):
            pass
        # Scale
        cv2.createTrackbar("HMin", self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv2.createTrackbar("SMin", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("VMin", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("HMax", self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv2.createTrackbar("SMax", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("VMax", self.TRACKBAR_WINDOW, 0, 255, nothing)
        # default
        cv2.setTrackbarPos("HMax", self.TRACKBAR_WINDOW, 179)
        cv2.setTrackbarPos("SMax", self.TRACKBAR_WINDOW, 255)
        cv2.setTrackbarPos("VMax", self.TRACKBAR_WINDOW, 255)

        cv2.createTrackbar("SAdd", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("SSub", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("VAdd", self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv2.createTrackbar("VSub", self.TRACKBAR_WINDOW, 0, 255, nothing)

    def get_hsv_filter_from_controls(self):
        hsv_filter = HsvFilter()
        hsv_filter.h_min = cv2.getTrackbarPos("HMin", self.TRACKBAR_WINDOW)
        hsv_filter.h_max = cv2.getTrackbarPos("HMax", self.TRACKBAR_WINDOW)
        hsv_filter.s_min = cv2.getTrackbarPos("SMin", self.TRACKBAR_WINDOW)
        hsv_filter.s_max = cv2.getTrackbarPos("SMax", self.TRACKBAR_WINDOW)
        hsv_filter.v_min = cv2.getTrackbarPos("VMin", self.TRACKBAR_WINDOW)
        hsv_filter.v_max = cv2.getTrackbarPos("VMax", self.TRACKBAR_WINDOW)
        hsv_filter.s_add = cv2.getTrackbarPos("SAdd", self.TRACKBAR_WINDOW)
        hsv_filter.s_sub = cv2.getTrackbarPos("SSub", self.TRACKBAR_WINDOW)
        hsv_filter.v_add = cv2.getTrackbarPos("VAdd", self.TRACKBAR_WINDOW)
        hsv_filter.v_sub = cv2.getTrackbarPos("VSub", self.TRACKBAR_WINDOW)
        return hsv_filter

    def apply_hsv_filter(self, ori_image, hsv_filter=None):
        hsv_img = cv2.cvtColor(ori_image, cv2.COLOR_BGR2HSV)
        if hsv_filter is None:
            hsv_filter = self.get_hsv_filter_from_controls()

        h, s, v = cv2.split(hsv_img)
        s = self.shift_channel(s, hsv_filter.s_add)
        s = self.shift_channel(s, -hsv_filter.s_sub)
        v = self.shift_channel(v, hsv_filter.v_add)
        v = self.shift_channel(v, -hsv_filter.v_sub)
        hsv_img = cv2.merge((h, s, v))

        lower_hsv = np.array([hsv_filter.h_min, hsv_filter.s_min, hsv_filter.v_min])
        upper_hsv = np.array([hsv_filter.h_max, hsv_filter.s_max, hsv_filter.v_max])
        mask = cv2.inRange(hsv_img, lower_hsv, upper_hsv)
        result = cv2.bitwise_and(hsv_img, hsv_img, mask=mask)

        img = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
        return img

    @staticmethod
    def shift_channel(c, amount):
        if amount > 0:
            lim = 255 - amount
            c[c >= lim] = 255
            c[c < lim] += amount
        elif amount < 0:
            amount = - amount
            lim = amount
            c[c <= lim] = 0
            c[c > lim] -= amount
        return c
    # endregion
