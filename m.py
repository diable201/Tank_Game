import pika
import uuid
import json
import pygame
from threading import Thread
from os import path
from enum import Enum

IP = '34.254.177.17'
PORT = 5672
VIRTUAL_HOST = 'dar-tanks'
USERNAME = 'dar-tanks'
PASSWORD = '5orPLExUYnyVYZg48caMpX'

WIDTH = 800
HEIGHT = 600

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

player_dir = path.join(path.dirname(__file__), 'Textures/Player')


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

        # if message is None:
        #     message = {}
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


class TankConsumerClient(Thread):

    def __init__(self, room_id):
        super().__init__()
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


UP = 'UP'
DOWN = 'DOWN'
LEFT = 'LEFT'
RIGHT = 'RIGHT'
FIRE = 'FIRE'

MOVE_KEYS = {
    pygame.K_w: UP,
    pygame.K_a: LEFT,
    pygame.K_s: DOWN,
    pygame.K_d: RIGHT
}


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class PlayerTank(pygame.sprite.Sprite):

    def __init__(self, x, y, speed, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP,
                 d_down=pygame.K_DOWN):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 1

        self.lives = 3
        self.width = 31
        self.height = 31
        self.direction = Direction.RIGHT
        # self.shoot_delay = 165
        # self.last_shot = pygame.time.get_ticks()

        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}

    def draw(self, x, y, width, height, direction):
        # print(**kwargs)
        tank_c = (x + int(width / 2), y + int(width / 2))
        # # image = pygame.image.load(path.join(player_dir, "player_3.png")).convert()
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)
        pygame.draw.circle(screen, (255, 255, 255), tank_c, int(width / 2))

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
        self.draw(self.rect.x, self.rect.y, self.width, self.height, Direction)


def draw_tank(x, y, width, height, direction, **kwargs):
    print(**kwargs)
    tank_c = (x + int(width / 2), y + int(width / 2))
    pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)
    pygame.draw.circle(screen, (255, 255, 255), tank_c, int(width / 2))
    pygame.draw.line(screen, (255, 255, 255), tank_c,
                     (x + width + int(width / 2), y + int(width / 2)), 4)
    if direction == DOWN:
        exit(0)


def draw_bullet(x, y, width, height, direction):
    bullet_c = (x + int(width / 2), y + int(width / 2))
    pygame.draw.rect(screen, (255, 255, 255),
                     (x, y, width, height))
    pygame.draw.rect(screen, (255, 255, 255), bullet_c)


class Button:

    def __init__(self, x, y, width, height, func):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.func = func

    def draw(self):
        font = pygame.font.Font('freesansbold.ttf', 32)
        text = font.render('click', True, (255, 255, 0))
        textRect = text.get_rect()
        textRect.center = (100, 100)
        screen.blit(text, textRect)


def click_button():
    print('ok good')


def game_start():
    mainloop = True
    font = pygame.font.Font('freesansbold.ttf', 32)
    button = Button(100, 100, 100, 100, click_button())
    while mainloop:
        screen.fill((0, 0, 0))

        pos = pygame.mouse.get_pos()
        # print(pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainloop = False
                event_client.daemon = True
                client.connection.close()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mainloop = False
                    client.connection.close()
                if event.key in MOVE_KEYS:
                    client.turn_tank(client.token, MOVE_KEYS[event.key])
                if event.key == pygame.K_SPACE:
                    client.fire_tank(client.token)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.x <= pos[0] <= button.x + button.width and button.y <= pos[1] <= button.y + button.height:
                    button.func()
        button.draw()
        try:
            remaining_time = event_client.response['remainingTime']
            # health_server = event_client.response['health']
            text = font.render('Remaining Time: {}'.format(remaining_time), True, (255, 255, 255))
            textRect = text.get_rect()
            textRect.center = (400, 100)
            screen.blit(text, textRect)
            # health = font.render('Health: {}'.format(health_server), True, (255, 255, 255))
            # healthRect = text.get_rect()
            # healthRect.center = (200, 50)
            # screen.blit(health, healthRect)
            hits = event_client.response['hits']
            bullets = event_client.response['gameField']['bullets']
            winner = event_client.response['winners']
            tanks = event_client.response['gameField']['tanks']
            for tank in tanks:
                tank_x = tank['x']
                tank_y = tank['y']
                tank_width = tank['width']
                tank_height = tank['height']
                tank_direction = tank['direction']
                draw_tank(tank_x, tank_y, tank_width, tank_height, tank_direction)
            #     # Not working :(
            #     # draw_tank(**tank)
            for bullet in bullets:
                bullet_x = bullet['x']
                bullet_y = bullet['y']
                bullet_width = bullet['width']
                bullet_height = bullet['height']
                bullet_direction = bullet['direction']
                draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height, bullet_direction)
        except:
            pass
        pygame.display.flip()
    client.connection.close()
    pygame.quit()


client = TankRpcClient()
client.check_server_status()
client.obtain_token('room-6')
# client.turn_tank(client.token, 'RIGHT')
event_client = TankConsumerClient('room-6')
event_client.start()
game_start()

# client.fire_tank(client.token)
