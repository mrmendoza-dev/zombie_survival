import pygame
import random

# Initialize pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Survival")

# Load images
player_image = pygame.image.load('assets/player.png')  # Replace with your own image
zombie_image = pygame.image.load('assets/zombie.png')  # Replace with your own image
background_image = pygame.image.load('assets/background.jpg')  # Replace with your own background image

# Scale down the player and zombie images
player_width, player_height = 60, 80
player_image = pygame.transform.scale(player_image, (player_width, player_height))

zombie_width, zombie_height = 60, 80
zombie_image = pygame.transform.scale(zombie_image, (zombie_width, zombie_height))

# Set up sounds
shoot_sound = pygame.mixer.Sound('assets/shoot.mp3')  # Replace with your own shooting sound
hit_sound = pygame.mixer.Sound('assets/hit.mp3')  # Replace with your own hit sound
shoot_sound.set_volume(0.2)
hit_sound.set_volume(0.2)

# Load and play ambient music
pygame.mixer.music.load('assets/music.wav')  # Replace with your own ambient music file
pygame.mixer.music.set_volume(0.5)  # Set music volume (0.0 to 1.0)
pygame.mixer.music.play(-1, 0.0)  # Play music in loop (-1 means loop indefinitely)

# Colors
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

platforms = [
    pygame.Rect(0, HEIGHT - 100, 200, 10),  # Bottom platform
    pygame.Rect(0, HEIGHT - 200, 200, 10),  # Middle platform
    pygame.Rect(0, HEIGHT - 300, 200, 10),  # Top platform
    pygame.Rect(0, HEIGHT - 400, 200, 10),  # Top platform
    pygame.Rect(0, HEIGHT - 500, 200, 10),  # Top platform

]


# Player setup
player_x, player_y = 1, HEIGHT
player_speed = 4
player_health = 3  # Player's health (3 hits to die)

# Bullet setup
bullet_width, bullet_height = 10, 3
bullets = []

# Zombie setup
zombies = []
zombie_speed = 2
zombie_spawn_rate = 30  # In frames

# Game variables
clock = pygame.time.Clock()
score = 0

# Weapon setup
current_weapon = 'pistol'  # Start with the pistol
max_ammo_pistol = 6
max_ammo_shotgun = 2
ammo_pistol = max_ammo_pistol
ammo_shotgun = max_ammo_shotgun
reload_time = 1000  # 1 second reload time for the pistol
shotgun_reload_time = 3000  # 3 second reload time for the shotgun
last_shot_time = pygame.time.get_ticks()

# Player movement and shooting direction
player_facing_left = False


gravity = 0.5
jump_strength = -10
player_vel_y = 0
is_jumping = False
on_ground = True



# Move player
def move_player(keys):
    global player_x, player_y, player_vel_y, is_jumping, on_ground, player_facing_left

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player_x -= player_speed
        player_facing_left = True
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player_x += player_speed
        player_facing_left = False

    if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
        player_vel_y = jump_strength
        is_jumping = True
        on_ground = False

    player_vel_y += gravity
    player_y += player_vel_y
    on_ground = False

    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

    for platform in platforms:
        if player_rect.colliderect(platform) and player_vel_y >= 0:
            player_y = platform.top - player_height
            player_vel_y = 0
            is_jumping = False
            on_ground = True
            break

    ground_y = HEIGHT - player_height
    if player_y >= ground_y:
        player_y = ground_y
        player_vel_y = 0
        is_jumping = False
        on_ground = True

    player_x = max(0, min(WIDTH - player_width, player_x))

# Bullet movement
def move_bullets():
    global bullets
    for bullet in bullets[:]:
        bullet[0] += 10 * bullet[2]  # Move based on stored direction
        if bullet[0] > WIDTH or bullet[0] < 0:
            bullets.remove(bullet)


# Zombie movement (right to left)
def move_zombies():
    global zombies
    for zombie in zombies:
        zombie[0] -= zombie_speed  # Move the zombie left
        if zombie[0] < -zombie_width:  # Remove zombie if it goes off the left side
            zombies.remove(zombie)

# Check for collisions between bullets and zombies
def check_collisions():
    global zombies, bullets, score
    for zombie in zombies[:]:
        zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_width, zombie_height)
        for bullet in bullets[:]:
            bullet_rect = pygame.Rect(bullet[0], bullet[1], bullet_width, bullet_height)
            if zombie_rect.colliderect(bullet_rect):
                zombies.remove(zombie)
                bullets.remove(bullet)
                score += 1
                hit_sound.play()  # Play hit sound
                break

# Check for collisions between player and zombies (health reduction)
def check_player_collisions():
    global player_health, zombies
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    for zombie in zombies[:]:
        zombie_rect = pygame.Rect(zombie[0], zombie[1], zombie_width, zombie_height)
        if player_rect.colliderect(zombie_rect):
            player_health -= 1  # Reduce health on hit
            zombies.remove(zombie)
            hit_sound.play()  # Play hit sound
            if player_health <= 0:
                return True  # Player is dead
    return False

# Spawn zombies at random vertical positions on the right side of the screen
def spawn_zombies():
    if random.randint(1, zombie_spawn_rate) == 1:
        zombie_y = HEIGHT - zombie_height
        zombies.append([WIDTH, zombie_y])  # Spawn at the far right
    # if random.randint(1, zombie_spawn_rate) == 1:
    #     zombie_y = random.randint(0, HEIGHT - zombie_height)
    #     zombies.append([WIDTH, zombie_y])  # Spawn at the far right

# Draw everything

def draw_game():
    screen.blit(background_image, (0, 0))  # Draw background first
    flipped_player_image = pygame.transform.flip(player_image, player_facing_left, False)
    screen.blit(flipped_player_image, (player_x, player_y))

    # Draw bullets
    for bullet in bullets:
        pygame.draw.rect(screen, YELLOW, pygame.Rect(bullet[0], bullet[1], bullet_width, bullet_height))

    # Draw zombies
    for zombie in zombies:
        screen.blit(zombie_image, (zombie[0], zombie[1]))

    for platform in platforms:
        pygame.draw.rect(screen, (50, 50, 50), platform)  # Gray platforms

    # Font setup
    font = pygame.font.SysFont(None, 36)

    # Draw health bar at top-left
    health_bar_width = 200
    health_bar_height = 20
    pygame.draw.rect(screen, RED, (10, 10, health_bar_width, health_bar_height))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, health_bar_width * (player_health / 3), health_bar_height))

    # Draw score directly underneath health bar
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10 + health_bar_height + 5))

    # Draw ammo
    if current_weapon == 'pistol':
        ammo_text = font.render(f"Pistol Ammo: {ammo_pistol}/{max_ammo_pistol}", True, WHITE)
    else:
        ammo_text = font.render(f"Shotgun Ammo: {ammo_shotgun}/{max_ammo_shotgun}", True, WHITE)
    screen.blit(ammo_text, (WIDTH - 250, 10))

    # Draw weapon name
    weapon_text = font.render(f"Weapon: {current_weapon.capitalize()}", True, WHITE)
    screen.blit(weapon_text, (WIDTH - 250, 40))

    pygame.display.update()


# Main game loop
def main():
    global player_x, player_y, bullets, zombies, score, ammo_pistol, ammo_shotgun, last_shot_time, current_weapon, player_facing_left, player_health
    running = True
    while running:
        clock.tick(60)  # 60 FPS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # Switch to pistol
                    current_weapon = 'pistol'
                elif event.key == pygame.K_2:  # Switch to shotgun
                    current_weapon = 'shotgun'
                elif event.key == pygame.K_SPACE:
                    if current_weapon == 'pistol' and ammo_pistol > 0:
                        bullet_x = player_x + player_width // 2 - bullet_width // 2
                        bullet_y = player_y
                        direction = -1 if player_facing_left else 1
                        bullets.append([bullet_x, bullet_y, direction])
                        shoot_sound.play()  # Play shoot sound
                        ammo_pistol -= 1  # Decrease ammo count
                        last_shot_time = pygame.time.get_ticks()  # Record the time of the shot
                    elif current_weapon == 'shotgun' and ammo_shotgun > 0:
                        for i in range(5):  # Spread the shotgun shot in 5 directions
                            bullet_x = player_x + player_width // 2 - bullet_width // 2 + (i - 2) * 5
                            bullet_y = player_y
                            direction = -1 if player_facing_left else 1
                            bullets.append([bullet_x, bullet_y, direction])

                        shoot_sound.play()  # Play shoot sound
                        ammo_shotgun -= 1  # Decrease ammo count
                        last_shot_time = pygame.time.get_ticks()  # Record the time of the shot

        # Reload if out of ammo and 1 second has passed since the last shot (pistol)
        if current_weapon == 'pistol' and ammo_pistol == 0 and pygame.time.get_ticks() - last_shot_time > reload_time:
            ammo_pistol = max_ammo_pistol  # Reload ammo after the delay

        # Reload if out of ammo and 3 seconds have passed since the last shot (shotgun)
        if current_weapon == 'shotgun' and ammo_shotgun == 0 and pygame.time.get_ticks() - last_shot_time > shotgun_reload_time:
            ammo_shotgun = max_ammo_shotgun  # Reload ammo after the delay

        keys = pygame.key.get_pressed()
        move_player(keys)
        move_bullets()
        move_zombies()
        check_collisions()
        check_player_collisions()
        spawn_zombies()
        draw_game()

        # Check if the player has died
        if player_health <= 0:
            running = False

    pygame.quit()

# Start the game
main()


