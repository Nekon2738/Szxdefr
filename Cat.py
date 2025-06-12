import pygame
import random
import sys
from pygame.locals import *

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Knight Cat: Platform Horror")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PLATFORM_COLOR = (100, 50, 20)

# Физика
GRAVITY = 0.5
JUMP_STRENGTH = -12

# Персонаж: кот
class Cat(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT - 100)
        self.velocity_y = 0
        self.on_ground = False
        self.health = 100
        self.attack_cooldown = 0

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        if keys[K_a]:
            self.rect.x -= 5
        if keys[K_d]:
            self.rect.x += 5

        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y

        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.velocity_y > 0:
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0
                self.on_ground = True

        if keys[K_w] and self.on_ground:
            self.velocity_y = JUMP_STRENGTH

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def attack(self):
        if self.attack_cooldown == 0:
            self.attack_cooldown = 20
            return True
        return False

# Платформы
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Враги
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 3)

    def update(self, platforms):
        self.rect.x += self.direction * self.speed
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.direction *= -1
                break
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction *= -1

# Генератор мира
def generate_world():
    platforms = pygame.sprite.Group()
    platforms.add(Platform(0, HEIGHT - 50, WIDTH, 50))  # Земля
    for _ in range(15):
        width = random.randint(50, 200)
        x = random.randint(0, WIDTH - width)
        y = random.randint(100, HEIGHT - 150)
        platforms.add(Platform(x, y, width, 20))
    return platforms

# Создание объектов
all_sprites = pygame.sprite.Group()
platforms = generate_world()
enemies = pygame.sprite.Group()
player = Cat()
all_sprites.add(player)

# Спавн врагов
for platform in platforms:
    if random.random() < 0.3 and platform.rect.y < HEIGHT - 100:
        enemy = Enemy(platform.rect.centerx, platform.rect.y - 30)
        all_sprites.add(enemy)
        enemies.add(enemy)

# Таймер и очки
start_time = pygame.time.get_ticks()
score = 0
font = pygame.font.SysFont(None, 36)

# Игровой цикл
clock = pygame.time.Clock()
running = True
while running:
    screen.fill(BLACK)
    
    # Таймер (секунды)
    current_time = (pygame.time.get_ticks() - start_time) // 1000
    timer_text = font.render(f"Time: {current_time}s", True, WHITE)
    
    # Очки
    score_text = font.render(f"Score: {score}", True, WHITE)
    
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_SPACE and player.attack():
                for enemy in enemies:
                    if abs(enemy.rect.x - player.rect.x) < 50 and abs(enemy.rect.y - player.rect.y) < 50:
                        enemy.kill()
                        score += 15  # +15 очков за врага

    # Обновление
    player.update(platforms)
    enemies.update(platforms)
    
    # Столкновения с врагами
    hits = pygame.sprite.spritecollide(player, enemies, False)
    for hit in hits:
        player.health -= 0.5
        if player.health <= 0:
            running = False
    
    # Рендеринг
    platforms.draw(screen)
    all_sprites.draw(screen)
    screen.blit(timer_text, (WIDTH - 150, 10))
    screen.blit(score_text, (10, 10))
    screen.blit(font.render(f"Health: {int(player.health)}", True, WHITE), (10, 50))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
