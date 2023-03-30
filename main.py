import cv2
import numpy as np
import os
from screenshot import screenshot_window, fetch_window_bounds
from pynput.mouse import Button, Controller
import time
import pyautogui
import threading as th

widthm = 2880 / 2
heightm = 1800 / 2

mouse = Controller()

joy_obj = None

MOVE_UP = 0
MOVE_LEFT = 1
MOVE_RIGHT = 2

movements = []

hided_ui = [
    # cv2.imread('window_ui.png', cv2.IMREAD_UNCHANGED),
    # cv2.imread('attack_btn.png', cv2.IMREAD_UNCHANGED),
    # cv2.imread('cast_btn.png', cv2.IMREAD_UNCHANGED),
    # cv2.imread('tasks_ui.png', cv2.IMREAD_UNCHANGED),
]

needle_marker = cv2.imread('marker.png', cv2.IMREAD_UNCHANGED)
needle_player = cv2.imread('player.png', cv2.IMREAD_UNCHANGED)
needle_joystick = cv2.imread('joystick.png', cv2.IMREAD_UNCHANGED)


def crop_image(image, x, y, w, h):
    return image[y:y+h, x:x+w]


def take_screenshot(flags=None):
    screenshot_window(application_name='Genshin Impact', filename='screen.png')
    return cv2.imread('screen.png', flags)


def find_object(where, who, threshold):
    result = cv2.matchTemplate(where, who, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        needle_w = who.shape[1]
        needle_h = who.shape[0]

        top_left = max_loc

        return top_left[0], top_left[1], needle_w, needle_h

    return None


def fill_object(where, who, threshold, color=(0, 0, 0)):
    result = find_object(where, who, threshold)
    if result is not None:
        x, y, w, h = result
        cv2.rectangle(frame, (x, y), (x + w, y + h), color=color, thickness=-1)

        return x, y, w, h

    return None


def thread_movement():
    # Find window bounds
    bounds = []
    for bounds_ in fetch_window_bounds(application_name='Genshin Impact'):
        bounds.append(bounds_)
    bound = bounds[0]

    # Get window values
    win_x = bound['X']
    win_y = bound['Y']
    win_w = bound['Width']
    win_h = bound['Height']
    center_x = (win_x + (win_w / 2))
    center_y = (win_y + (win_h / 2))

    # Movement processing
    while True:
        if MOVE_UP in movements and joy_obj is not None:
            jy, jx, jw, jh = joy_obj
            jy = jy - (jh / 2)
            jx = jx - (jw / 2)
            pyautogui.moveTo(win_x + (win_w - jx), win_y + (win_h - jy) - 80, duration=0.5)
            mouse.press(Button.left)
            # pyautogui.drag(0, -80, duration=1.0, button='left')
            time.sleep(1)
            mouse.release(Button.left)
        if MOVE_RIGHT in movements:
            pyautogui.moveTo(center_x, center_y)
            pyautogui.drag(distance, 0, duration=0.5, button='left')
            time.sleep(0.5)
        if MOVE_LEFT in movements:
            pyautogui.moveTo(center_x, center_y)
            pyautogui.drag(-distance, 0, duration=0.5, button='left')
            time.sleep(0.5)


# Start moving thread
th.Thread(target=thread_movement).start()

while True:
    frame = take_screenshot(cv2.IMREAD_UNCHANGED)
    w = frame.shape[1]
    h = frame.shape[0]

    # Find joy is not founded
    if joy_obj is None:
        joy_obj = find_object(frame, needle_joystick, 0.4)

    # Fill non-map zones
    cv2.rectangle(frame, (250, 0), (w, h), color=(0, 0, 0), thickness=-1)
    cv2.rectangle(frame, (0, 250+20), (250, h), color=(0, 0, 0), thickness=-1)
    cv2.rectangle(frame, (0, 0), (60, 250+20), color=(0, 0, 0), thickness=-1)
    cv2.rectangle(frame, (60, 0), (250, 70), color=(0, 0, 0), thickness=-1)

    # Hide UI
    for image in hided_ui:
        fill_object(frame, image, 0.5)

    # Draw joy
    if joy_obj is not None:
        x, y, w, h = joy_obj
        cv2.rectangle(frame, (x, y), (x + w, y + h), color=(255, 255, 0), thickness=2)

    # Find and fill marker and player
    marker = fill_object(frame, needle_marker, 0.4, color=(255, 0, 0))
    player = fill_object(frame, needle_player, 0.4, color=(0, 255, 0))

    # Reset all movements tasks
    movements.clear()

    if marker is not None and player is not None: # and joy_obj is not None:
        x1, y1, w1, h1 = marker
        x2, y2, w2, h2 = player

        movements.append(MOVE_UP)

        if x1 > x2:
            distance = x1 - x2
            if distance > 8:
                movements.append(MOVE_RIGHT)
        elif x1 < x2:
            distance = x2 - x1
            if distance > 8:
                movements.append(MOVE_LEFT)

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
