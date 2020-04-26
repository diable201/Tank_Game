import pygame 
import random 

from os import path 

WIDTH = 800
HEIGHT = 600
FPS = 60


pygame.init()
pygame.display.set_caption('Armored Kill')
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

#TODO directories


images_of_player = 'player.png'

class PlayerTank(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = images_of_player
        self.rect = self.image.get_rect()
        self.radius = 25
        self.rect.centerx = random.randrange(WIDTH)
        self.rect.bottom = random.randrange(HEIGHT)
        self.lives = 3
        self.health = 100
        self.speedx = 0
        self.speedy = 0

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


all_sprites = pygame.sprite.Group()
player_tank = PlayerTank()
all_sprites.add(player_tank)



New_Game = True
Game = True

while Game:
    clock.tick(FPS)
    if New_Game:
        all_sprites = pygame.sprite.Group()
        player_tank = PlayerTank()
        all_sprites.add(player_tank)
        #draw(PlayerTank)
        screen.fill((0, 0, 0))

    pygame.display.flip()

pygame.quit()


