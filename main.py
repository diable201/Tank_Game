import pygame
import random
import pika
import uuid
import json

from os import path
from enum import Enum
from threading import Thread

WIDTH = 1000
HEIGHT = 800
FPS = 60
POWER_UP_TIME = 5000

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
pygame.mixer.music.load(path.join(sound_dir, 'ost.ogg'))
pygame.mixer.music.play(-1)  # for loop
pygame.mixer.music.set_volume(5)

shoot_sound_player = pygame.mixer.Sound(path.join(sound_dir, 'shoot_player.ogg'))
shoot_sound_enemy = pygame.mixer.Sound(path.join(sound_dir, 'shoot_enemy.ogg'))
explosion_sound_tank = pygame.mixer.Sound(path.join(sound_dir, 'explosion_tank.ogg'))

# Directories for textures
background_dir = path.join(path.dirname(__file__), 'Textures/Background')
player_dir = path.join(path.dirname(__file__), 'Textures/Player')
player_multiplayer_dir = path.join(path.dirname(__file__), 'Textures/Player_Multiplayer')
enemy_dir = path.join(path.dirname(__file__), 'Textures/Enemy')
effects_dir = path.join(path.dirname(__file__), 'Textures/Effects')
explosions_dir = path.join(path.dirname(__file__), 'Textures/Explosions')
walls_dir = path.join(path.dirname(__file__), 'Textures/Walls')
background = pygame.image.load(path.join(background_dir, "back.png")).convert()
background_rect = background.get_rect()

# Sprites for animating various explosions
animation_of_explosion = {'large': [], 'small': [], 'wall': []}
for animation in range(1, 9):
    filename = 'explosion_{}.png'.format(animation)
    img = pygame.image.load(path.join(explosions_dir, filename)).convert()
    img.set_colorkey(BLACK)
    img_large = pygame.transform.scale(img, (75, 75))
    animation_of_explosion['large'].append(img_large)
    img_small = pygame.transform.scale(img, (32, 32))
    animation_of_explosion['small'].append(img_small)
    filename = 'wall_explosion_{}.png'.format(animation)
    img_player = pygame.image.load(path.join(explosions_dir, filename)).convert()
    img_player.set_colorkey(BLACK)
    animation_of_explosion['wall'].append(img_player)


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class PlayerTank(pygame.sprite.Sprite):

    def __init__(self, x, y, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP,
                 d_down=pygame.K_DOWN):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()
        self.rect = self.image.get_rect()
        self.image.set_colorkey(BLACK)
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.speed_time = pygame.time.get_ticks()
        self.lives = 3
        self.width = 25
        self.direction = Direction.RIGHT
        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}
        self.scores = 0

    def draw(self):
        if self.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(player_dir, "player_2.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.UP:
            self.image = pygame.image.load(path.join(player_dir, "player_1.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(player_dir, "player_4.png")).convert()
            self.image.set_colorkey(BLACK)

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

    def power(self):
        self.speed += 2
        self.speed_time = pygame.time.get_ticks()

    def update(self):
        if self.speed >= 4 and pygame.time.get_ticks() - self.speed_time > POWER_UP_TIME:
            self.speed = 2


class EnemyTank(pygame.sprite.Sprite):

    def __init__(self, x, y, d_right=pygame.K_d, d_left=pygame.K_a, d_up=pygame.K_w,
                 d_down=pygame.K_s):
        pygame.sprite.Sprite.__init__(self)
        # Initialize player attributes, coordinates
        self.image = pygame.image.load(path.join(enemy_dir, "player_1.png")).convert()
        self.rect = self.image.get_rect()
        self.image.set_colorkey(BLACK)
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.width = 25
        self.lives = 3
        self.direction = Direction.LEFT
        self.last_shot = pygame.time.get_ticks()
        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}
        self.speed_time = pygame.time.get_ticks()
        self.scores = 0

    def change_direction(self, direction):
        self.direction = direction

    def draw(self):
        if self.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(enemy_dir, "player_4.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(enemy_dir, "player_2.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.UP:
            self.image = pygame.image.load(path.join(enemy_dir, "player_1.png")).convert()
            self.image.set_colorkey(BLACK)
        if self.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(enemy_dir, "player_3.png")).convert()
            self.image.set_colorkey(BLACK)

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

    def power(self):
        self.speed += 2
        self.speed_time = pygame.time.get_ticks()

    def update(self):
        if self.speed >= 4 and pygame.time.get_ticks() - self.speed_time > POWER_UP_TIME:
            self.speed = 2


class Bullet(pygame.sprite.Sprite):

    def __init__(self, x, y, flight):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(path.join(effects_dir, "Shell_1.png")).convert()
        self.rect = self.image.get_rect()
        self.image.set_colorkey(BLACK)
        self.rect.x = x
        self.rect.y = y
        self.speed = 3
        self.flight = False
        self.speed_time = pygame.time.get_ticks()
        self.dx = 0
        self.dy = 0

    def fire(self):
        if self.flight:
            self.rect.x += self.dx
            self.rect.y += self.dy

    def shoot(self, Tank):
        shoot_sound_enemy.play()
        if Tank.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_4.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 15, 0
        if Tank.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_2.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = - 15, 0
        if Tank.direction == Direction.UP:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_1.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, -15
        if Tank.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_3.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, 15

    def remove(self):
        if self.rect.x >= WIDTH or self.rect.x <= 0:
            self.kill()
            return True
        if self.rect.y >= HEIGHT or self.rect.y <= 0:
            self.kill()
            return True
        return False

    def collision(self, Tank):

        if Tank.direction == Direction.RIGHT and self.flight:
            if (Tank.rect.x < self.rect.x < Tank.rect.x + 60) and (Tank.rect.y < self.rect.y < Tank.rect.y + 40):
                self.kill()
                return True
        if Tank.direction == Direction.LEFT and self.flight:
            if (Tank.rect.x - 20 < self.rect.x < Tank.rect.x + 40) and (Tank.rect.y < self.rect.y < Tank.rect.y + 40):
                self.kill()
                return True
        if Tank.direction == Direction.UP and self.flight:
            if (Tank.rect.y - 20 < self.rect.y < Tank.rect.y + 40) and (Tank.rect.y < self.rect.x < Tank.rect.x + 40):
                self.kill()
                return True
        if Tank.direction == Direction.DOWN and self.flight:
            if (Tank.rect.y < self.rect.y < Tank.rect.y + 60) and (Tank.rect.x < self.rect.x < Tank.rect.x + 40):
                self.kill()
                return True

    def power(self, Tank):
        shoot_sound_enemy.play()
        self.speed = 5
        if Tank.direction == Direction.RIGHT:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_4.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 30, 0
        if Tank.direction == Direction.LEFT:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_2.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = -30, 0
        if Tank.direction == Direction.UP:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_1.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, -30
        if Tank.direction == Direction.DOWN:
            self.image = pygame.image.load(path.join(effects_dir, "Shell_3.png")).convert()
            self.rect = self.image.get_rect()
            self.image.set_colorkey(BLACK)
            self.rect.x, self.rect.y = Tank.rect.x + int(Tank.width / 2), Tank.rect.y + int(Tank.width / 2)
            self.dx, self.dy = 0, 30

    def update(self):
        if self.speed >= 8 and pygame.time.get_ticks() - self.speed_time > POWER_UP_TIME:
            self.speed = 3


class Wall(pygame.sprite.Sprite):

    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(path.join(walls_dir, "wall.png")).convert()
        self.rect = self.image.get_rect()
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.rect.x = x
        self.rect.y = y


class SuperPowerKit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        # Position of FirstAidKit, velocity, texture
        self.image = pygame.image.load(path.join(player_dir, "first_aid_kit.png")).convert()
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.last = pygame.time.get_ticks()
        self.time = 5000  # 5 seconds

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last >= self.time:
            self.last = now
            self.kill()


class Explosion(pygame.sprite.Sprite):

    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)

        # Position of explosion
        self.size = size
        self.image = animation_of_explosion[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        # Drawing explosion sprites until all sprites are drawn
        timer = pygame.time.get_ticks()
        if timer - self.last_update > self.frame_rate:
            self.last_update = timer
            self.frame += 1
            if self.frame == len(animation_of_explosion[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = animation_of_explosion[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


# Functions for single player
def player_1_lives():
    font = pygame.font.SysFont("Arial", 25)
    lives = font.render("Player 1 lives: " + str(player_1.lives), True, WHITE)
    screen.blit(lives, (800, 20))


def player_2_lives():
    font = pygame.font.SysFont("Arial", 25)
    lives = font.render("Player 2 lives: " + str(player_2.lives), True, WHITE)
    screen.blit(lives, (800, 40))


def player_1_scores():
    font = pygame.font.SysFont("Arial", 25)
    scores = font.render("Player 1 scores:" + str(player_1.scores), True, WHITE)
    screen.blit(scores, (50, 20))


def player_2_scores():
    font = pygame.font.SysFont("Arial", 25)
    scores = font.render("Player 2 scores:" + str(player_2.scores), True, WHITE)
    screen.blit(scores, (50, 40))


def multiplayer():
    WIDTH = 1000
    HEIGHT = 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Armored Kill')
    IP = '34.254.177.17'
    PORT = 5672
    VIRTUAL_HOST = 'dar-tanks'
    USERNAME = 'dar-tanks'
    PASSWORD = '5orPLExUYnyVYZg48caMpX'

    sound_dir = path.join(path.dirname(__file__), 'Sound')
    pygame.mixer.init()

    pygame.mixer.music.load(path.join(sound_dir, 'ost.ogg'))
    pygame.mixer.music.play(-1)  # for loop

    class TankRpcClient:

        def __init__(self):
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=IP,
                    port=PORT,
                    virtual_host=VIRTUAL_HOST,
                    credentials=pika.PlainCredentials(
                        username=USERNAME,
                        password=PASSWORD
                    )
                )
            )
            self.channel = self.connection.channel()
            queue = self.channel.queue_declare(queue='',
                                               auto_delete=True,
                                               exclusive=True
                                               )
            self.callback_queue = queue.method.queue
            self.channel.queue_bind(
                exchange='X:routing.topic',
                queue=self.callback_queue
            )

            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True
            )

            self.response = None
            self.corr_id = None
            self.token = None
            self.tank_id = None
            self.room_id = None

        def on_response(self, ch, method, props, body):
            if self.corr_id == props.correlation_id:
                self.response = json.loads(body)
                print(self.response)

        def call(self, key, message={}):

            # message = {}
            # if message is None:
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.channel.basic_publish(
                exchange='X:routing.topic',
                routing_key=key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                ),
                body=json.dumps(message)
            )
            while self.response is None:
                self.connection.process_data_events()

        def check_server_status(self):
            self.call('tank.request.healthcheck')
            return self.response['status'] == '200'

        def obtain_token(self, room_id):
            message = {
                'roomId': room_id
            }
            self.call('tank.request.register', message)
            if 'token' in self.response:
                self.token = self.response['token']
                self.tank_id = self.response['tankId']
                self.room_id = self.response['roomId']

                return True
            return False

        def turn_tank(self, token, direction):
            message = {
                'token': token,
                'direction': direction
            }
            self.call('tank.request.turn', message)

        def fire_tank(self, token):
            message = {
                'token': token
            }
            self.call('tank.request.fire', message)

    class TankConsumerClient(Thread, pygame.sprite.Sprite):

        def __init__(self, room_id):
            super().__init__()
            pygame.sprite.Sprite.__init__(self)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=IP,
                    port=PORT,
                    virtual_host=VIRTUAL_HOST,
                    credentials=pika.PlainCredentials(
                        username=USERNAME,
                        password=PASSWORD
                    )
                )
            )
            self.channel = self.connection.channel()
            queue = self.channel.queue_declare(queue='',
                                               auto_delete=True,
                                               exclusive=True
                                               )
            event_listener = queue.method.queue
            self.channel.queue_bind(exchange='X:routing.topic',
                                    queue=event_listener,
                                    routing_key='event.state.' + room_id)

            self.channel.basic_consume(
                queue=event_listener,
                on_message_callback=self.on_response,
                auto_ack=True
            )
            self.response = None

        def on_response(self, ch, method, props, body):
            self.response = json.loads(body)
            print(self.response)

        def run(self):
            self.channel.start_consuming()

        def stop(self):
            self.channel.stop_consuming()

        def draw_tank(self, x, y, direction, **kwargs):

            if direction == UP:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_1.png')
                screen.blit(tank_image, (x, y))

            if direction == DOWN:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_3.png')
                screen.blit(tank_image, (x, y))

            if direction == LEFT:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2.png')
                screen.blit(tank_image, (x, y))

            if direction == RIGHT:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_4.png')
                screen.blit(tank_image, (x, y))

    UP = 'UP'
    DOWN = 'DOWN'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'

    MOVE_KEYS = {
        pygame.K_w: UP,
        pygame.K_a: LEFT,
        pygame.K_s: DOWN,
        pygame.K_d: RIGHT
    }

    def draw_tank(x, y, direction, **kwargs):

        if direction == UP:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_1.png')
            screen.blit(tank_image, (x, y))

        if direction == DOWN:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_3.png')
            screen.blit(tank_image, (x, y))

        if direction == LEFT:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_2.png')
            screen.blit(tank_image, (x, y))

        if direction == RIGHT:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_4.png')
            screen.blit(tank_image, (x, y))

    def draw_bullet(x, y, width, height, direction):

        if direction == RIGHT or direction == LEFT:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_1.png'), (15, 5))
            screen.blit(my_im, (x, y))
        if direction == UP or direction == DOWN:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_2.png'), (5, 15))
            screen.blit(my_im, (x, y))

    def draw_enemy_bullet(x, y, width, height, direction):
        if direction == RIGHT or direction == LEFT:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_3.png'), (15, 5))
            screen.blit(my_im, (x, y))
        if direction == UP or direction == DOWN:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_4.png'), (5, 15))
            screen.blit(my_im, (x, y))

    player = TankConsumerClient('room-10')

    def game_start():
        mainloop = True
        font = pygame.font.Font('freesansbold.ttf', 16)
        Kicked = False
        Win = False
        Lose = False
        while mainloop:
            screen.fill(BLACK)
            screen.blit(background, background_rect)
            for event in pygame.event.get():
                clock.tick(FPS)
                if event.type == pygame.QUIT:
                    mainloop = False
                    # event_client.daemon = True
                    client.connection.close()
                    pygame.quit()
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        mainloop = False
                        client.connection.close()
                        pygame.quit()

                    if event.key in MOVE_KEYS:
                        client.turn_tank(client.token, MOVE_KEYS[event.key])

                    if event.key == pygame.K_SPACE:
                        client.fire_tank(client.token)
                        shoot_sound_player.play()

            try:
                bullets = event_client.response['gameField']['bullets']
                tanks = event_client.response['gameField']['tanks']
                i = 30
                pygame.draw.rect(screen, WHITE, (720, 10, 260, 40 * len(tanks)), 10)
                table = {tank['id']:
                             [tank['score'],
                              tank['health']]
                         for tank in tanks
                         }
                sorted_table = reversed(sorted(table.items(), key=lambda kv: kv[1]))
                for score in sorted_table:
                    if score[0] == client.tank_id:
                        color = RED
                    else:
                        color = BLUE
                    text = font.render(
                        'ID:' + str(score[0]) + ' Scores: ' + str(score[1][0]) + ' Lives : ' + str(score[1][1]), True,
                        color)
                    textRect = text.get_rect()
                    textRect.center = (850, i)
                    screen.blit(text, textRect)
                    i += 30
                for tank in tanks:
                    if client.tank_id == tank['id']:
                        player.draw_tank(**tank)
                    else:
                        draw_tank(**tank)

                    remaining_time = event_client.response['remainingTime']

                    text = font.render('Remaining Time: {}'.format(remaining_time), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (100, 20)
                    screen.blit(text, textRect)

                    # Only for 2 players. Sadface.
                    # if tank['id'] == client.tank_id:
                    #     text = font.render('ID: {}'.format(client.tank_id), True, WHITE)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 150)
                    #     screen.blit(text, textRect)
                    # else:
                    #     text = font.render('Not My ID: {}'.format(tank['id']), True, BLACK)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 300)
                    #     screen.blit(text, textRect)
                    # if tank['id'] == client.tank_id:
                    #     my_score = tank['score']
                    #     text = font.render('My Scores: {}'.format(my_score), True, WHITE)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 200)
                    #     screen.blit(text, textRect)
                    # else:
                    #     not_my_score = tank['score']
                    #     text = font.render('Not My Scores: {}'.format(not_my_score), True, BLACK)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 350)
                    #     screen.blit(text, textRect)
                    # if tank['id'] == client.tank_id:
                    #     my_health = tank['health']
                    #     text = font.render('My Lives: {}'.format(my_health), True, WHITE)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 250)
                    #     screen.blit(text, textRect)
                    # else:
                    #     not_my_health = tank['health']
                    #     text = font.render('Not my Lives: {}'.format(not_my_health), True, BLACK)
                    #     textRect = text.get_rect()
                    #     textRect.center = (850, 400)
                    #     screen.blit(text, textRect)

                for bullet in bullets:
                    if client.tank_id:
                        bullet_x = bullet['x']
                        bullet_y = bullet['y']
                        bullet_width = bullet['width']
                        bullet_height = bullet['height']
                        bullet_direction = bullet['direction']
                        draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height, bullet_direction)
                    if client.tank_id != tank['id']:
                        draw_enemy_bullet(**bullet)

            except:
                pass

            winners = event_client.response['winners']
            kicks = event_client.response['kicked']
            losers = event_client.response['losers']

            def win():
                screen.blit(background, background_rect)
                render(screen, "YOU WIN. Do you want to restart the game?", 48, WIDTH / 2, HEIGHT / 4)
                render(screen, "For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if remaining_time != 0:
                    render(screen, "Your Scores: 3", 16, 500, 400)
                else:
                    if tank['id'] == client.tank_id:
                        my_score = tank['score']
                        text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                        textRect = text.get_rect()
                        textRect.center = (500, 400)
                        screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            def lose():
                screen.blit(background, background_rect)
                render(screen, "YOU LOSE. Do you want to restart the game?", 48, WIDTH / 2, HEIGHT / 4)
                render(screen, "For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if tank['id'] == client.tank_id:
                    my_score = tank['score']
                    text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (500, 400)
                    screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            def kicked():
                screen.blit(background, background_rect)
                render(screen, "You was kicked. For MultiPlayer press R. For Quit press 1.", 32, WIDTH / 2,
                       HEIGHT / 4)
                render(screen, "Do you want to restart? For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if tank['id'] == client.tank_id:
                    my_score = tank['score']
                    text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (500, 400)
                    screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            if winners:
                for winner in winners:
                    my_id = client.tank_id
                    if winner['tankId'] == my_id:
                        Win = True

            if Win:
                win()

            elif losers:
                for loser in losers:
                    my_id = client.tank_id
                    if loser['tankId'] == my_id:
                        Lose = True

            if Lose:
                lose()

            elif kicks:
                for kick in kicks:
                    my_id = client.tank_id
                    if kick['tankId'] == my_id:
                        Kicked = True

            if Kicked:
                kicked()

            pygame.display.flip()
        client.connection.close()
        pygame.quit()

    client = TankRpcClient()
    client.check_server_status()
    client.obtain_token('room-11')

    event_client = TankConsumerClient('room-11')
    event_client.start()
    game_start()


def multiplayer_ai():
    WIDTH = 1000
    HEIGHT = 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Armored Kill')
    IP = '34.254.177.17'
    PORT = 5672
    VIRTUAL_HOST = 'dar-tanks'
    USERNAME = 'dar-tanks'
    PASSWORD = '5orPLExUYnyVYZg48caMpX'

    sound_dir = path.join(path.dirname(__file__), 'Sound')
    pygame.mixer.init()

    pygame.mixer.music.load(path.join(sound_dir, 'ost.ogg'))
    pygame.mixer.music.play(-1)  # for loop

    class TankRpcClient:

        def __init__(self):
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=IP,
                    port=PORT,
                    virtual_host=VIRTUAL_HOST,
                    credentials=pika.PlainCredentials(
                        username=USERNAME,
                        password=PASSWORD
                    )
                )
            )
            self.channel = self.connection.channel()
            queue = self.channel.queue_declare(queue='',
                                               auto_delete=True,
                                               exclusive=True
                                               )
            self.callback_queue = queue.method.queue
            self.channel.queue_bind(
                exchange='X:routing.topic',
                queue=self.callback_queue
            )

            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True
            )

            self.response = None
            self.corr_id = None
            self.token = None
            self.tank_id = None
            self.room_id = None

        def on_response(self, ch, method, props, body):
            if self.corr_id == props.correlation_id:
                self.response = json.loads(body)
                # print(self.response)

        def call(self, key, message={}):
            # message = {}
            # if message is None:
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.channel.basic_publish(
                exchange='X:routing.topic',
                routing_key=key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                ),
                body=json.dumps(message)
            )
            while self.response is None:
                self.connection.process_data_events()

        def check_server_status(self):
            self.call('tank.request.healthcheck')
            return self.response['status'] == '200'

        def obtain_token(self, room_id):
            message = {
                'roomId': room_id
            }
            self.call('tank.request.register', message)
            if 'token' in self.response:
                self.token = self.response['token']
                self.tank_id = self.response['tankId']
                self.room_id = self.response['roomId']
                return True
            return False

        def turn_tank(self, token, direction):
            message = {
                'token': token,
                'direction': direction
            }
            self.call('tank.request.turn', message)

        def fire_tank(self, token):
            message = {
                'token': token
            }
            self.call('tank.request.fire', message)

    class TankConsumerClient(Thread, pygame.sprite.Sprite):

        def __init__(self, room_id):
            super().__init__()
            pygame.sprite.Sprite.__init__(self)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=IP,
                    port=PORT,
                    virtual_host=VIRTUAL_HOST,
                    credentials=pika.PlainCredentials(
                        username=USERNAME,
                        password=PASSWORD
                    )
                )
            )
            self.radius = 800
            self.channel = self.connection.channel()
            queue = self.channel.queue_declare(queue='',
                                               auto_delete=True,
                                               exclusive=True
                                               )
            event_listener = queue.method.queue
            self.channel.queue_bind(exchange='X:routing.topic',
                                    queue=event_listener,
                                    routing_key='event.state.' + room_id)

            self.channel.basic_consume(
                queue=event_listener,
                on_message_callback=self.on_response,
                auto_ack=True
            )
            self.response = None

        def on_response(self, ch, method, props, body):
            self.response = json.loads(body)
            # if client.tank_id:
            #     print(self.response)

        def run(self):
            self.channel.start_consuming()

        def stop(self):
            self.channel.stop_consuming()

        def draw_tank(self, x, y, direction, **kwargs):
            if direction == UP:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_1.png')
                screen.blit(tank_image, (x, y))

            if direction == DOWN:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_3.png')
                screen.blit(tank_image, (x, y))

            if direction == LEFT:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2.png')
                screen.blit(tank_image, (x, y))

            if direction == RIGHT:
                tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_4.png')
                screen.blit(tank_image, (x, y))

    UP = 'UP'
    DOWN = 'DOWN'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'

    MOVE_KEYS = {
        pygame.K_w: UP,
        pygame.K_a: LEFT,
        pygame.K_s: DOWN,
        pygame.K_d: RIGHT
    }

    def draw_enemy_tank(x, y, direction, **kwargs):
        if direction == UP:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_1.png')
            screen.blit(tank_image, (x, y))

        if direction == DOWN:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_3.png')
            screen.blit(tank_image, (x, y))

        if direction == LEFT:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_2.png')
            screen.blit(tank_image, (x, y))

        if direction == RIGHT:
            tank_image = pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/player_2_4.png')
            screen.blit(tank_image, (x, y))

    def draw_bullet(x, y, width, height, direction):

        if direction == RIGHT or direction == LEFT:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_1.png'), (15, 5))
            screen.blit(my_im, (x, y))
        if direction == UP or direction == DOWN:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_2.png'), (5, 15))
            screen.blit(my_im, (x, y))

    def draw_enemy_bullet(x, y, width, height, direction):
        if direction == RIGHT or direction == LEFT:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_3.png'), (15, 5))
            screen.blit(my_im, (x, y))
        if direction == UP or direction == DOWN:
            my_im = pygame.transform.scale(
                pygame.image.load('/Users/sanzhar/Tank_Game-/Textures/Player_Multiplayer/Shell_4.png'), (5, 15))
            screen.blit(my_im, (x, y))

    player = TankConsumerClient('room-11')

    def game_start():
        mainloop = True
        font = pygame.font.Font('freesansbold.ttf', 16)
        Win = False
        Lose = False
        Kicked = False
        direction_movement = ''

        while mainloop:
            screen.fill(BLACK)
            screen.blit(background, background_rect)
            for event in pygame.event.get():
                clock.tick(FPS)
                if event.type == pygame.QUIT:
                    mainloop = False
                    event_client.daemon = True
                    pygame.quit()
                    client.connection.close()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mainloop = False
                        pygame.quit()
                        client.connection.close()
                    if event.key in MOVE_KEYS:
                        client.turn_tank(client.token, MOVE_KEYS[event.key])
                    if event.key == pygame.K_SPACE:
                        client.fire_tank(client.token)
                        shoot_sound_player.play()

            try:
                bullets = event_client.response['gameField']['bullets']
                tanks = event_client.response['gameField']['tanks']
                i = 30
                pygame.draw.rect(screen, WHITE, (720, 10, 260, 40 * len(tanks)), 10)
                table = {tank['id']:
                             [tank['score'],
                              tank['health']]
                         for tank in tanks
                         }
                sorted_table = reversed(sorted(table.items(), key=lambda kv: kv[1]))
                for score in sorted_table:
                    if score[0] == client.tank_id:
                        color = RED
                    else:
                        color = BLUE
                    text = font.render(
                        'ID:' + str(score[0]) + ' Scores: ' + str(score[1][0]) + ' Lives : ' + str(score[1][1]), True,
                        color)
                    textRect = text.get_rect()
                    textRect.center = (850, i)
                    screen.blit(text, textRect)
                    i += 35

                for tank in tanks:
                    if client.tank_id == tank['id']:
                        player.draw_tank(**tank)
                    else:
                        draw_enemy_tank(**tank)
                    tank_id = tank['id']
                    tank_x = tank['x']
                    tank_y = tank['y']
                    my_id = client.tank_id
                    if tank['id'] == my_id:
                        client_x = tank_x
                        client_y = tank_y

                    my_tank_x = client_x
                    my_tank_y = client_y

                    not_my_tank_x = tank_x
                    not_my_tank_y = tank_y

                    if tank_id != client.tank_id:
                        for coordinate in range(my_tank_x, my_tank_x + 100):
                            if not_my_tank_x == coordinate:
                                if not_my_tank_y > my_tank_y:
                                    direction_movement = 'UP'
                                    client.fire_tank(client.token)
                                    shoot_sound_player.play()

                                elif not_my_tank_y <= my_tank_y:
                                    direction_movement = 'Down'
                                    client.fire_tank(client.token)
                                    shoot_sound_player.play()

                        for coordinate in range(my_tank_y, my_tank_y + 100):
                            if not_my_tank_x == coordinate:
                                if my_tank_x > not_my_tank_x:
                                    direction_movement = 'RIGHT'
                                    client.fire_tank(client.token)
                                    shoot_sound_player.play()

                                elif my_tank_x <= not_my_tank_x:
                                    direction_movement = 'LEFT'
                                    client.fire_tank(client.token)
                                    shoot_sound_player.play()
                    client.turn_tank(client.token, direction_movement)

                    remaining_time = event_client.response['remainingTime']
                    text = font.render('Remaining Time: {}'.format(remaining_time), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (100, 20)
                    screen.blit(text, textRect)

                for bullet in bullets:
                    if client.tank_id:
                        bullet_x = bullet['x']
                        bullet_y = bullet['y']
                        bullet_width = bullet['width']
                        bullet_height = bullet['height']
                        bullet_direction = bullet['direction']
                        draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height, bullet_direction)
                    if client.tank_id != tank['id']:
                        draw_enemy_bullet(**bullet)
            except:
                pass

            winners = event_client.response['winners']
            kicks = event_client.response['kicked']
            losers = event_client.response['losers']

            def win():
                screen.blit(background, background_rect)
                render(screen, "YOU WIN. Do you want to restart the game?", 48, WIDTH / 2, HEIGHT / 4)
                render(screen, "For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if remaining_time != 0:
                    render(screen, "Your Scores: 3", 16, 500, 400)
                else:
                    if tank['id'] == client.tank_id:
                        my_score = tank['score']
                        text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                        textRect = text.get_rect()
                        textRect.center = (500, 400)
                        screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            def lose():
                screen.blit(background, background_rect)
                render(screen, "YOU LOSE. Do you want to restart the game?", 48, WIDTH / 2, HEIGHT / 4)
                render(screen, "For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if tank['id'] == client.tank_id:
                    my_score = tank['score']
                    text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (500, 400)
                    screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            def kicked():
                screen.blit(background, background_rect)
                render(screen, "You was kicked. For MultiPlayer press R. For Quit press 1.", 32, WIDTH / 2,
                       HEIGHT / 4)
                render(screen, "Do you want to restart? For MultiPlayer press R. For Quit press 1.",
                       25, WIDTH / 2,
                       HEIGHT / 1.5)
                if tank['id'] == client.tank_id:
                    my_score = tank['score']
                    text = font.render('Your Scores: {}'.format(my_score), True, WHITE)
                    textRect = text.get_rect()
                    textRect.center = (500, 400)
                    screen.blit(text, textRect)
                pygame.display.flip()
                menu = True
                while menu:
                    clock.tick(FPS)
                    for key in pygame.event.get():
                        if key.type == pygame.QUIT:
                            pygame.quit()
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_1]:
                            pygame.quit()
                        if pressed[pygame.K_r]:
                            multiplayer()

            if winners:
                for winner in winners:
                    my_id = client.tank_id
                    if winner['tankId'] == my_id:
                        Win = True

            if Win:
                win()

            elif losers:
                for loser in losers:
                    my_id = client.tank_id
                    if loser['tankId'] == my_id:
                        Lose = True

            if Lose:
                lose()

            elif kicks:
                for kick in kicks:
                    my_id = client.tank_id
                    if kick['tankId'] == my_id:
                        Kicked = True

            if Kicked:
                kicked()

            pygame.display.flip()
        client.connection.close()
        pygame.quit()

    client = TankRpcClient()
    client.check_server_status()
    client.obtain_token('room-11')

    event_client = TankConsumerClient('room-11')
    event_client.start()
    game_start()


def start_menu():
    screen.blit(background, background_rect)
    render(screen, "Welcome to Armored Kill", 48, WIDTH / 2, HEIGHT / 4)
    render(screen, "Arrow WASD/arrows to move. Hold Enter/Space to fire", 25, WIDTH / 2, HEIGHT / 1.5)
    render(screen, "For SinglePlayer press 1. For MultiPlayer press 2. For MultiPlayer with AI press 3.", 22, WIDTH / 2,
           HEIGHT * 3 / 4)
    pygame.display.flip()
    menu = True
    while menu:
        clock.tick(FPS)
        for key in pygame.event.get():
            if key.type == pygame.QUIT:
                pygame.quit()
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_1]:
                menu = False
            if pressed[pygame.K_2]:
                multiplayer()
            if pressed[pygame.K_3]:
                multiplayer_ai()
            if pressed[pygame.K_ESCAPE]:
                pygame.quit()


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
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)


def new_wall_static():
    wallList = [
        Wall(60, 700),
        Wall(104, 700),
        Wall(148, 700),
        Wall(192, 700),
        Wall(236, 700),
        Wall(280, 700)
    ]
    all_sprites.add(wallList)
    walls.add(wallList)


def new_wall_dynamic():
    wall = Wall(random.randrange(0, WIDTH), random.randrange(0, HEIGHT))
    all_sprites.add(wall)
    walls.add(wall)


def create_wall():
    for wall in range(4):
        new_wall_dynamic()


New_Game = True
Game_Over = False
Game = True
Multiplayer = True

player_1 = PlayerTank(300, 300)
player_2 = EnemyTank(100, 100)
bullet_player_1 = Bullet(player_1.rect.x + int(player_2.width / 2), player_1.rect.y + int(player_2.width / 2), False)
bullet_player_2 = Bullet(player_2.rect.x + int(player_2.width / 2), player_2.rect.y + int(player_2.width / 2), False)
tanks = [player_1, player_2]
bullets = [bullet_player_1, bullet_player_2]

all_sprites = pygame.sprite.Group()
first_ait_kit = pygame.sprite.Group()
walls = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
all_sprites.add(player_1)
all_sprites.add(player_2)

while Game:
    clock.tick(FPS)
    if New_Game:
        start_menu()
        New_Game = False
        new_wall_static()
        create_wall()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Game = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                Game = False
            if event.key == pygame.K_RETURN:
                if not bullet_player_1.flight:
                    bullet_player_1.flight = True
                    all_sprites.add(bullet_player_1)
                    bullet_player_1.shoot(player_1)
            if event.key == pygame.K_SPACE:
                if not bullet_player_2.flight:
                    bullet_player_2.flight = True
                    all_sprites.add(bullet_player_2)
                    bullet_player_2.shoot(player_2)
            for tank in tanks:
                if event.key in tank.KEY.keys():
                    tank.change_direction(tank.KEY[event.key])

        for bullet in bullets:
            if bullet.remove():
                bullet.flight = False

    if bullet_player_1.collision(player_2):
        player_1.scores += 1
        explosion = Explosion(player_2.rect.center, 'large')
        all_sprites.add(explosion)
        explosion_sound_tank.play()
        player_2.lives -= 1
        bullet_player_1.flight = False
    if bullet_player_2.collision(player_1):
        player_2.scores += 1
        explosion = Explosion(player_1.rect.center, 'large')
        all_sprites.add(explosion)
        explosion_sound_tank.play()
        player_1.lives -= 1
        bullet_player_2.flight = False

    if random.randrange(0, 100) < 0.1:  # 1 % probability
        health_boost = SuperPowerKit(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100))
        all_sprites.add(health_boost)
        first_ait_kit.add(health_boost)

    all_sprites.update()

    #################################PLAYER 2###########################################
    hits_wall_player_2_bullet = pygame.sprite.spritecollide(bullet_player_2, walls, True)
    for hit_wall in hits_wall_player_2_bullet:
        explosion = Explosion(hit_wall.rect.center, 'wall')
        all_sprites.add(explosion)
        bullet_player_2.flight = False
        bullet_player_2.kill()

    hits_player_2_walls = pygame.sprite.spritecollide(player_2, walls, True)
    for hit_player in hits_player_2_walls:
        explosion = Explosion(hit_player.rect.center, 'wall')
        all_sprites.add(explosion)
        player_2.lives -= 1

    hits_super_power_player_2 = pygame.sprite.spritecollide(player_2, first_ait_kit, True)
    for hit_super_power in hits_super_power_player_2:
        player_2.power()

    #################################PLAYER 1###########################################
    hits_wall_player_1_bullet = pygame.sprite.spritecollide(bullet_player_1, walls, True)
    for hit_wall in hits_wall_player_1_bullet:
        explosion = Explosion(hit_wall.rect.center, 'wall')
        all_sprites.add(explosion)
        bullet_player_1.flight = False
        bullet_player_1.kill()

    hits_player_1_walls = pygame.sprite.spritecollide(player_1, walls, True)
    for hit_player in hits_player_1_walls:
        explosion = Explosion(hit_player.rect.center, 'wall')
        all_sprites.add(explosion)
        player_1.lives -= 1

    hits_super_power_player_1 = pygame.sprite.spritecollide(player_1, first_ait_kit, True)
    for hit_super_power in hits_super_power_player_1:
        player_1.power()

    if Game_Over:
        end_menu()
        Game_Over = False

    screen.fill(BLACK)
    all_sprites.draw(screen)
    # screen.blit(background, background_rect)

    for tank in tanks:
        tank.move()

    if player_1.lives == 0 or player_2.lives == 0:
        Game_Over = True

    bullet_player_1.fire()
    bullet_player_2.fire()

    screen.fill(BLACK)
    screen.blit(background, background_rect)
    player_1_lives()
    player_2_lives()
    player_1_scores()
    player_2_scores()
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
