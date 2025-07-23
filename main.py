import cv2
import mediapipe as mp
import pygame
import time
import sys

# --- Pygame Mixer Initialization for Sounds ---
pygame.mixer.init()

# Path to your sounds directory (adjust if necessary)
SOUND_DIR = "suoni/"

# Load sounds
try:
    sound_like = pygame.mixer.Sound(SOUND_DIR + "like.wav")
    sound_dislike = pygame.mixer.Sound(SOUND_DIR + "dislike.wav")
    sound_vittoria = pygame.mixer.Sound(SOUND_DIR + "vittoria.wav")
    sound_dito_medio = pygame.mixer.Sound(SOUND_DIR + "dito_medio.wav")
    sound_rock = pygame.mixer.Sound(SOUND_DIR + "rock.wav")
    sound_chiamami = pygame.mixer.Sound(SOUND_DIR + "chiamami.wav")
    sound_bang_bang = pygame.mixer.Sound(SOUND_DIR + "bang_bang.wav")
except pygame.error as e:
    print(f"Errore nel caricamento dei suoni: {e}")
    print("Assicurati che i file .wav siano nella cartella 'suoni' e che i nomi siano corretti.")
    # Assign None to sounds if loading fails to prevent errors later
    sound_like = sound_dislike = sound_vittoria = sound_dito_medio = None
    sound_rock = sound_chiamami = sound_bang_bang = None

# Store references to sounds in a dictionary for easy access
GESTURE_SOUNDS = {
    "LIKE": sound_like,
    "DISLIKE": sound_dislike,
    "VITTORIA": sound_vittoria,
    "DITO_MEDIO": sound_dito_medio,
    "ROCK": sound_rock,
    "CHIAMAMI": sound_chiamami,
    "BANG_BANG": sound_bang_bang
}

# --- MediaPipe Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,  # We'll focus on one hand for simplicity
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# --- Gesture Recognition Logic ---
# These functions define what constitutes each gesture based on landmark positions
# NO LONGER NEED get_hand_info, passing 'landmarks' directly from MediaPipe

def is_thumb_up(landmarks):
    """Gesture: Thumbs Up (LIKE)"""
    # Thumb tip is above index finger tip and thumb is extended
    # We use .y for vertical position (smaller Y is higher) and .x for horizontal position
    if (landmarks[mp_hands.HandLandmark.THUMB_TIP].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y and
        landmarks[mp_hands.HandLandmark.THUMB_IP].x < landmarks[mp_hands.HandLandmark.THUMB_MCP].x): # Check thumb extension on X-axis (for right hand - adjust for left if needed)
        return True
    return False

def is_thumb_down(landmarks):
    """Gesture: Thumbs Down (DISLIKE)"""
    # Thumb tip is below pinky tip and thumb is extended
    if (landmarks[mp_hands.HandLandmark.THUMB_TIP].y > landmarks[mp_hands.HandLandmark.PINKY_TIP].y and
        landmarks[mp_hands.HandLandmark.THUMB_IP].x < landmarks[mp_hands.HandLandmark.THUMB_MCP].x): # Check thumb extension on X-axis (for right hand)
        return True
    return False

def is_victory_sign(landmarks):
    """Gesture: Victory/Peace (V)"""
    # Index and middle fingers are up, others down
    index_up = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle_up = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_down = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_down = landmarks[mp_hands.HandLandmark.PINKY_TIP].y > landmarks[mp_hands.HandLandmark.PINKY_PIP].y
    # Simple check for thumb: not extended up like a thumbs up
    thumb_crossed_or_bent = landmarks[mp_hands.HandLandmark.THUMB_TIP].x > landmarks[mp_hands.HandLandmark.INDEX_FINGER_MCP].x or \
                            landmarks[mp_hands.HandLandmark.THUMB_TIP].y > landmarks[mp_hands.HandLandmark.THUMB_IP].y

    return index_up and middle_up and ring_down and pinky_down and thumb_crossed_or_bent

def is_middle_finger(landmarks):
    """Gesture: Middle Finger"""
    # Only middle finger is up
    index_down = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle_up = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_down = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_down = landmarks[mp_hands.HandLandmark.PINKY_TIP].y > landmarks[mp_hands.HandLandmark.PINKY_PIP].y
    # Thumb usually tucked away or not pointing up
    thumb_bent = landmarks[mp_hands.HandLandmark.THUMB_TIP].x > landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x or \
                 landmarks[mp_hands.HandLandmark.THUMB_TIP].y > landmarks[mp_hands.HandLandmark.THUMB_IP].y

    return index_down and middle_up and ring_down and pinky_down and thumb_bent

def is_rock_n_roll(landmarks):
    """Gesture: Rock and Roll (🤘)"""
    # Index and pinky up, middle and ring down, thumb might be bent
    index_up = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle_down = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_down = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_up = landmarks[mp_hands.HandLandmark.PINKY_TIP].y < landmarks[mp_hands.HandLandmark.PINKY_PIP].y
    
    # Thumb often tucked under, or slightly out, but not pointing up significantly
    thumb_not_up = landmarks[mp_hands.HandLandmark.THUMB_TIP].y > landmarks[mp_hands.HandLandmark.THUMB_IP].y

    return index_up and middle_down and ring_down and pinky_up and thumb_not_up

def is_call_me(landmarks):
    """Gesture: Call Me (🤙)"""
    # Thumb and pinky up, middle and ring down, index might be bent
    thumb_up = landmarks[mp_hands.HandLandmark.THUMB_TIP].y < landmarks[mp_hands.HandLandmark.THUMB_IP].y
    index_down_or_bent = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    middle_down = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_down = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_up = landmarks[mp_hands.HandLandmark.PINKY_TIP].y < landmarks[mp_hands.HandLandmark.PINKY_PIP].y
    
    return thumb_up and index_down_or_bent and middle_down and ring_down and pinky_up

def is_bang_bang(landmarks):
    """Gesture: Bang Bang (Gun gesture)"""
    # Index and thumb extended, other fingers curled
    index_up = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
    # Thumb extended horizontally (adjust condition based on hand orientation)
    # This might need fine-tuning depending on the angle you hold your hand
    thumb_extended_horizontally = abs(landmarks[mp_hands.HandLandmark.THUMB_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_IP].x) > \
                                  abs(landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].x) * 0.5 # Example, check horizontal extension
    
    # Ensure other fingers are curled
    middle_down = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
    ring_down = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y > landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
    pinky_down = landmarks[mp_hands.HandLandmark.PINKY_TIP].y > landmarks[mp_hands.HandLandmark.PINKY_PIP].y

    return index_up and thumb_extended_horizontally and middle_down and ring_down and pinky_down

def detect_gesture(hand_landmarks_obj): # Removed image_width, image_height as they're not needed for landmark attribute access
    """Detects the specific gesture based on hand landmarks."""
    landmarks = hand_landmarks_obj.landmark # Access the landmark data directly

    if is_thumb_up(landmarks):
        return "LIKE"
    elif is_thumb_down(landmarks):
        return "DISLIKE"
    elif is_victory_sign(landmarks):
        return "VITTORIA"
    elif is_middle_finger(landmarks):
        return "DITO_MEDIO"
    elif is_rock_n_roll(landmarks):
        return "ROCK"
    elif is_call_me(landmarks):
        return "CHIAMAMI"
    elif is_bang_bang(landmarks):
        return "BANG_BANG"
    
    return "NONE"

# --- Main Program Loop ---
cap = cv2.VideoCapture(0) # 0 for default webcam

if not cap.isOpened():
    print("Errore: Impossibile accedere alla webcam. Assicurati che non sia già in uso e che i driver siano installati.")
    sys.exit()

# Variables to manage sound playback frequency
last_played_gesture = "NONE"
last_play_time = time.time()
PLAY_COOLDOWN = 1.0 # seconds, to prevent rapid sound re-triggers

print("Detector di Gesture Avviato. Premi 'q' per uscire.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Errore: Impossibile leggere il frame dalla webcam.")
        break

    # Flip the frame horizontally for a mirror effect
    frame = cv2.flip(frame, 1)
    
    # Convert the BGR image to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    current_gesture = "NONE"

    # Draw hand landmarks and detect gestures
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # Pass the hand_landmarks object directly
            current_gesture = detect_gesture(hand_landmarks)
            break # Process only the first detected hand for simplicity

    # Play sound if a new gesture is detected and cooldown is over
    if current_gesture != "NONE" and current_gesture != last_played_gesture and (time.time() - last_play_time > PLAY_COOLDOWN):
        sound_to_play = GESTURE_SOUNDS.get(current_gesture)
        if sound_to_play:
            if not pygame.mixer.get_busy(): # Only play if mixer is not busy
                sound_to_play.play()
                print(f"Riconosciuta gesture: {current_gesture} - Riproduco {current_gesture.lower()}.wav")
                last_played_gesture = current_gesture
                last_play_time = time.time()
        else:
            print(f"Riconosciuta gesture: {current_gesture} - (Nessun suono associato o errore di caricamento)")
    elif current_gesture == "NONE":
        last_played_gesture = "NONE" # Reset for next detection

    # Display the detected gesture on the frame
    cv2.putText(frame, f"Gesture: {current_gesture}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Gesture Detector', frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
pygame.quit()
sys.exit()