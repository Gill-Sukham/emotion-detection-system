import cv2
from deepface import DeepFace
import numpy as np
import datetime
import matplotlib.pyplot as plt

cap = cv2.VideoCapture(0)

PINK = (255, 182, 193)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GREEN = (180, 255, 180)

emotion_history = []

def draw_rounded_rect(img, x, y, w, h, color):
    cv2.rectangle(img, (x, y), (x+w, y+h), color, -1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        if not isinstance(results, list):
            results = [results]

        for face in results:
            region = face.get('region', None)

            if region:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']

                emotions = face['emotion']
                dominant = face['dominant_emotion']

                emotion_history.append(dominant)

                # Keep last 20 values
                if len(emotion_history) > 20:
                    emotion_history.pop(0)

                # Draw face box
                cv2.rectangle(frame, (x, y), (x+w, y+h), PINK, 2)

                draw_rounded_rect(frame, x, y-35, w, 30, BLACK)

                cv2.putText(frame, dominant, (x+5, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)

                # Emotion bars
                bar_x = 20
                bar_y = 60

                for i, (emo, val) in enumerate(emotions.items()):
                    bar_length = int(val * 2)
                    y_pos = bar_y + i * 25

                    cv2.putText(frame, emo, (bar_x, y_pos),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

                    cv2.rectangle(frame,
                                  (bar_x + 80, y_pos - 10),
                                  (bar_x + 80 + bar_length, y_pos),
                                  GREEN, -1)

                    cv2.putText(frame, f"{int(val)}%",
                                (bar_x + 200, y_pos),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

        cv2.putText(frame, "Emotion Mode ON <3",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, PINK, 2)

    except Exception as e:
        print("Error:", e)

    cv2.imshow("Cute Emotion AI", frame)

    key = cv2.waitKey(1)

    # 📸 Screenshot
    if key == ord('s'):
        filename = f"screenshot_{datetime.datetime.now().strftime('%H%M%S')}.png"
        cv2.imwrite(filename, frame)
        print(f"Saved: {filename}")

    # 📈 Show graph
    if key == ord('g'):
     if emotion_history:

        # 🎯 Convert emotions to numbers
        emotion_map = {
            "angry": 0,
            "disgust": 1,
            "fear": 2,
            "sad": 3,
            "neutral": 4,
            "happy": 5,
            "surprise": 6
        }

        numeric_values = [emotion_map[e] for e in emotion_history]

        plt.figure()
        plt.plot(numeric_values, marker='o')

        # 🎨 Clean labels
        plt.yticks(list(emotion_map.values()), list(emotion_map.keys()))

        plt.title("Emotion Trend Over Time")
        plt.xlabel("Time (Frames)")
        plt.ylabel("Emotion")

        plt.grid()
        plt.show()

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()