import cv2
import mediapipe as mp
import pygame
import random
import time
import math


# --- Initialize MediaPipe for hand tracking ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


# --- Initialize Pygame and window ---
pygame.init()
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand Catch Game")
font = pygame.font.SysFont("Arial", 30)
clock = pygame.time.Clock()


# --- Game Variables ---
balls = []  # List of falling balls
BALL_RADIUS = 15
BALL_SPEED = 8  # Ball falling speed (pixels per frame)
score = 0  # Player's score
target_score = 30  # Score needed to win
game_duration = 30  # Game duration in seconds
start_time = None  # Time when game starts
game_over = False  # Game over state
show_message = "Pinch to start - Catch balls and bring them to the box!"  # Start/restart message
ball_container = []  # Balls collected in the box
held_balls = []  # Balls currently held by the hand
box_timer = 0  # (Unused) Timer for holding hand in box
MAX_HELD_BALLS = 9  # Maximum number of balls that can be held at once


# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLORS = [
    (255,0,0),    # Red
    (0,255,0),    # Green
    (0,0,255),    # Blue
    (255,255,0),  # Yellow
    (255,0,255),  # Magenta
    (0,255,255)   # Cyan
]


# --- Webcam Setup ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    pygame.quit()
    exit()

# MediaPipe Hands model
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)


# --- Helper Functions ---
def convert_cv2_to_pygame(cv_image):
    """Convert OpenCV image (BGR) to pygame surface (RGB)."""
    cv_image = cv2.resize(cv_image, (WIDTH, HEIGHT))
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    return pygame.surfarray.make_surface(cv_image.swapaxes(0, 1))

# --- Helper Functions ---

def spawn_ball():
    """Spawn a new ball at a random x position at the top of the screen."""
    x = random.randint(BALL_RADIUS, WIDTH - BALL_RADIUS)
    return [x, 0, random.choice(COLORS)]


def distance(a, b):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


# --- Main Game Loop ---
running = True
try:
    while running:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read from webcam")
            break

        frame = cv2.flip(frame, 1)  # Mirror image for natural interaction
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_pos = None  # (thumb, index) positions
        pinch = False  # Pinch gesture state

        # Detect hand and pinch gesture
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Thumb tip = 4, Index tip = 8
                h, w, _ = frame.shape
                try:
                    thumb_x = max(0, min(WIDTH-1, int(hand_landmarks.landmark[4].x * WIDTH)))
                    thumb_y = max(0, min(HEIGHT-1, int(hand_landmarks.landmark[4].y * HEIGHT)))
                    index_x = max(0, min(WIDTH-1, int(hand_landmarks.landmark[8].x * WIDTH)))
                    index_y = max(0, min(HEIGHT-1, int(hand_landmarks.landmark[8].y * HEIGHT)))
                    thumb = (thumb_x, thumb_y)
                    index = (index_x, index_y)
                    hand_pos = (thumb, index)
                    if distance(thumb, index) < 40:
                        pinch = True
                except (IndexError, AttributeError):
                    # If hand landmarks are not detected, skip
                    pass

        # Handle window events (quit, escape)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Display camera frame in pygame window
        camera_surface = convert_cv2_to_pygame(frame)
        window.blit(camera_surface, (0, 0))

        # Draw a semi-transparent white overlay for game visuals
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(100)  # Transparency level (0-255)
        overlay.fill((255, 255, 255))  # White overlay
        window.blit(overlay, (0, 0))

        # --- Game State Control ---
        if not start_time:
            # Wait for pinch to start game
            if pinch:
                score = 0
                balls.clear()
                ball_container.clear()
                held_balls.clear()  # Clear held balls on restart
                start_time = time.time()
                game_over = False
                show_message = ""
        else:
            elapsed = time.time() - start_time
            remaining = max(0, game_duration - int(elapsed))

            if not game_over:
                # Spawn balls at random intervals
                if random.random() < 0.12:  # Higher = more balls
                    balls.append(spawn_ball())

                # Occasionally spawn bonus balls
                if random.random() < 0.03:
                    balls.append(spawn_ball())
                    if random.random() < 0.5:
                        balls.append(spawn_ball())

                # Move balls down the screen
                for ball in balls[:]:
                    ball[1] += BALL_SPEED
                    if ball[1] > HEIGHT:
                        balls.remove(ball)

                # Check for catching balls with hand (pinch area)
                if hand_pos and len(hand_pos) == 2:
                    thumb, index = hand_pos
                    if len(thumb) == 2 and len(index) == 2:
                        cx = (thumb[0] + index[0]) // 2
                        cy = (thumb[1] + index[1]) // 2
                        for ball in balls[:]:
                            if len(ball) >= 3 and distance((cx, cy), (ball[0], ball[1])) < 50:
                                # Only catch if under the limit
                                if len(held_balls) < MAX_HELD_BALLS:
                                    balls.remove(ball)
                                    held_balls.append(ball[2])  # Add to held balls

                # Drop balls in collection box (bottom right)
                if hand_pos and len(hand_pos) == 2 and held_balls:
                    thumb, index = hand_pos
                    if len(thumb) == 2 and len(index) == 2:
                        cx = (thumb[0] + index[0]) // 2
                        cy = (thumb[1] + index[1]) // 2
                        # Collection box area (bottom right)
                        box_x, box_y = WIDTH-150, HEIGHT-150
                        box_w, box_h = 120, 120
                        if (box_x < cx < box_x + box_w and box_y < cy < box_y + box_h):
                            # Automatic drop when hand is over box
                            score += len(held_balls)
                            ball_container.extend(held_balls)
                            held_balls.clear()

                # Win/Lose condition
                if score >= target_score:
                    game_over = True
                    show_message = "You Win! Pinch to restart"
                elif remaining <= 0:
                    game_over = True
                    show_message = "Time's up — You Lose. Pinch to restart"

                # Draw hand and held balls
                if hand_pos and len(hand_pos) == 2:
                    thumb, index = hand_pos
                    if len(thumb) == 2 and len(index) == 2:
                        # Draw hand as a circle
                        cx = (thumb[0] + index[0]) // 2
                        cy = (thumb[1] + index[1]) // 2

                        # Draw hand as a larger circle when holding balls
                        if held_balls:
                            # Color changes as hand fills up
                            if len(held_balls) >= MAX_HELD_BALLS:
                                hand_color = (255, 0, 0)  # Red when full
                            elif len(held_balls) >= 6:
                                hand_color = (255, 165, 0)  # Orange when nearly full
                            else:
                                hand_color = (100, 100, 100)  # Gray normally

                            pygame.draw.circle(window, hand_color, (cx, cy), 45, 3)

                            # Draw held balls in a 3x3 grid pattern
                            for i, color in enumerate(held_balls):
                                row = i // 3
                                col = i % 3
                                offset_x = (col - 1) * 20
                                offset_y = (row - 1) * 20
                                pygame.draw.circle(window, color, (cx + offset_x, cy + offset_y), 8)
                        else:
                            # Draw thumb and index as circles, and a line between them
                            pygame.draw.circle(window, BLACK, thumb, 20, 2)
                            pygame.draw.circle(window, BLACK, index, 20, 2)
                            pygame.draw.line(window, BLACK, thumb, index, 2)

                # Draw falling balls
                for ball in balls:
                    pygame.draw.circle(window, ball[2], (ball[0], ball[1]), BALL_RADIUS)

                # Draw score and timer
                score_text = font.render(f"Score: {score}/{target_score}", True, BLACK)
                timer_text = font.render(f"Time: {remaining}", True, BLACK)
                window.blit(score_text, (20, 20))
                window.blit(timer_text, (WIDTH - 150, 20))

                # Draw collection box (bottom right)
                box_x, box_y = WIDTH-150, HEIGHT-150
                pygame.draw.rect(window, (50, 50, 50), (box_x, box_y, 120, 120))  # Dark background
                pygame.draw.rect(window, BLACK, (box_x, box_y, 120, 120), 3)  # Thick border

                # Draw collected balls in box
                for i, color in enumerate(ball_container[-20:]):
                    pygame.draw.circle(window, color, (box_x+10+(i%5)*20, box_y+10+(i//5)*20), 8)
                # Box label
                box_text = font.render("AUTO DROP", True, BLACK)
                window.blit(box_text, (box_x-10, box_y-30))

                # Show held balls count with limit indicator
                if held_balls:
                    if len(held_balls) >= MAX_HELD_BALLS:
                        held_text = font.render(f"Holding: {len(held_balls)}/{MAX_HELD_BALLS} - FULL!", True, (255, 0, 0))
                    else:
                        held_text = font.render(f"Holding: {len(held_balls)}/{MAX_HELD_BALLS}", True, (255, 0, 0))
                    window.blit(held_text, (20, 60))

            else:
                # Show win/lose message and wait for pinch to restart
                message_text = font.render(show_message, True, (200,0,0))
                window.blit(message_text, (WIDTH//2 - message_text.get_width()//2, HEIGHT//2))
                if pinch:
                    start_time = None

        # Show start/restart message if game not started
        if not start_time:
            message_text = font.render(show_message, True, (0,0,200))
            window.blit(message_text, (WIDTH//2 - message_text.get_width()//2, HEIGHT//2))

        pygame.display.flip()
        clock.tick(30)
except KeyboardInterrupt:
    print("Game interrupted by user")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    cap.release()
    pygame.quit()