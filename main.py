import pygame
import random

from os import path
from enum import Enum

WIDTH = 1000
HEIGHT = 800
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

pygame.init()
pygame.display.set_caption('Armored Kill')
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load sound directory and main theme for game
sound_dir = path.join(path.dirname(__file__), 'Sound')
pygame.mixer.init()
# pygame.mixer.music.load(path.join(sound_dir, 'ost.ogg'))
# pygame.mixer.music.play(-1)  # for loop
pygame.mixer.music.set_volume(10)

shoot_sound_player = pygame.mixer.Sound(path.join(sound_dir, 'shoot_player.ogg'))
shoot_sound_enemy = pygame.mixer.Sound(path.join(sound_dir, 'shoot_enemy.ogg'))
explosion_sound_tank = pygame.mixer.Sound(path.join(sound_dir, 'explosion_tank.ogg'))

background_dir = path.join(path.dirname(__file__), 'Textures/Background')
player_dir = path.join(path.dirname(__file__), 'Textures/Player')
enemy_dir = path.join(path.dirname(__file__), 'Textures/Enemy')
background = pygame.image.load(path.join(background_dir, "back.png")).convert()
background_rect = background.get_rect()


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class PlayerTank(pygame.sprite.Sprite):

    def __init__(self, x, y, speed, color, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP,
                 d_down=pygame.K_DOWN):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.color = color
        self.lives = 3
        self.width = 50
        self.direction = Direction.RIGHT
        # self.shoot_delay = 165
        # self.last_shot = pygame.time.get_ticks()

        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}

    def draw(self):
        # tank_c = (self.rect.x + int(self.width / 2), self.rect.y + int(self.width / 2))
        # pygame.draw.rect(screen, self.color,
        #                  (self.rect.x, self.rect.y, self.width, self.width))
        # pygame.draw.circle(screen, self.color, tank_c, int(self.width / 2))

        if self.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()

            # pygame.draw.line(screen, self.color, tank_c,
            #                  (self.rect.x + self.width + int(self.width / 2), self.rect.y + int(self.width / 2)), 4)

        if self.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(player_dir, "player_2.png")).convert()

            # pygame.draw.line(screen, self.color, tank_c, (
            #     self.rect.x - int(self.width / 2), self.rect.y + int(self.width / 2)), 4)

        if self.direction == Direction.UP:
            self.image = pygame.image.load(path.join(player_dir, "player_1.png")).convert()

            # pygame.draw.line(screen, self.color, tank_c, (self.rect.x + int(self.width / 2), self.rect.y - int(self.width / 2)),
            #                  4)

        if self.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(player_dir, "player_4.png")).convert()

            # pygame.draw.line(screen, self.color, tank_c,
            #                  (self.rect.x + int(self.width / 2), self.rect.y + self.width + int(self.width / 2)), 4)

    def change_direction(self, direction):
        self.direction = direction

    def move(self):
        if self.direction == Direction.LEFT:
            self.rect.x -= self.speed
        if self.direction == Direction.RIGHT:
            self.rect.x += self.speed
        if self.direction == Direction.UP:
            self.rect.y -= self.speed
        if self.direction == Direction.DOWN:
            self.rect.y += self.speed
        self.draw()

        # Borders
        if self.rect.x > WIDTH:
            self.rect.x = WIDTH - 975
        if self.rect.x < 0:
            self.rect.x = WIDTH - 25
        if self.rect.y > HEIGHT:
            self.rect.y = HEIGHT - 775
        if self.rect.y < 0:
            self.rect.y = HEIGHT - 25


class EnemyTank(pygame.sprite.Sprite):

    def __init__(self, x, y, speed, color, d_right=pygame.K_d, d_left=pygame.K_a, d_up=pygame.K_w,
                 d_down=pygame.K_s):
        pygame.sprite.Sprite.__init__(self)
        # Initialize player attributes, coordinates
        self.image = pygame.image.load(path.join(enemy_dir, "player_1.png")).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.color = color
        self.width = 40
        self.lives = 3
        self.direction = Direction.LEFT
        self.last_shot = pygame.time.get_ticks()
        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}

    def change_direction(self, direction):
        self.direction = direction

    def draw(self):
        # tank_c = (self.x + int(self.width / 2), self.y + int(self.width / 2))
        # pygame.draw.rect(screen, self.color,
        #                  (self.x, self.y, self.width, self.width))
        # pygame.draw.circle(screen, self.color, tank_c, int(self.width / 2))

        if self.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(enemy_dir, "player_4.png")).convert()
            # pygame.draw.line(screen, self.color, tank_c,
            #                  (self.x + self.width + int(self.width / 2), self.y + int(self.width / 2)), 4)

        if self.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(enemy_dir, "player_2.png")).convert()
            # pygame.draw.line(screen, self.color, tank_c, (
            #     self.x - int(self.width / 2), self.y + int(self.width / 2)), 4)

        if self.direction == Direction.UP:
            self.image = pygame.image.load(path.join(enemy_dir, "player_1.png")).convert()
            # pygame.draw.line(screen, self.color, tank_c, (self.x + int(self.width / 2), self.y - int(self.width / 2)),
            #                  4)

        if self.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(enemy_dir, "player_3.png")).convert()
            # pygame.draw.line(screen, self.color, tank_c,
            #                  (self.x + int(self.width / 2), self.y + self.width + int(self.width / 2)), 4)

    def move(self):
        if self.direction == Direction.LEFT:
            self.rect.x -= self.speed
        if self.direction == Direction.RIGHT:
            self.rect.x += self.speed
        if self.direction == Direction.UP:
            self.rect.y -= self.speed
        if self.direction == Direction.DOWN:
            self.rect.y += self.speed
        self.draw()

        # Borders
        if self.rect.x > WIDTH:
            self.rect.x = WIDTH - 975
        if self.rect.x < 0:
            self.rect.x = WIDTH - 25
        if self.rect.y > HEIGHT:
            self.rect.y = HEIGHT - 775
        if self.rect.y < 0:
            self.rect.y = HEIGHT - 25


class Bullet:
    def __init__(self, x, y, color, drop):
        self.x = x
        self.y = y
        self.color = color
        self.speed = 1
        self.radius = 4
        self.dx = 0
        self.dy = 0
        self.drop = False

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def fire(self):
        if self.drop:
            self.x += self.dx
            self.y += self.dy
            self.draw()

    def shoot(self, Tank):
        shoot_sound_enemy.play()
        if Tank.direction == Direction.RIGHT:
            self.x, self.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 15, 0
        if Tank.direction == Direction.LEFT:
            self.x, self.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = - 15, 0
        if Tank.direction == Direction.UP:
            self.x, self.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, -15
        if Tank.direction == Direction.DOWN:
            self.x, self.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, 15

    def remove(self):
        if self.x >= WIDTH or self.x <= 0:
            return True
        if self.y >= HEIGHT or self.y <= 0:
            return True
        return False

    def collision(self, Tank):

        if Tank.direction == Direction.RIGHT and self.drop:
            if (Tank.rect.x < self.x < Tank.rect.x + 60) and (Tank.rect.y < self.y < Tank.rect.y + 40):
                return True
        if Tank.direction == Direction.LEFT and self.drop:
            if (Tank.rect.x - 20 < self.x < Tank.rect.x + 40) and (Tank.rect.y < self.y < Tank.rect.y + 40):
                return True
        if Tank.direction == Direction.UP and self.drop:
            if (Tank.rect.y - 20 < self.y < Tank.rect.y + 40) and (Tank.rect.y < self.x < Tank.rect.x + 40):
                return True
        if Tank.direction == Direction.DOWN and self.drop:
            if (Tank.rect.y < self.y < Tank.rect.y + 60) and (Tank.rect.x < self.x < Tank.rect.x + 40):
                return True


class Wall(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.x = x
        self.y = y


class FirstAidKit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Position of FirstAidKit, velocity, texture
        self.image = pygame.image.load(path.join(player_dir, "first_aid_kit.png")).convert()
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.last = pygame.time.get_ticks()
        self.last = pygame.time.get_ticks()
        self.cooldown = 3000 # 3 seconds

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last >= self.cooldown:
            self.last = now
            self.kill()


    # def hide(self):
    #     self.hidden = True
    #     self.hide_timer = pygame.time.get_ticks()
    #     self.rect.center = (WIDTH / 2, HEIGHT - 10)

        #     self.speedy = 4
    #
    # def update(self):
    #     self.rect.y += self.speedy
    # # if FirstAidKit goes off bottom of window, destroy it
    #     if self.rect.top > HEIGHT:
    #         self.kill()


def player_1_lives():
    font = pygame.font.SysFont("Arial", 25)
    lives = font.render("Player 1: " + str(player_1.lives), True, RED)
    screen.blit(lives, (850, 20))


def player_2_lives():
    font = pygame.font.SysFont("Arial", 25)
    lives = font.render("Player 2: " + str(player_2.lives), True, RED)
    screen.blit(lives, (850, 40))


def start_menu():
    screen.blit(background, background_rect)
    render(screen, "Welcome to Armored Kill", 48, WIDTH / 2, HEIGHT / 4)
    render(screen, "Arrow WASD/arrows to move. Hold Enter/Space to fire", 25, WIDTH / 2, HEIGHT / 1.5)
    render(screen, "Press any key to begin", 22, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()
    menu = True
    while menu:
        clock.tick(FPS)
        for key in pygame.event.get():
            if key.type == pygame.QUIT:
                pygame.quit()
            if key.type == pygame.KEYUP:
                menu = False


def end_menu():
    screen.blit(background, background_rect)
    render(screen, "GAME OVER", 64, WIDTH / 2, HEIGHT / 4)
    render(screen, "Press ESCAPE to end", 22, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()
    end = True
    while end:
        clock.tick(FPS)
        for key in pygame.event.get():
            key_pressed = pygame.key.get_pressed()
            if key.type == pygame.QUIT:
                pygame.quit()
            if key_pressed[pygame.K_ESCAPE]:
                pygame.quit()


def render(surface, text, size, x, y):
    font_name = pygame.font.match_font('Arial')
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)


New_Game = True
Game_Over = False
Game = True

player_1 = PlayerTank(300, 300, 2, (255, 123, 100))
player_2 = EnemyTank(100, 100, 2, (100, 230, 40))
bullet_player_1 = Bullet(player_1.rect.x + int(player_1.width / 2), player_1.rect.y + int(player_1.width / 2), (255, 123, 100),
                         False)
bullet_player_2 = Bullet(player_2.rect.x + int(player_2.width / 2), player_2.rect.y + int(player_2.width / 2), (0, 120, 255),
                         False)
tanks = [player_1, player_2]
bullets = [bullet_player_1, bullet_player_2]

# TODO add random coordinates
wallList = [
    Wall(random.randrange(0, WIDTH), random.randrange(0, HEIGHT)),
    Wall(100, 100),
    Wall(130, 100),
    Wall(160, 100),
    Wall(190, 100),
    Wall(400, 100)
]

all_sprites = pygame.sprite.Group()
first_ait_kit = pygame.sprite.Group()
walls = pygame.sprite.Group(wallList)
all_sprites.add(player_1)
all_sprites.add(player_2)


while Game:
    clock.tick(FPS)
    if New_Game:
        start_menu()
        New_Game = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Game = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                Game = False
            if event.key == pygame.K_RETURN:
                if not bullet_player_1.drop:
                    bullet_player_1.drop = True
                    bullet_player_1.shoot(player_1)
            if event.key == pygame.K_SPACE:
                if not bullet_player_2.drop:
                    bullet_player_2.drop = True
                    bullet_player_2.shoot(player_2)
            for tank in tanks:
                if event.key in tank.KEY.keys():
                    tank.change_direction(tank.KEY[event.key])

        for bullet in bullets:
            if bullet.remove():
                bullet.drop = False

    if bullet_player_1.collision(player_2):
        explosion_sound_tank.play()
        player_2.lives -= 1
        bullet_player_1.drop = False
        bullet_player_1.x, bullet_player_1.y = player_1.rect.x + int(player_1.width / 2), player_1.rect.y + int(
            player_1.width / 2)
    if bullet_player_2.collision(player_1):
        explosion_sound_tank.play()
        player_1.lives -= 1
        bullet_player_2.drop = False
        bullet_player_2.x, bullet_player_2.y = player_2.rect.x + int(player_2.width / 2), player_2.rect.y + int(
            player_2.width / 2)

    if random.randrange(0, 100) < 1: # 1 % probability
        health_boost = FirstAidKit(random.randint(50, WIDTH), random.randint(50, HEIGHT))
        all_sprites.add(health_boost)
        first_ait_kit.add(health_boost)

    all_sprites.update()

    if Game_Over:
        end_menu()
        Game_Over = False

    screen.fill(BLACK)
    all_sprites.draw(screen)
    # screen.blit(background, background_rect)

    for tank in tanks:
        tank.move()

    # Render walls
    for wall in wallList:
        screen.blit(wall.image, (wall.x, wall.y))

    if player_1.lives == 0 or player_2.lives == 0:
        Game_Over = True

    bullet_player_1.fire()
    bullet_player_2.fire()
    player_1_lives()
    player_2_lives()

    pygame.display.flip()

pygame.quit()
