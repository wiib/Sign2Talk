import cv2
import mediapipe as mp
import csv
import os

# --- CONFIGURATION ---
FILE_NAME = 'hand_data.csv'

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

# Initialize CSV if it doesn't exist
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Header: label, then 42 coordinates (21 points * x,y)
        header = ['label']
        for i in range(21):
            header.extend([f'x{i}', f'y{i}'])
        writer.writerow(header)

cap = cv2.VideoCapture(0)

print("--- INSTRUCTIONS ---")
print("1. Make a sign with your hand.")
print("2. Press the LETTER key (a-z) on your keyboard to save that sign.")
print("   Example: Hold 'Peace' sign -> Press 'v'.")
print("3. Collect ~50 samples per letter.")
print("4. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # FIX: Rotate camera
    # frame = cv2.flip(frame, -1)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Extract relative coordinates
            # We subtract the WRIST (landmark 0) from all points to make it 
            # position-invariant (so it works even if your hand is in the corner)
            base_x = hand_landmarks.landmark[0].x
            base_y = hand_landmarks.landmark[0].y
            
            row = []
            for lm in hand_landmarks.landmark:
                row.extend([lm.x - base_x, lm.y - base_y])
            
            # Check for key presses to save data
            key = cv2.waitKey(1)
            if key != -1 and key != 27:
                label = chr(key).upper() # Convert 'a' to 'A'
                
                # Write to CSV
                with open(FILE_NAME, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([label] + row)
                
                cv2.putText(frame, f"Saved: {label}", (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow('Data Recorder', frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
