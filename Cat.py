import pygame
import random
import sys
import math
from enum import Enum, auto
from typing import List, Dict, Optional, Callable
from pygame.locals import (
    K_a, K_d, K_w, K_SPACE, K_ESCAPE, K_r,
    QUIT, MOUSEBUTTONDOWN
)

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -16
ENEMY_SCORE = 25
PLATFORM_COUNT = 18
MAX_ENEMIES = 10
SWORD_RANGE = 80
SWORD_ANGLE_SPEED = 35
SWORD_DAMAGE = 50  # Изменено для баланса
MIN_VERTICAL_GAP = 140
MIN_HORIZONTAL_GAP = 90
PLAYER_SPEED = 7
ENEMY_SPEED_RANGE = (1.8, 3.0)
INVINCIBILITY_DURATION = 45
ATTACK_COOLDOWN = 20
PLAYER_HEALTH = 100
ENEMY_HEALTH = 50  # Изменено для баланса

# Цвета
BLACK = (0, 0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
GREEN = (70, 255, 70)
BLUE = (70, 70, 255)
PLATFORM_COLOR = (130, 90, 60)
SWORD_COLOR = (230, 230, 180)
BACKGROUND_COLOR = (25, 25, 50)
HEALTH_GREEN = (50, 255, 50)
HEALTH_RED = (255, 50, 50)
BUTTON_COLOR = (70, 70, 150)
BUTTON_HOVER_COLOR = (100, 100, 200)
TITLE_COLOR = (240, 240, 100)
TITLE_SHADOW = (100, 100, 0)
TEXT_COLOR = (220, 220, 220)

class GameState(Enum):
    MAIN_MENU = auto()
    SETTINGS = auto()
    CREDITS = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    PAUSE = auto()

class PlayerState(Enum):
    IDLE = auto()
    WALKING = auto()
    JUMPING = auto()
    ATTACKING = auto()
    HURT = auto()
    DANCING = auto()

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 action: Optional[Callable] = None, font_size: int = 32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', font_size, bold=True)
        self.normal_color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER_COLOR
    
    def draw(self, surface: pygame.Surface) -> None:
        color = self.hover_color if self.is_hovered else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos: tuple) -> bool:
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Callable]:
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return self.action
        return None

class Animation:
    def __init__(self, frames: List[pygame.Surface], speed: float = 0.2, loop: bool = True):
        self.frames = frames
        self.speed = speed
        self.loop = loop
        self.frame_index = 0.0
        self.done = False
    
    def update(self) -> None:
        if not self.done:
            self.frame_index += self.speed
            if self.loop:
                self.frame_index %= len(self.frames)
            elif self.frame_index >= len(self.frames):
                self.frame_index = len(self.frames) - 1
                self.done = True
    
    def get_current_frame(self) -> pygame.Surface:
        return self.frames[int(self.frame_index)]
    
    def reset(self) -> None:
        self.frame_index = 0.0
        self.done = False

class Entity(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity_y = 0.0
        self.on_ground = False
    
    def apply_gravity(self) -> None:
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
    
    def check_platform_collision(self, platforms: pygame.sprite.Group) -> None:
        self.on_ground = False
        for platform in platforms:
            if (self.rect.colliderect(platform.rect) and 
                self.velocity_y > 0 and 
                self.rect.bottom > platform.rect.top + 5):
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0
                self.on_ground = True

class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 70, 80)
        self.animations = self._create_animations()
        self.current_state = PlayerState.IDLE
        self.image = self.animations[self.current_state].get_current_frame()
        self.health = PLAYER_HEALTH
        self.max_health = PLAYER_HEALTH
        self.attack_cooldown = 0
        self.speed = PLAYER_SPEED
        self.facing_right = True
        self.is_attacking = False
        self.invincible = 0
        self.hurt_timer = 0
        self.dance_timer = 0
    
    def _create_animations(self) -> Dict[PlayerState, Animation]:
        return {
            PlayerState.IDLE: self._create_idle_animation(),
            PlayerState.WALKING: self._create_walk_animation(),
            PlayerState.JUMPING: self._create_jump_animation(),
            PlayerState.ATTACKING: self._create_attack_animation(),
            PlayerState.HURT: self._create_hurt_animation(),
            PlayerState.DANCING: self._create_dance_animation()
        }
    
    def _create_idle_animation(self) -> Animation:
        frames = []
        for i in range(4):
            frame = pygame.Surface((70, 80), pygame.SRCALPHA)
            # Тело
            pygame.draw.ellipse(frame, (220, 180, 110), (15, 30, 50, 40))
            # Голова
            pygame.draw.circle(frame, (220, 180, 110), (45, 20), 20)
            # Глаза
            eye_offset = i % 2 * 2
            pygame.draw.circle(frame, (80, 80, 160), (40 + eye_offset, 15), 4)
            pygame.draw.circle(frame, (80, 80, 160), (50 + eye_offset, 15), 4)
            # Уши
            pygame.draw.polygon(frame, (220, 180, 110), 
                              [(45, 0), (55, 15), (35, 15)])
            # Лапы
            pygame.draw.ellipse(frame, (220, 180, 110), (10, 60, 20, 15))
            pygame.draw.ellipse(frame, (220, 180, 110), (50, 60, 20, 15))
            # Хвост
            pygame.draw.ellipse(frame, (220, 180, 110), (5, 40, 15, 10))
            # Меч
            pygame.draw.line(frame, SWORD_COLOR, (40, 40), (60, 20), 5)
            pygame.draw.circle(frame, WHITE, (60, 20), 3)
            
            frames.append(frame)
        return Animation(frames, 0.15)
    
    def _create_walk_animation(self) -> Animation:
        frames = []
        for i in range(6):
            frame = pygame.Surface((70, 80), pygame.SRCALPHA)
            # Тело с анимацией ходьбы
            body_offset = 5 * math.sin(i * math.pi / 3)
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (15 + body_offset, 30, 50, 40))
            # Голова
            head_offset = 3 * math.sin(i * math.pi / 1.5)
            pygame.draw.circle(frame, (220, 180, 110), 
                              (45 + head_offset, 20), 20)
            # Глаза
            pygame.draw.circle(frame, (80, 80, 160), 
                              (40 + head_offset, 15), 4)
            pygame.draw.circle(frame, (80, 80, 160), 
                              (50 + head_offset, 15), 4)
            # Уши
            pygame.draw.polygon(frame, (220, 180, 110), 
                              [(45 + head_offset, 0), 
                               (55 + head_offset, 15), 
                               (35 + head_offset, 15)])
            # Лапы с анимацией ходьбы
            paw_offset = 10 * math.sin(i * math.pi / 3)
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (10, 60 + paw_offset, 20, 15))
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (50, 60 - paw_offset, 20, 15))
            # Хвост
            tail_angle = 15 * math.sin(i * math.pi / 3)
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (5, 40, 15 + tail_angle, 10))
            # Меч
            pygame.draw.line(frame, SWORD_COLOR, 
                           (40 + body_offset, 40), 
                           (60 + body_offset, 20), 5)
            pygame.draw.circle(frame, WHITE, 
                             (60 + body_offset, 20), 3)
            
            frames.append(frame)
        return Animation(frames, 0.2)
    
    def _create_jump_animation(self) -> Animation:
        frame = pygame.Surface((70, 80), pygame.SRCALPHA)
        # Тело в прыжке
        pygame.draw.ellipse(frame, (220, 180, 110), (15, 25, 50, 45))
        # Голова
        pygame.draw.circle(frame, (220, 180, 110), (45, 15), 20)
        # Глаза (узкие)
        pygame.draw.line(frame, (80, 80, 160), (40, 15), (43, 15), 2)
        pygame.draw.line(frame, (80, 80, 160), (47, 15), (50, 15), 2)
        # Уши прижаты
        pygame.draw.polygon(frame, (220, 180, 110), 
                          [(45, 5), (50, 15), (40, 15)])
        # Лапы вытянуты
        pygame.draw.ellipse(frame, (220, 180, 110), (10, 55, 20, 20))
        pygame.draw.ellipse(frame, (220, 180, 110), (50, 55, 20, 20))
        # Хвост поднят
        pygame.draw.ellipse(frame, (220, 180, 110), (5, 30, 20, 15))
        # Меч
        pygame.draw.line(frame, SWORD_COLOR, (40, 35), (60, 15), 5)
        pygame.draw.circle(frame, WHITE, (60, 15), 3)
        
        return Animation([frame], 0.1, loop=False)
    
    def _create_attack_animation(self) -> Animation:
        frames = []
        for i in range(5):
            frame = pygame.Surface((90, 80), pygame.SRCALPHA)
            # Тело в атаке
            body_offset = 10 * (i / 4)
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (15 + body_offset, 30, 50, 40))
            # Голова
            pygame.draw.circle(frame, (220, 180, 110), 
                              (45 + body_offset, 20), 20)
            # Глаза (злые)
            pygame.draw.line(frame, (160, 60, 60), (40, 15), (43, 18), 3)
            pygame.draw.line(frame, (160, 60, 60), (47, 15), (50, 18), 3)
            # Уши
            pygame.draw.polygon(frame, (220, 180, 110), 
                              [(45 + body_offset, 0), 
                               (55 + body_offset, 15), 
                               (35 + body_offset, 15)])
            # Лапы
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (10 + body_offset, 60, 20, 15))
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (50 + body_offset, 60, 20, 15))
            # Меч с анимацией атаки
            sword_angle = 120 + i * 30
            start_pos = (55 + body_offset, 35)
            end_pos = (
                start_pos[0] + 50 * math.cos(math.radians(sword_angle)),
                start_pos[1] + 50 * math.sin(math.radians(sword_angle)))
            pygame.draw.line(frame, SWORD_COLOR, start_pos, end_pos, 6)
            pygame.draw.circle(frame, WHITE, (int(end_pos[0]), int(end_pos[1])), 4)
            
            frames.append(frame)
        return Animation(frames, 0.25, loop=False)
    
    def _create_hurt_animation(self) -> Animation:
        frames = []
        for i in range(4):
            frame = pygame.Surface((70, 80), pygame.SRCALPHA)
            # Тело
            pygame.draw.ellipse(frame, (220, 180, 110), (15, 30, 50, 40))
            # Голова (наклонена)
            head_offset = 5 * math.sin(i * math.pi / 2)
            pygame.draw.ellipse(frame, (220, 180, 110), 
                              (40 + head_offset, 15, 30, 30))
            # Глаза (крестики)
            pygame.draw.line(frame, (160, 60, 60), (40, 15), (45, 20), 3)
            pygame.draw.line(frame, (160, 60, 60), (45, 15), (40, 20), 3)
            pygame.draw.line(frame, (160, 60, 60), (50, 15), (55, 20), 3)
            pygame.draw.line(frame, (160, 60, 60), (55, 15), (50, 20), 3)
            # Уши прижаты
            pygame.draw.polygon(frame, (220, 180, 110), 
                              [(45 + head_offset, 5), 
                               (50 + head_offset, 15), 
                               (40 + head_offset, 15)])
            # Лапы
            pygame.draw.ellipse(frame, (220, 180, 110), (10, 60, 20, 15))
            pygame.draw.ellipse(frame, (220, 180, 110), (50, 60, 20, 15))
            # Меч (выпал)
            if i < 2:
                pygame.draw.line(frame, SWORD_COLOR, (40, 50), (60, 40), 5)
                pygame.draw.circle(frame, WHITE, (60, 40), 3)
            
            frames.append(frame)
        return Animation(frames, 0.15, loop=False)
    
    def _create_dance_animation(self) -> Animation:
        frames = []
        for i in range(8):
            frame = pygame.Surface((90, 100), pygame.SRCALPHA)
            
            # Тело с анимацией танца
            body_offset = 8 * math.sin(i * math.pi / 4)
            pygame.draw.ellipse(frame, (220, 180, 110), (25 + body_offset, 40, 50, 40))
            
            # Голова
            head_offset = 5 * math.sin(i * math.pi / 2)
            pygame.draw.circle(frame, (220, 180, 110), (55 + head_offset, 30), 25)
            
            # Глаза (веселые)
            pygame.draw.arc(frame, (80, 80, 160), (50 + head_offset, 20, 10, 15), 0, math.pi, 3)
            pygame.draw.arc(frame, (80, 80, 160), (65 + head_offset, 20, 10, 15), 0, math.pi, 3)
            
            # Уши
            pygame.draw.polygon(frame, (220, 180, 110), 
                              [(55 + head_offset, 5), (70 + head_offset, 25), (40 + head_offset, 25)])
            
            # Лапы
            paw_offset = 15 * math.sin(i * math.pi / 2)
            pygame.draw.ellipse(frame, (220, 180, 110), (15, 70 + paw_offset, 20, 15))
            pygame.draw.ellipse(frame, (220, 180, 110), (65, 70 - paw_offset, 20, 15))
            
            # Меч за спиной
            sword_angle = 15 * math.sin(i * math.pi / 4)
            start_pos = (30 + body_offset, 50)
            end_pos = (
                start_pos[0] + 40 * math.cos(math.radians(140 + sword_angle)),
                start_pos[1] + 40 * math.sin(math.radians(140 + sword_angle)))
            pygame.draw.line(frame, SWORD_COLOR, start_pos, end_pos, 6)
            pygame.draw.circle(frame, WHITE, (int(end_pos[0]), int(end_pos[1])), 4)
            
            frames.append(frame)
        return Animation(frames, 0.15)
    
    def update_dance(self) -> None:
        self.current_state = PlayerState.DANCING
        self.animations[self.current_state].update()
        self.image = self.animations[self.current_state].get_current_frame()
        
        # Периодически меняем направление
        self.dance_timer += 1
        if self.dance_timer >= 90:
            self.dance_timer = 0
            self.facing_right = not self.facing_right
        
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def update(self, platforms: pygame.sprite.Group) -> None:
        keys = pygame.key.get_pressed()
        
        # Горизонтальное движение
        move_x = (keys[K_d] - keys[K_a]) * self.speed
        if move_x > 0:
            self.facing_right = True
        elif move_x < 0:
            self.facing_right = False
        
        if not self.current_state == PlayerState.HURT:
            self.rect.x += move_x
        
        # Ограничение границ экрана
        self.rect.x = max(20, min(self.rect.x, SCREEN_WIDTH - self.rect.width - 20))
        
        # Гравитация и коллизии
        self.apply_gravity()
        self.check_platform_collision(platforms)

        # Прыжок
        if keys[K_w] and self.on_ground and self.current_state != PlayerState.HURT:
            self.velocity_y = JUMP_STRENGTH
            self.current_state = PlayerState.JUMPING
            self.animations[PlayerState.JUMPING].reset()
        
        # Определение состояния
        if self.current_state == PlayerState.HURT:
            if self.animations[PlayerState.HURT].done:
                self.current_state = PlayerState.IDLE
        elif self.is_attacking:
            self.current_state = PlayerState.ATTACKING
            if self.animations[PlayerState.ATTACKING].done:
                self.is_attacking = False
        elif not self.on_ground:
            self.current_state = PlayerState.JUMPING
        elif abs(move_x) > 0.5:
            self.current_state = PlayerState.WALKING
        else:
            self.current_state = PlayerState.IDLE
        
        # Обновление анимации
        self.animations[self.current_state].update()
        self.image = self.animations[self.current_state].get_current_frame()
        
        # Отражаем изображение если нужно
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        
        # КД атаки и неуязвимости
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        
        # Таймер получения урона
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
    
    def attack(self, enemies: pygame.sprite.Group) -> int:
        if self.attack_cooldown == 0 and not self.is_attacking:
            self.is_attacking = True
            self.attack_cooldown = ATTACK_COOLDOWN
            self.animations[PlayerState.ATTACKING].reset()
            
            # Создаем хитбокс атаки
            attack_rect = pygame.Rect(0, 0, SWORD_RANGE * 1.5, 60)
            if self.facing_right:
                attack_rect.midleft = self.rect.midright
            else:
                attack_rect.midright = self.rect.midleft
                attack_rect.x -= 20
            
            # Проверка попадания по врагам
            hits = 0
            for enemy in enemies:
                if attack_rect.colliderect(enemy.rect):
                    if enemy.take_damage(SWORD_DAMAGE):
                        enemy.kill()
                        hits += 1
            return hits
        return 0
    
    def take_damage(self, amount: int) -> bool:
        if self.invincible == 0 and self.current_state != PlayerState.HURT:
            self.health = max(0, self.health - amount)
            self.invincible = INVINCIBILITY_DURATION
            self.current_state = PlayerState.HURT
            self.animations[PlayerState.HURT].reset()
            self.hurt_timer = 15
            self.velocity_y = -8  # Отбрасывание
            
            # Отталкивание в зависимости от позиции
            if self.rect.centerx < SCREEN_WIDTH // 2:
                self.rect.x = max(20, self.rect.x - 30)
            else:
                self.rect.x = min(SCREEN_WIDTH - self.rect.width - 20, self.rect.x + 30)
            
            return self.health <= 0
        return False
    
    def draw_health(self, surface: pygame.Surface) -> None:
        health_width = 100
        health_height = 12
        outline_rect = pygame.Rect(10, 10, health_width, health_height)
        fill_rect = pygame.Rect(10, 10, health_width * (self.health / self.max_health), health_height)
        
        pygame.draw.rect(surface, HEALTH_RED, outline_rect, 2)
        pygame.draw.rect(surface, HEALTH_GREEN, fill_rect)
        
        # Эффект повреждения
        if self.hurt_timer > 0 and self.hurt_timer % 4 < 2:
            flash_rect = pygame.Rect(10, 10, health_width, health_height)
            pygame.draw.rect(surface, (255, 255, 255, 100), flash_rect)

class Enemy(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, 50, 60)
        self.animation = self._create_animation()
        self.image = self.animation.get_current_frame()
        self.direction = random.choice([-1, 1])
        self.speed = random.uniform(*ENEMY_SPEED_RANGE)
        self.health = ENEMY_HEALTH
        self.max_health = ENEMY_HEALTH
        self.damage = 15
        self.attack_cooldown = 0
    
    def _create_animation(self) -> Animation:
        frames = []
        for i in range(4):
            frame = pygame.Surface((50, 60), pygame.SRCALPHA)
            # Тело
            pygame.draw.ellipse(frame, (200, 70, 70), (5, 15, 40, 35))
            # Голова
            pygame.draw.circle(frame, (200, 70, 70), (35, 15), 15)
            # Глаза
            eye_offset = i % 2
            pygame.draw.circle(frame, (50, 50, 50), (30 + eye_offset, 12), 4)
            pygame.draw.circle(frame, (50, 50, 50), (40 + eye_offset, 12), 4)
            # Рога
            pygame.draw.polygon(frame, (150, 150, 150), [(35, 0), (40, 10), (30, 10)])
            frames.append(frame)
        return Animation(frames, 0.15)
    
    def update(self, platforms: pygame.sprite.Group) -> None:
        self.animation.update()
        self.image = self.animation.get_current_frame()
        
        if self.direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)
        
        # Горизонтальное движение
        self.rect.x += self.direction * self.speed
        
        # Гравитация и коллизии
        self.apply_gravity()
        self.check_platform_collision(platforms)
        
        # Изменение направления
        if self.on_ground:
            at_edge = False
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    if (self.direction > 0 and not platform.rect.collidepoint(self.rect.right+5, self.rect.bottom+5)) or \
                       (self.direction < 0 and not platform.rect.collidepoint(self.rect.left-5, self.rect.bottom+5)):
                        at_edge = True
                        break
            
            if at_edge or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.direction *= -1
        
        # КД атаки
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
    
    def take_damage(self, amount: int) -> bool:
        self.health = max(0, self.health - amount)
        return self.health <= 0
    
    def draw_health(self, surface: pygame.Surface) -> None:
        if self.health < self.max_health:
            health_width = 40
            health_height = 5
            outline_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y - 10, 
                health_width, 
                health_height)
            fill_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y - 10, 
                health_width * (self.health / self.max_health), 
                health_height)
            
            pygame.draw.rect(surface, HEALTH_RED, outline_rect)
            pygame.draw.rect(surface, HEALTH_GREEN, fill_rect)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, width: int, height: int, is_ground: bool = False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if is_ground:
            # Текстура земли
            self.image.fill((90, 60, 40))
            for i in range(0, width, 20):
                pygame.draw.line(self.image, (110, 80, 50), (i, 0), (i, height), 2)
            for i in range(0, height, 20):
                pygame.draw.line(self.image, (110, 80, 50), (0, i), (width, i), 2)
        else:
            # Текстура платформы
            self.image.fill((120, 80, 50))
            pygame.draw.rect(self.image, (140, 100, 60), (0, 0, width, 5))
            pygame.draw.rect(self.image, (100, 60, 30), (0, 5, width, height-5))
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_ground = is_ground

class WorldGenerator:
    @staticmethod
    def generate() -> pygame.sprite.Group:
        platforms = pygame.sprite.Group()
        
        # Создаем землю
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, True)
        platforms.add(ground)
        
        # Параметры генерации
        min_width, max_width = 80, 240
        attempts_per_platform = 50
        
        # Зоны для проверки пересечений (x, y, width)
        occupied_zones = []
        
        for _ in range(PLATFORM_COUNT):
            for _ in range(attempts_per_platform):
                width = random.randint(min_width, max_width)
                x = random.randint(20, SCREEN_WIDTH - width - 20)
                
                # Выбираем Y с учетом минимального вертикального расстояния
                possible_y = []
                for y in range(100, SCREEN_HEIGHT - 200, 10):
                    valid = True
                    
                    # Проверяем расстояние до других платформ
                    for zone in occupied_zones:
                        zone_x, zone_y, zone_width = zone
                        if (abs(y - zone_y) < MIN_VERTICAL_GAP and
                            not (x + width < zone_x or x > zone_x + zone_width + MIN_HORIZONTAL_GAP)):
                            valid = False
                            break
                    
                    if valid:
                        possible_y.append(y)
                
                if not possible_y:
                    continue
                
                y = random.choice(possible_y)
                
                # Проверяем горизонтальное расстояние
                valid_position = True
                for zone in occupied_zones:
                    zone_x, zone_y, zone_width = zone
                    if (abs(y - zone_y) < MIN_VERTICAL_GAP * 1.5 and
                        abs(x + width/2 - (zone_x + zone_width/2)) < (width + zone_width)/2 + MIN_HORIZONTAL_GAP):
                        valid_position = False
                        break
                
                if valid_position:
                    platform = Platform(x, y, width, 20)
                    platforms.add(platform)
                    occupied_zones.append((x, y, width))
                    break
        
        return platforms

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Knight Cat Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 28, bold=True)
        self.title_font = pygame.font.SysFont('Arial', 72, bold=True)
        self.button_font = pygame.font.SysFont('Arial', 32, bold=True)
        
        # Игровые объекты
        self.background = self._create_forest_background()
        self.menu_background = self._create_menu_background()
        self.platforms = WorldGenerator.generate()
        
        # Группы спрайтов
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        
        # Игрок
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.all_sprites.add(self.player)
        
        # Кнопки меню
        self._create_menu_buttons()
        
        # Игровые переменные
        self.state = GameState.MAIN_MENU
        self.start_time = 0
        self.score = 0
        self.running = True
    
    def _create_menu_buttons(self) -> None:
        button_width, button_height = 300, 60
        x_pos = SCREEN_WIDTH // 2 - button_width // 2
        
        self.start_button = Button(
            x_pos, 350, button_width, button_height, 
            "Начать игру", self.start_game
        )
        self.settings_button = Button(
            x_pos, 430, button_width, button_height,
            "Настройки", self.show_settings
        )
        self.credits_button = Button(
            x_pos, 510, button_width, button_height,
            "Авторы", self.show_credits
        )
        self.back_button = Button(
            x_pos, 550, button_width, button_height,
            "Назад", self.show_main_menu
        )
        self.resume_button = Button(
            x_pos, 350, button_width, button_height,
            "Продолжить", self.resume_game
        )
        self.quit_button = Button(
            x_pos, 430, button_width, button_height,
            "Выйти в меню", self.show_main_menu
        )
    
    def _create_forest_background(self) -> pygame.Surface:
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Градиентное небо
        for y in range(SCREEN_HEIGHT):
            color = (
                max(10, min(40, 20 + y//30)),
                max(20, min(60, 30 + y//20)),
                max(30, min(100, 50 + y//10))
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
        
        # Дальние деревья
        for x in range(-100, SCREEN_WIDTH + 300, 250):
            pygame.draw.rect(surface, (80, 50, 30), 
                            (x, SCREEN_HEIGHT - 320, 40, 320))
            pygame.draw.ellipse(surface, (30, 80, 40), 
                              (x - 60, SCREEN_HEIGHT - 450, 160, 180))
        
        # Луна и звёзды
        pygame.draw.circle(surface, (240, 240, 200), (850, 120), 60)
        pygame.draw.circle(surface, (50, 50, 90), (860, 110), 60)
        
        for _ in range(100):
            x, y = random.randint(0, SCREEN_WIDTH), random.randint(0, 300)
            size = random.randint(1, 3)
            brightness = random.randint(200, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)
        
        return surface
    
    def _create_menu_background(self) -> pygame.Surface:
        surface = self.background.copy()
        
        # Затемнение фона
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Заголовок игры
        title_text = self.title_font.render("Knight Cat Adventure", True, TITLE_SHADOW)
        surface.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2 + 5, 100 + 5))
        title_text = self.title_font.render("Knight Cat Adventure", True, TITLE_COLOR)
        surface.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        
        return surface
    
    def spawn_enemies(self) -> None:
        if len(self.enemies) >= MAX_ENEMIES:
            return
            
        for platform in self.platforms:
            if (platform.rect.y < SCREEN_HEIGHT - 150 and 
                random.random() < 0.5 and
                not platform.is_ground):
                
                enemy = Enemy(
                    random.randint(platform.rect.left + 30, platform.rect.right - 30),
                    platform.rect.y - 50
                )
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
    
    def start_game(self) -> None:
        self.state = GameState.PLAYING
        self.start_time = pygame.time.get_ticks()
        self.score = 0
        
        # Сброс игрока
        self.player.health = self.player.max_health
        self.player.rect.center = (200, SCREEN_HEIGHT - 200)
        self.player.current_state = PlayerState.IDLE
        self.player.velocity_y = 0
        self.player.on_ground = False
        
        # Сброс врагов
        for enemy in list(self.enemies):
            enemy.kill()
        self.spawn_enemies()
    
    def resume_game(self) -> None:
        self.state = GameState.PLAYING
    
    def show_settings(self) -> None:
        self.state = GameState.SETTINGS
    
    def show_credits(self) -> None:
        self.state = GameState.CREDITS
    
    def show_main_menu(self) -> None:
        self.state = GameState.MAIN_MENU
        self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
    
    def pause_game(self) -> None:
        self.state = GameState.PAUSE
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            if self.state == GameState.MAIN_MENU:
                if self.start_button.handle_event(event):
                    self.start_game()
                elif self.settings_button.handle_event(event):
                    self.show_settings()
                elif self.credits_button.handle_event(event):
                    self.show_credits()
            
            elif self.state == GameState.PLAYING:
                if event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        hits = self.player.attack(self.enemies)
                        self.score += hits * ENEMY_SCORE
                    elif event.key == K_ESCAPE:
                        self.pause_game()
            
            elif self.state == GameState.PAUSE:
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.resume_game()
                elif self.resume_button.handle_event(event):
                    self.resume_game()
                elif self.quit_button.handle_event(event):
                    self.show_main_menu()
            
            elif self.state in (GameState.SETTINGS, GameState.CREDITS):
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.show_main_menu()
                elif self.back_button.handle_event(event):
                    self.show_main_menu()
            
            elif self.state == GameState.GAME_OVER:
                if event.type == KEYDOWN and event.key == K_r:
                    self.show_main_menu()
    
    def update(self) -> None:
        if self.state != GameState.PLAYING:
            return
        
        self.player.update(self.platforms)
        self.enemies.update(self.platforms)
        
        # Удаление мертвых врагов и спавн новых
        for enemy in list(self.enemies):
            if enemy.health <= 0:
                enemy.kill()
                self.score += ENEMY_SCORE
                # Спавн нового врага с шансом 50%
                if random.random() < 0.5 and len(self.enemies) < MAX_ENEMIES:
                    available_platforms = [p for p in self.platforms 
                                         if not p.is_ground and p.rect.y < SCREEN_HEIGHT - 150]
                    if available_platforms:
                        platform = random.choice(available_platforms)
                        new_enemy = Enemy(
                            random.randint(platform.rect.left + 30, platform.rect.right - 30),
                            platform.rect.y - 50
                        )
                        self.all_sprites.add(new_enemy)
                        self.enemies.add(new_enemy)
        
        # Проверка столкновений с врагами
        for enemy in self.enemies:
            if (pygame.sprite.collide_rect(self.player, enemy) and 
                self.player.invincible == 0 and
                self.player.current_state != PlayerState.HURT and
                enemy.attack_cooldown == 0):
                
                if self.player.take_damage(enemy.damage):
                    enemy.attack_cooldown = 30
                    if self.player.health <= 0:
                        self.state = GameState.GAME_OVER
        
        # Проверка выхода за пределы экрана
        if self.player.rect.top > SCREEN_HEIGHT:
            self.state = GameState.GAME_OVER
        
        # Спавн новых врагов
        if random.random() < 0.01 and len(self.enemies) < MAX_ENEMIES:
            self.spawn_enemies()
    
    def draw_main_menu(self) -> None:
        self.screen.blit(self.menu_background, (0, 0))
        
        # Танцующий кот
        self.player.update_dance()
        self.screen.blit(self.player.image, self.player.rect)
        
        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.check_hover(mouse_pos)
        self.settings_button.check_hover(mouse_pos)
        self.credits_button.check_hover(mouse_pos)
        
        self.start_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        self.credits_button.draw(self.screen)
    
    def draw_settings(self) -> None:
        self.screen.blit(self.menu_background, (0, 0))
        
        title = self.title_font.render("Настройки", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Здесь можно добавить настройки
        text = self.font.render("Настройки звука и управления", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 200))
        
        # Кнопка назад
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(self.screen)
    
    def draw_credits(self) -> None:
        self.screen.blit(self.menu_background, (0, 0))
        
        title = self.title_font.render("Авторы", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Информация об авторах
        author = self.font.render("Игра создана человеком под ником Nekon2738", True, WHITE)
        self.screen.blit(author, (SCREEN_WIDTH//2 - author.get_width()//2, 200))
        
        version = self.font.render("Версия 1.0", True, WHITE)
        self.screen.blit(version, (SCREEN_WIDTH//2 - version.get_width()//2, 250))
        
        # Кнопка назад
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(self.screen)
    
    def draw_pause_menu(self) -> None:
        # Затемнение игрового экрана
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.title_font.render("Пауза", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        self.resume_button.draw(self.screen)
        self.quit_button.draw(self.screen)
    
    def draw_game_over(self) -> None:
        # Затемнение игрового экрана
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        title = self.title_font.render("Игра окончена", True, (255, 80, 80))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        
        score_text = self.font.render(f"Счет: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 300))
        
        time_survived = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = self.font.render(f"Время выживания: {time_survived} сек", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH//2 - time_text.get_width()//2, 350))
        
        restart_text = self.font.render("Нажмите R для возврата в меню", True, (200, 200, 255))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 450))
    
    def draw_game(self) -> None:
        self.screen.blit(self.background, (0, 0))
        
        # Отрисовка всех платформ
        self.platforms.draw(self.screen)
        
        # Отрисовка всех спрайтов (сортировка по Y для правильного отображения)
        for sprite in sorted(self.all_sprites, key=lambda x: x.rect.bottom):
            self.screen.blit(sprite.image, sprite.rect)
            if isinstance(sprite, Enemy):
                sprite.draw_health(self.screen)
        
        # Отрисовка здоровья игрока
        self.player.draw_health(self.screen)
        
        # Отрисовка интерфейса
        current_time = (pygame.time.get_ticks() - self.start_time) // 1000
        score_text = self.font.render(f"Счет: {self.score}", True, WHITE)
        time_text = self.font.render(f"Время: {current_time} сек", True, WHITE)
        
        self.screen.blit(score_text, (20, 40))
        self.screen.blit(time_text, (SCREEN_WIDTH - time_text.get_width() - 20, 40))
    
    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            
            if self.state == GameState.MAIN_MENU:
                self.draw_main_menu()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.CREDITS:
                self.draw_credits()
            elif self.state == GameState.PLAYING:
                self.draw_game()
            elif self.state == GameState.PAUSE:
                self.draw_game()
                self.draw_pause_menu()
            elif self.state == GameState.GAME_OVER:
                self.draw_game()
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
