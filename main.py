import math
import os
import sys
import time

import cv2
import mediapipe as mp
import pygame

# --- Configuration ---
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
CAMERA_INDEX = 0          # 0 = default webcam
STABLE_FRAMES = 5         # frames a gesture must persist before it is accepted
PLAY_COOLDOWN = 1.0       # seconds between two sounds

GESTURE_SOUND_FILES = {
    "LIKE": "like.wav",
    "DISLIKE": "dislike.wav",
    "VICTORY": "victory.wav",
    "MIDDLE_FINGER": "middle_finger.wav",
    "ROCK": "rock.wav",
    "CALL_ME": "call_me.wav",
    "BANG_BANG": "bang_bang.wav",
}

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
HL = mp_hands.HandLandmark

# Landmark indices for the four fingers: (MCP, PIP, TIP)
FINGERS = {
    "index": (HL.INDEX_FINGER_MCP, HL.INDEX_FINGER_PIP, HL.INDEX_FINGER_TIP),
    "middle": (HL.MIDDLE_FINGER_MCP, HL.MIDDLE_FINGER_PIP, HL.MIDDLE_FINGER_TIP),
    "ring": (HL.RING_FINGER_MCP, HL.RING_FINGER_PIP, HL.RING_FINGER_TIP),
    "pinky": (HL.PINKY_MCP, HL.PINKY_PIP, HL.PINKY_TIP),
}

# Finger patterns: (thumb, index, middle, ring, pinky). None = "don't care".
# LIKE / DISLIKE share a pattern and are told apart by the thumb direction.
GESTURE_PATTERNS = [
    ("VICTORY",       (None,  True,  True,  False, False)),
    ("MIDDLE_FINGER", (None,  False, True,  False, False)),
    ("ROCK",          (None,  True,  False, False, True)),
    ("CALL_ME",       (True,  False, False, False, True)),
    ("BANG_BANG",     (True,  True,  False, False, False)),
    ("THUMB",         (True,  False, False, False, False)),
]


# --- Gesture Recognition ---
# Landmarks are normalized to [0, 1] on both axes, so x is rescaled by the
# frame aspect ratio to get distances that are not distorted.
# All checks are distance/direction based, so they work with either hand and
# with the hand rotated (e.g. the sideways "bang bang" pose).

def to_points(landmarks, aspect_ratio):
    return [(lm.x * aspect_ratio, lm.y) for lm in landmarks]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_finger_extended(points, finger):
    """A finger is extended when its tip is farther from the wrist than its PIP joint
    and the finger is roughly straight."""
    mcp, pip, tip = (points[i] for i in FINGERS[finger])
    wrist = points[HL.WRIST]
    return dist(wrist, tip) > dist(wrist, pip) * 1.1 and dist(mcp, tip) > dist(mcp, pip) * 1.5


def angle_between(v1, v2):
    """Angle in degrees between two 2D vectors."""
    norm = math.hypot(*v1) * math.hypot(*v2)
    if norm == 0:
        return 0.0
    cos = (v1[0] * v2[0] + v1[1] * v2[1]) / norm
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def is_thumb_extended(points):
    """The thumb is extended when it is roughly straight and its tip sticks out
    away from the palm (instead of being folded over the fingers)."""
    mcp, ip, tip = points[HL.THUMB_MCP], points[HL.THUMB_IP], points[HL.THUMB_TIP]
    index_mcp, pinky_mcp = points[HL.INDEX_FINGER_MCP], points[HL.PINKY_MCP]
    palm_size = dist(points[HL.WRIST], points[HL.MIDDLE_FINGER_MCP])
    bend = angle_between((ip[0] - mcp[0], ip[1] - mcp[1]), (tip[0] - ip[0], tip[1] - ip[1]))
    return (bend < 40
            and dist(tip, pinky_mcp) > dist(ip, pinky_mcp)
            and dist(tip, index_mcp) > palm_size * 0.3)


def thumb_direction(points):
    """Returns 'UP', 'DOWN' or None depending on where the thumb is pointing."""
    mcp, tip = points[HL.THUMB_MCP], points[HL.THUMB_TIP]
    dx, dy = tip[0] - mcp[0], tip[1] - mcp[1]
    if abs(dy) < abs(dx) * 1.2:  # thumb is mostly horizontal
        return None
    return "UP" if dy < 0 else "DOWN"  # image y grows downwards


def finger_states(points):
    return (
        is_thumb_extended(points),
        is_finger_extended(points, "index"),
        is_finger_extended(points, "middle"),
        is_finger_extended(points, "ring"),
        is_finger_extended(points, "pinky"),
    )


def matches(states, pattern):
    return all(p is None or p == s for s, p in zip(states, pattern))


def detect_gesture(hand_landmarks, aspect_ratio):
    """Detects the gesture made by a single hand. Returns a gesture name or 'NONE'."""
    points = to_points(hand_landmarks.landmark, aspect_ratio)
    states = finger_states(points)

    for name, pattern in GESTURE_PATTERNS:
        if matches(states, pattern):
            if name == "THUMB":
                direction = thumb_direction(points)
                if direction == "UP":
                    return "LIKE"
                if direction == "DOWN":
                    return "DISLIKE"
                return "NONE"
            return name
    return "NONE"


# --- Sounds ---

def load_sounds():
    sounds = {}
    for gesture, filename in GESTURE_SOUND_FILES.items():
        path = os.path.join(SOUND_DIR, filename)
        try:
            sounds[gesture] = pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError) as e:
            print(f"Could not load '{path}': {e}")
    if len(sounds) < len(GESTURE_SOUND_FILES):
        print("Some sounds are missing. Run 'python generate_sounds.py' to (re)create them.")
    return sounds


# --- Main Loop ---

def main():
    pygame.mixer.init()
    sounds = load_sounds()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: cannot access the webcam. Make sure it is connected and not used by another app.")
        sys.exit(1)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    candidate_gesture = "NONE"   # gesture seen in the latest frames
    candidate_count = 0
    stable_gesture = "NONE"      # gesture confirmed for STABLE_FRAMES frames
    last_played_gesture = "NONE"
    last_play_time = 0.0

    print("Gesture Detector started. Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: cannot read a frame from the webcam.")
                break

            frame = cv2.flip(frame, 1)  # mirror effect
            height, width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            current_gesture = "NONE"
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )
                current_gesture = detect_gesture(hand_landmarks, width / height)

            # Debounce: accept a gesture only after it persists for a few frames,
            # so single-frame misdetections don't trigger sounds.
            if current_gesture == candidate_gesture:
                candidate_count += 1
            else:
                candidate_gesture = current_gesture
                candidate_count = 1
            if candidate_count >= STABLE_FRAMES:
                stable_gesture = candidate_gesture

            if stable_gesture == "NONE":
                last_played_gesture = "NONE"
            elif (stable_gesture != last_played_gesture
                  and time.time() - last_play_time > PLAY_COOLDOWN):
                sound = sounds.get(stable_gesture)
                if sound:
                    pygame.mixer.stop()
                    sound.play()
                print(f"Detected gesture: {stable_gesture}")
                last_played_gesture = stable_gesture
                last_play_time = time.time()

            cv2.putText(frame, f"Gesture: {stable_gesture}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, "Press 'q' to quit", (10, height - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow("Gesture Detector", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        hands.close()
        cap.release()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        pygame.quit()


if __name__ == "__main__":
    main()
