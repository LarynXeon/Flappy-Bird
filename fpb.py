import pygame
import random
import sys
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption('Flappy Bird')

# Fullscreen mode flag
fullscreen = False

# Sound toggle flag
sound_enabled = True

# Load images and scale them once
def load_images():
    global background_day_img, background_night_img, bird_imgs, pipe_img, pipe_img_flipped, power_up_imgs
    background_day_img = pygame.image.load('background_day.png').convert_alpha()
    background_day_img = pygame.transform.scale(background_day_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    background_night_img = pygame.image.load('background_night.png').convert_alpha()
    background_night_img = pygame.transform.scale(background_night_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    bird_imgs = [pygame.transform.scale(pygame.image.load(f'bird_{i}.png').convert_alpha(), (34, 24)) for i in range(3)]
    
    pipe_img = pygame.image.load('pipe.png').convert_alpha()
    pipe_img = pygame.transform.scale(pipe_img, (70, 500))
    pipe_img_flipped = pygame.transform.flip(pipe_img, False, True)

    power_up_imgs = {
        "double_points": pygame.image.load('power_up_double_points.png').convert_alpha(),
        "invincibility": pygame.image.load('power_up_invincibility.png').convert_alpha()
    }

load_images()

# Load sounds
def load_sounds():
    global flap_sound, score_sound, hit_sound, power_up_sound
    flap_sound = pygame.mixer.Sound('flap.wav')
    score_sound = pygame.mixer.Sound('score.wav')
    hit_sound = pygame.mixer.Sound('hit.wav')
    power_up_sound = pygame.mixer.Sound('power_up.wav')

# Load the sounds
load_sounds()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game constants
GRAVITY = 1000  # Pixels per second^2
FLAP_STRENGTH = -300  # Initial velocity in pixels per second
PIPE_WIDTH = 70
PIPE_HEIGHT = 500
PIPE_GAP = 150
PIPE_MIN_SPACING = 200  # Minimum horizontal distance between pipes
PIPE_SPEED = 200  # Pixels per second
TRANSITION_TIME = 5  # Time taken to transition from day to night (in seconds)

# Fonts
FONT = pygame.font.Font(None, 36)
FPS_FONT = pygame.font.Font(None, 24)

# High score file path
HIGH_SCORE_FILE = "high_score.txt"

# Variables
score = 0
high_score = 0
paused = False
game_over = False
day_to_night = True
current_time = 0
power_up_active = False
power_up_timer = 0

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, 'r') as file:
            return int(file.read())
    return 0

def save_high_score(high_score):
    with open(HIGH_SCORE_FILE, 'w') as file:
        file.write(str(high_score))

class PowerUp:
    def __init__(self, x, y, power_up_type):
        self.image = power_up_imgs[power_up_type]
        self.rect = self.image.get_rect(center=(x, y))
        self.power_up_type = power_up_type

    def apply_power_up(self, bird):
        global power_up_active, power_up_timer, score
        if self.power_up_type == "double_points":
            power_up_active = True
            power_up_timer = 10  # Duration of the power-up in seconds
            if sound_enabled:
                power_up_sound.play()  # Play a sound effect
            score *= 2  # Double the score while the power-up is active
        elif self.power_up_type == "invincibility":
            bird.invincible = True
            power_up_active = True
            power_up_timer = 5  # Duration of the power-up in seconds
            if sound_enabled:
                power_up_sound.play()

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# Bird class
class Bird:
    def __init__(self):
        self.images = bird_imgs
        self.current_image = 0
        self.rect = self.images[self.current_image].get_rect()
        self.rect.center = (100, SCREEN_HEIGHT // 2)
        self.velocity = 0
        self.frame_time = 0
        self.invincible = False

    def flap(self):
        self.velocity = FLAP_STRENGTH
        if sound_enabled:
            flap_sound.play()

    def update(self, dt):
        self.velocity += GRAVITY * dt
        self.rect.y += self.velocity * dt

        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            return True  # Bird has hit the floor, indicate game over
        return False

    def draw(self, screen, dt):
        self.frame_time += dt
        if self.frame_time >= 0.1:  # Change frame every 0.1 seconds
            self.frame_time = 0
            self.current_image = (self.current_image + 1) % len(self.images)
        rotated_image = pygame.transform.rotate(self.images[self.current_image], -self.velocity * 0.05)  # Rotate the bird based on velocity
        new_rect = rotated_image.get_rect(center=self.rect.center)  # Ensure the rotation keeps the rect centered
        screen.blit(rotated_image, new_rect)

# Pipe class
class Pipe:
    def __init__(self, x):
        self.image_top = pipe_img_flipped
        self.image_bottom = pipe_img
        self.rect_top = self.image_top.get_rect(midbottom=(x,random.randint(PIPE_GAP, SCREEN_HEIGHT - PIPE_GAP)))
        self.rect_bottom = self.image_bottom.get_rect(midtop=(x, self.rect_top.bottom + PIPE_GAP))
        self.passed = False

    def update(self, dt):
        self.rect_top.x -= PIPE_SPEED * dt
        self.rect_bottom.x -= PIPE_SPEED * dt

        if self.rect_top.right < 0:
            self.reset_position()

    def reset_position(self):
        self.rect_top.left = SCREEN_WIDTH
        self.rect_top.bottom = random.randint(PIPE_GAP, SCREEN_HEIGHT - PIPE_GAP)
        self.rect_bottom.top = self.rect_top.bottom + PIPE_GAP
        self.passed = False

    def draw(self, screen):
        screen.blit(self.image_top, self.rect_top)
        screen.blit(self.image_bottom, self.rect_bottom)

# Initialize power-ups list
power_ups = []

def spawn_power_up():
    x = random.randint(100, SCREEN_WIDTH - 100)
    y = random.randint(100, SCREEN_HEIGHT - 100)
    power_up_type = random.choice(list(power_up_imgs.keys()))
    power_up = PowerUp(x, y, power_up_type)
    power_ups.append(power_up)

def apply_blur(surface, intensity):
    for _ in range(intensity):
        surface.blit(pygame.transform.smoothscale(surface, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)), (0, 0))
        surface.blit(pygame.transform.smoothscale(surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

def draw_game_over_screen():
    blur_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    apply_blur(blur_surface, 5)
    blur_surface.set_alpha(150)
    SCREEN.blit(blur_surface, (0, 0))

    game_over_text = FONT.render("You Died", True, WHITE)
    text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(game_over_text, text_rect)

    retry_text = FONT.render("Press Enter to Retry", True, WHITE)
    retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    SCREEN.blit(retry_text, retry_rect)

    quit_text = FONT.render("Press ESC to Quit", True, WHITE)
    quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    SCREEN.blit(quit_text, quit_rect)

def draw_pause_menu():
    blur_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    apply_blur(blur_surface, 5)
    blur_surface.set_alpha(150)
    SCREEN.blit(blur_surface, (0, 0))

    pause_text = FONT.render("Game Paused", True, WHITE)
    text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    SCREEN.blit(pause_text, text_rect)

    resume_text = FONT.render("Press P to Resume", True, WHITE)
    resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    SCREEN.blit(resume_text, resume_rect)

def show_loading_screen():
    SCREEN.fill((0, 0, 0))
    loading_text = FONT.render("Loading...", True, WHITE)
    SCREEN.blit(loading_text, (SCREEN_WIDTH // 2 - loading_text.get_width() // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()

def main_menu():
    show_loading_screen()
    running = True
    while running:
        SCREEN.fill((0, 0, 0))
        title_text = FONT.render("Flappy Bird", True, WHITE)
        start_text = FONT.render("Press Enter to Start", True, WHITE)
        settings_text = FONT.render("Press S for Settings", True, WHITE)
        quit_text = FONT.render("Press ESC to Quit", True, WHITE)
        SCREEN.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 2 - 90))
        SCREEN.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        SCREEN.blit(settings_text, (SCREEN_WIDTH // 2 - settings_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        SCREEN.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    main()  # Start the game
                    running = False
                elif event.key == pygame.K_s:
                    settings_menu()
                elif event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()  # Start the game
                running = False

def settings_menu():
    global fullscreen, sound_enabled, SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN

    running = True
    while running:
        SCREEN.fill((0, 0, 0))
        settings_text = FONT.render("Settings", True, WHITE)
        fullscreen_text = FONT.render(f"Fullscreen: {'On' if fullscreen else 'Off'}", True, WHITE)
        sound_text = FONT.render(f"Sound: {'On' if sound_enabled else 'Off'}", True, WHITE)
        resolution_text = FONT.render("Press R to Toggle Resolution", True, WHITE)
        fullscreen_toggle_text = FONT.render("Press F to Toggle Fullscreen", True, WHITE)
        sound_toggle_text = FONT.render("Press M to Toggle Sound", True, WHITE)
        back_text = FONT.render("Press ESC to Go Back", True, WHITE)

        SCREEN.blit(settings_text, (SCREEN_WIDTH // 2 - settings_text.get_width() // 2, SCREEN_HEIGHT // 2 - 150))
        SCREEN.blit(fullscreen_text, (SCREEN_WIDTH // 2 - fullscreen_text.get_width() // 2, SCREEN_HEIGHT // 2 - 90))
        SCREEN.blit(sound_text, (SCREEN_WIDTH // 2 - sound_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        SCREEN.blit(resolution_text, (SCREEN_WIDTH // 2 - resolution_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
        SCREEN.blit(fullscreen_toggle_text, (SCREEN_WIDTH // 2 - fullscreen_toggle_text.get_width() // 2, SCREEN_HEIGHT // 2))
        SCREEN.blit(sound_toggle_text, (SCREEN_WIDTH // 2 - sound_toggle_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        SCREEN.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                elif event.key == pygame.K_m:
                    sound_enabled = not sound_enabled
                elif event.key == pygame.K_r:
                    # Toggle between predefined resolutions
                    if SCREEN_WIDTH == 400 and SCREEN_HEIGHT == 600:
                        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
                    else:
                        SCREEN_WIDTH, SCREEN_HEIGHT = 400, 600
                    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    load_images()  # Reload images to fit the new resolution

def main():
    global score, high_score, paused, game_over, day_to_night, current_time, power_up_active, power_up_timer
    load_images()  # Reload images in case resolution was changed
    load_sounds()  # Load sounds again in case settings were changed

    clock = pygame.time.Clock()
    bird = Bird()
    pipes = [Pipe(SCREEN_WIDTH + i * PIPE_MIN_SPACING) for i in range(3)]
    power_ups.clear()
    
    score = 0
    paused = False
    game_over = False
    day_to_night = True
    current_time = 0
    power_up_active = False
    power_up_timer = 0

    while True:
        dt = clock.tick(120) / 1000  # Delta time in seconds, limit FPS to 60
        fps = int(clock.get_fps())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if game_over:
                    if event.key == pygame.K_RETURN:
                        main()  # Restart the game
                        return  # Exit the current instance of main()
                else:
                    if event.key == pygame.K_SPACE:
                        bird.flap()
                    if event.key == pygame.K_p:
                       paused = not paused
            if event.type == pygame.MOUSEBUTTONDOWN and not paused and not game_over:
                bird.flap()

        if not paused and not game_over:
            if bird.update(dt):  # Update the bird and check if it hits the floor
                game_over = True

            for pipe in pipes:
                pipe.update(dt)

            # Ensure minimum distance between pipes
            for i in range(len(pipes) - 1):
                if pipes[i + 1].rect_top.left - pipes[i].rect_top.left < PIPE_MIN_SPACING:
                    pipes[i + 1].rect_top.left = pipes[i].rect_top.left + PIPE_MIN_SPACING
                    pipes[i + 1].rect_bottom.left = pipes[i + 1].rect_top.left

            # Collision detection
            for pipe in pipes:
                if bird.rect.colliderect(pipe.rect_top) or bird.rect.colliderect(pipe.rect_bottom):
                    if not bird.invincible:
                        game_over = True
                        high_score = max(score, high_score)  # Update high score if the current score is higher

            # Update score
            for pipe in pipes:
                if not pipe.passed and pipe.rect_top.right < bird.rect.left:
                    pipe.passed = True
                    score += 1

            # Update power-up timer
            if power_up_active:
                power_up_timer -= dt
                if power_up_timer <= 0:
                    power_up_active = False
                    bird.invincible = False
                    power_up_timer = 0

            current_time += dt
            if current_time >= TRANSITION_TIME:
                current_time = 0
                day_to_night = not day_to_night  # Toggle between day and night

            # Spawning power-ups
            if random.random() < 0.01:  # Adjust the probability as needed
                spawn_power_up() 

            # Update power-ups
            for power_up in power_ups:
                power_up.update(dt)

            # Check collision with power-ups
            for power_up in power_ups:
                if bird.rect.colliderect(power_up.rect):
                    power_up.apply_power_up(bird)
                    power_ups.remove(power_up)

            # Interpolate between day and night images
            alpha = min(1, current_time / TRANSITION_TIME)
            if day_to_night:
                background_day_alpha = int((1 - alpha) * 255)
                background_night_alpha = int(alpha * 255)
            else:
                background_day_alpha = int(alpha * 255)
                background_night_alpha = int((1 - alpha) * 255)

            SCREEN.blit(background_day_img, (0, 0))
            SCREEN.blit(background_night_img, (0, 0))

            for pipe in pipes:
                pipe.draw(SCREEN)
            bird.draw(SCREEN, dt)  # Draw bird with rotation
            for power_up in power_ups:
                power_up.draw(SCREEN)
            score_text = FONT.render(f"Score: {score}", True, WHITE)
            SCREEN.blit(score_text, (10, 10))
            high_score_text = FPS_FONT.render(f"High Score: {high_score}", True, WHITE)
            SCREEN.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 10))
            fps_text = FPS_FONT.render(f"FPS: {fps}", True, WHITE)
            SCREEN.blit(fps_text, (SCREEN_WIDTH - 70, 10))
            pygame.display.flip()

        if game_over:
            draw_game_over_screen()
        elif paused:
            draw_pause_menu()

if __name__ == "__main__":
    main_menu()
