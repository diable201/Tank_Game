import pygame
import random 

from os import path 

WIDTH = 800
HEIGHT = 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
pygame.display.set_caption('Armored Kill')
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# TODO directories

player_dir = path.join(path.dirname(__file__), 'Textures/Player')
background_dir = path.join(path.dirname(__file__), 'Textures/Background')
player_bullet_img = pygame.image.load('Textures/Player/laser.png').convert()

background = pygame.image.load(path.join(background_dir, "back.png")).convert()
background_rect = background.get_rect()

images_of_player = []
for player in range(1, 12):
    filename = 'player_{}.png'.format(player)
    image_of_player = pygame.image.load(path.join(player_dir, filename)).convert()
    image_of_player.set_colorkey(BLACK)
    img_main = pygame.transform.scale(image_of_player, (60, 60))
    images_of_player.append(img_main)


class PlayerTank(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Initialize player attributes, coordinates
        self.radius = 30
        self.image = random.choice(images_of_player)
        self.rect = self.image.get_rect()
        self.radius = 25
        self.rect.centerx = random.randrange(WIDTH)
        self.rect.bottom = random.randrange(HEIGHT)
        self.lives = 3
        self.health = 100
        self.speedx = 0
        self.speedy = 0

        self.shoot_delay = 165
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.speedx = 0
        self.speedy = 0
        press = pygame.key.get_pressed()
        if press[pygame.K_a]:
            self.speedx = -5
        if press[pygame.K_d]:
            self.speedx = 5
        if press[pygame.K_w]:
            self.speedy = -5
        if press[pygame.K_s]:
            self.speedy = 5
        if press[pygame.K_RETURN]:
            self.shoot()

        # Acceleration
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        # Borders
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.rect.top < 0:
            self.rect.top = 0

    def shoot(self):
        timer = pygame.time.get_ticks()
        if timer - self.last_shot > self.shoot_delay:
            self.last_shot = timer
            bullet = PlayerBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            player_bullets.add(bullet)


class PlayerBullet(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)

        # Scale bullet size
        self.image = pygame.transform.scale(player_bullet_img, (9, 24))
        self.rect = self.image.get_rect()

        # Bullet position is according the player position
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10  # Negative for movement up

    def update(self):
        self.rect.y += self.speedy
        # If bullet goes off bottom of window, destroy it
        if self.rect.bottom < 0:
            self.kill()


class EnemyTank(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # Initialize player attributes, coordinates
        self.radius = 30
        self.image = random.choice(images_of_player)
        self.rect = self.image.get_rect()
        self.radius = 25
        self.rect.x = random.randint(20, WIDTH - 20)
        self.rect.y = random.randrange(-140, -30)
        self.lives = 3
        self.health = 100
        self.speedx = 0
        self.speedy = 0

        self.shoot_delay = 165
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.speedx = 0
        self.speedy = 0
        press = pygame.key.get_pressed()
        if press[pygame.K_LEFT]:
            self.speedx = -5
        if press[pygame.K_RIGHT]:
            self.speedx = 5
        if press[pygame.K_UP]:
            self.speedy = -5
        if press[pygame.K_DOWN]:
            self.speedy = 5
        if press[pygame.K_SPACE]:
            self.shoot()

        # Acceleration
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        # Borders. Better replace with width and height
        if self.rect.right > WIDTH:
            self.rect.right = 100
        if self.rect.left < 0:
            self.rect.left = 700
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = 100
        if self.rect.top < 0:
            self.rect.top = 500
        # Why this piece of shit works?

    def shoot(self):
        timer = pygame.time.get_ticks()
        if timer - self.last_shot > self.shoot_delay:
            self.last_shot = timer
            bullet = PlayerBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            player_bullets.add(bullet)


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


all_sprites = pygame.sprite.Group()
player_tank = PlayerTank()
player_bullets = pygame.sprite.Group()
enemy_tank = EnemyTank()
enemy_bullets = pygame.sprite.Group()
all_sprites.add(player_tank)
all_sprites.add(enemy_tank)


def render(surface, text, size, x, y):
    font_name = pygame.font.match_font('Arial')
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)


New_Game = True
Game = True

while Game:
    clock.tick(FPS)
    if New_Game:
        start_menu()
        New_Game = False
        all_sprites = pygame.sprite.Group()
        player_tank = PlayerTank()
        player_bullets = pygame.sprite.Group()
        enemy_tank = EnemyTank()
        enemy_bullets = pygame.sprite.Group()
        all_sprites.add(player_tank)
        all_sprites.add(enemy_tank)

    for event in pygame.event.get():
        pressed = pygame.key.get_pressed()
        if event.type == pygame.QUIT:
            Game = False
        if pressed[pygame.K_ESCAPE]:
            Game = False

    all_sprites.update()

    screen.fill(BLACK)
    screen.blit(background, background_rect)
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()