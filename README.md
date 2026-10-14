# Gesture Detector

Real-time hand gesture recognition from your webcam, built with [MediaPipe Hands](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) and OpenCV.
Every time a gesture is recognized, the app shows its name on screen and plays a sound.

## Supported gestures

| Gesture | Emoji | How to do it | Sound |
|---|---|---|---|
| `LIKE` | 👍 | Fist with the thumb pointing up | `like.wav` |
| `DISLIKE` | 👎 | Fist with the thumb pointing down | `dislike.wav` |
| `VICTORY` | ✌️ | Index and middle fingers up | `victory.wav` |
| `MIDDLE_FINGER` | 🖕 | Only the middle finger up | `middle_finger.wav` |
| `ROCK` | 🤘 | Index and pinky up | `rock.wav` |
| `CALL_ME` | 🤙 | Thumb and pinky out, other fingers folded | `call_me.wav` |
| `BANG_BANG` | 👉 | Thumb and index out like a pistol, other fingers folded | `bang_bang.wav` |

## How it works

1. Each webcam frame is processed by MediaPipe Hands, which returns 21 landmarks for the detected hand.
2. For each finger, the app decides whether it is **extended** or **folded** by comparing distances
   between landmarks (e.g. a finger is extended when its tip is farther from the wrist than its middle joint).
   Because only distances and angles are used, detection works with **either hand** and with the hand **rotated**.
3. The resulting finger pattern (thumb, index, middle, ring, pinky) is matched against the gestures above.
   For 👍 / 👎 the thumb direction decides which one it is.
4. A gesture must stay stable for a few consecutive frames before it is accepted, which filters out
   flickering misdetections. A short cooldown prevents the same sound from being spammed.

## Requirements

- Python 3.9 – 3.12 (tested with 3.10)
- A webcam

## Installation

```bash
git clone https://github.com/DarkShark02/Gesture_Detector.git
cd Gesture_Detector

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Show your hand to the camera and try the gestures. Press **`q`** to quit.

The sounds are already included in the `sounds/` folder. If you want to regenerate or customize them
(frequency, duration, type), edit and run:

```bash
python generate_sounds.py
```

You can also drop your own `.wav` files into `sounds/`, keeping the same file names.

## Configuration

The main settings are at the top of [`main.py`](main.py):

| Setting | Default | Description |
|---|---|---|
| `CAMERA_INDEX` | `0` | Which webcam to use |
| `STABLE_FRAMES` | `5` | Frames a gesture must persist before it is accepted |
| `PLAY_COOLDOWN` | `1.0` | Minimum seconds between two sounds |

## Project structure

```
Gesture_Detector/
├── main.py              # Webcam loop + gesture recognition
├── generate_sounds.py   # Generates the WAV files in sounds/
├── sounds/              # One sound per gesture
├── requirements.txt
└── LICENSE
```

## Tips

- Use good, even lighting and keep your whole hand inside the frame.
- Hold the gesture for a moment: it is confirmed after a few frames.
- Only one hand is tracked at a time.

## License

Released under the [MIT License](LICENSE) © Flavio Ruggiero.
