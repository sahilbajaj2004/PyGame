# Hand Catch Game

A webcam-based game using OpenCV, MediaPipe, and Pygame. Catch falling balls with your hand and drop them in the box to score points!

## Controls & How to Play

- **Start/Restart Game:**
  - Pinch your thumb and index finger together in front of the camera.
- **Catch Balls:**
  - Move your hand (thumb and index finger) to catch falling balls. Balls will stick to your hand if you are close enough.
  - You can hold up to 9 balls at once.
- **Drop Balls in Box:**
  - Move your hand (while holding balls) to the bottom-right box labeled "AUTO DROP". Balls will be automatically dropped and scored.
- **Win Condition:**
  - Collect 30 balls before the timer runs out.
- **Lose Condition:**
  - If the timer reaches 0 before you collect 30 balls, you lose.
- **Exit Game:**
  - Press the `ESC` key or close the window.

## Requirements

- Python 3.11
- OpenCV (`opencv-python`)
- MediaPipe
- Pygame

Install requirements with:

```
pip install opencv-python mediapipe pygame
```

## Notes

- Make sure your webcam is connected and accessible.
- The game uses pinch detection (thumb and index finger) for starting/restarting and catching balls.
- The collection box is at the bottom right of the screen.
- The game window is 800x600 pixels.

Enjoy catching balls with your hand!
