# -*-  coding: utf-8 -*-

import sys
import time
import signal
import threading
from datetime import datetime

from queue import Queue

import click

import arcade
import math
import random

from twisted.internet import protocol, reactor, endpoints, task, threads
from twisted.logger import Logger, globalLogPublisher, FilteringLogObserver, LogLevel, LogLevelFilterPredicate, textFileLogObserver

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data, Bubbles, Bubble, Joycon
import player_model
import bubble_model
import joycon_model

from ringggo_packet import Header, PositionObject, PositionNoti, Packet

from pyjoycon import get_R_id, get_L_id
from rumble import RumbleJoyCon, RumbleData

LOG_LEVELS = dict(
    debug=LogLevel.debug,
    info=LogLevel.info,
    warn=LogLevel.warn,
    error=LogLevel.error,
    critical=LogLevel.critical
)


class Singleton(type):
    __instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self.__instances:
            self.__instances[self] = super().__call__(*args, **kwargs)
        return self.__instances[self]


VENDOR_ID = 1406
PRODUCT_ID_LEFT = 8198
PRODUCT_ID_RIGHT = 8199

class JoyconService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        joycon_r_id = get_R_id()
        if isinstance(joycon_r_id, tuple) and len(joycon_r_id) == 3 and joycon_r_id[0] == VENDOR_ID and joycon_r_id[1] == PRODUCT_ID_RIGHT and joycon_r_id[2]:
            self.joycon_r = RumbleJoyCon(*joycon_r_id) 
            print('[joycon right] connected')
            print(joycon_r_id)
        else:
            self.joycon_r = None
            print('[joycon right] failed')
        joycon_l_id = get_L_id()
        if isinstance(joycon_l_id, tuple) and len(joycon_l_id) == 3 and joycon_l_id[0] == VENDOR_ID and joycon_l_id[1] == PRODUCT_ID_LEFT and joycon_l_id[2]:
            self.joycon_l = RumbleJoyCon(*joycon_l_id) 
            print('[joycon left] connected')
            print(joycon_l_id)
        else:
            self.joycon_l = None
            print('[joycon left] failed')

    def is_connect_right(self):
        if isinstance(self.joycon_r, RumbleJoyCon) and get_R_id() == (self.joycon_r.vendor_id, self.joycon_r.product_id, self.joycon_r.serial):
            return True
        else:
            return False

    def is_connect_left(self):
        if isinstance(self.joycon_l, RumbleJoyCon) and get_L_id() == (self.joycon_l.vendor_id, self.joycon_l.product_id, self.joycon_l.serial):
            return True
        else:
            return False

    def get_info_right(self):
        if self.is_connect_right():
            return {
                'vendor_id': self.joycon_r.vendor_id,
                'product_id': self.joycon_r.product_id,
                'serial': self.joycon_r.serial,
            }
        else:
            return {}

    def get_info_left(self):
        if self.is_connect_left():
            return {
                'vendor_id': self.joycon_l.vendor_id,
                'product_id': self.joycon_l.product_id,
                'serial': self.joycon_l.serial,
            }
        else:
            return {}

    def set_paring_right(self):
        joycon_r_id = get_R_id()
        if joycon_r_id[0]:
            self.joycon_r = RumbleJoyCon(*joycon_r_id) 
            return True
        else:
            return False

    def set_paring_left(self):
        joycon_l_id = get_L_id()
        if joycon_l_id[0]:
            self.joycon_l = RumbleJoyCon(*joycon_l_id) 
            return True
        else:
            return False

    def get_status_right(self):
        if self.is_connect_right():
            return self.joycon_r.get_status()
        else:
            return {}

    def get_status_left(self):
        if self.is_connect_left():
            return self.joycon_l.get_status()
        else:
            return {}

    def set_rumble_right(self, freq,  amp):
        if self.is_connect_right():
            self.joycon_r.enable_vibration()
            rd = RumbleData(freq/2, freq, amp)
            self.joycon_r._send_rumble(rd.GetData())

    def set_rumble_left(self, freq, amp):
        if self.is_connect_left():
            self.joycon_l.enable_vibration()
            rd = RumbleData(freq/2, freq, amp)
            self.joycon_l._send_rumble(rd.GetData())

    def set_rumble_simple_right(self):
        if self.is_connect_right():
            self.joycon_r.enable_vibration()
            self.joycon_r.rumble_simple()

    def set_rumble_simple_left(self):
        if self.is_connect_left():
            self.joycon_l.enable_vibration()
            self.joycon_l.rumble_simple()


ARENA_WIDTH = 1900
ARENA_HEIGHT = 1380

SCREEN_SCALING = 1.0
SCREEN_WIDTH = ARENA_WIDTH * SCREEN_SCALING
SCREEN_HEIGHT = ARENA_HEIGHT * SCREEN_SCALING
SCREEN_TITLE = "Starting Game(by RTLS - RINGGGO)"

SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_COIN = 1.0
# SPRITE_SCALING_COIN = 0.2
COIN_COUNT_MAX = 10
SPRITE_SCALING_SHIP = 1.0

JOYSTICK_NAME = '8BitDo Lite 2'


# --- Explosion Particles Related

# How fast the particle will accelerate down. Make 0 if not desired
PARTICLE_GRAVITY = 0.05

# How fast to fade the particle
PARTICLE_FADE_RATE = 8

# How fast the particle moves. Range is from 2.5 <--> 5 with 2.5 and 2.5 set.
PARTICLE_MIN_SPEED = 2.5
PARTICLE_SPEED_RANGE = 2.5

# How many particles per explosion
PARTICLE_COUNT = 20

# How big the particle
PARTICLE_RADIUS = 12

# Possible particle colors
PARTICLE_SKY_COLORS = [arcade.color.SKY_BLUE,
                       arcade.color.DEEP_SKY_BLUE,
                       arcade.color.SKY_MAGENTA,
                       arcade.color.VIVID_SKY_BLUE,
                       arcade.color.LIGHT_SKY_BLUE]

PARTICLE_GREEN_COLORS = [arcade.color.UFO_GREEN,
                         arcade.color.NEON_GREEN,
                         arcade.color.DEEP_JUNGLE_GREEN,
                         arcade.color.GO_GREEN,
                         arcade.color.LIGHT_GREEN]

# PARTICLE_COLORS = [arcade.color.ALIZARIN_CRIMSON,
#                    arcade.color.COQUELICOT,
#                    arcade.color.LAVA,
#                    arcade.color.KU_CRIMSON,
#                    arcade.color.DARK_TANGERINE]

# Chance we'll flip the texture to white and make it 'sparkle'
PARTICLE_SPARKLE_CHANCE = 0.02

# --- Smoke
# Note: Adding smoke trails makes for a lot of sprites and can slow things
# down. If you want a lot, it will be necessary to move processing to GPU
# using transform feedback. If to slow, just get rid of smoke.

# Start scale of smoke, and how fast is scales up
SMOKE_START_SCALE = 1.0
SMOKE_EXPANSION_RATE = 0.1

# Rate smoke fades, and rises
SMOKE_FADE_RATE = 7
SMOKE_RISE_RATE = 0.5

# Chance we leave smoke trail
SMOKE_CHANCE = 0.25


class Smoke(arcade.SpriteCircle):
    """ This represents a puff of smoke """
    def __init__(self, size):
        super().__init__(size, arcade.color.LIGHT_GRAY, soft=True)
        self.change_y = SMOKE_RISE_RATE
        self.scale = SMOKE_START_SCALE

    def update(self):
        """ Update this particle """
        if self.alpha <= PARTICLE_FADE_RATE:
            # Remove faded out particles
            self.remove_from_sprite_lists()
        else:
            # Update values
            self.alpha -= SMOKE_FADE_RATE
            self.center_x += self.change_x
            self.center_y += self.change_y
            self.scale += SMOKE_EXPANSION_RATE


class Particle(arcade.SpriteCircle):
    """ Explosion particle """
    def __init__(self, my_list, particle_colors):
        # Choose a random color
        color = random.choice(particle_colors)

        # Make the particle
        super().__init__(PARTICLE_RADIUS, color)

        # Track normal particle texture, so we can 'flip' when we sparkle.
        self.normal_texture = self.texture

        # Keep track of the list we are in, so we can add a smoke trail
        self.my_list = my_list

        # Set direction/speed
        speed = random.random() * PARTICLE_SPEED_RANGE + PARTICLE_MIN_SPEED
        direction = random.randrange(360)
        self.change_x = math.sin(math.radians(direction)) * speed
        self.change_y = math.cos(math.radians(direction)) * speed

        # Track original alpha. Used as part of 'sparkle' where we temp set the
        # alpha back to 255
        self.my_alpha = 255

        # What list do we add smoke particles to?
        self.my_list = my_list

    def update(self):
        """ Update the particle """
        if self.my_alpha <= PARTICLE_FADE_RATE:
            # Faded out, remove
            self.remove_from_sprite_lists()
        else:
            # Update
            self.my_alpha -= PARTICLE_FADE_RATE
            self.alpha = self.my_alpha
            self.center_x += self.change_x
            self.center_y += self.change_y
            self.change_y -= PARTICLE_GRAVITY

            # Should we sparkle this?
            if random.random() <= PARTICLE_SPARKLE_CHANCE:
                self.alpha = 255
                self.texture = arcade.make_circle_texture(int(self.width),
                                                          arcade.color.WHITE)
            else:
                self.texture = self.normal_texture

            # Leave a smoke particle?
            if random.random() <= SMOKE_CHANCE:
                smoke = Smoke(5)
                smoke.position = self.position
                self.my_list.append(smoke)


class CrosshairSprite(arcade.Sprite):
    START_XY = (100, 100)

    def __init__(self, filename, sprite_scaling):

        super().__init__(filename, sprite_scaling)

        self.center_x = self.START_XY[0]
        self.center_y = self.START_XY[1]

        self.cur_texture = 0
        self.unlock_textures = [
            arcade.load_texture('./resources/images/crosshair137.png'),
            arcade.load_texture('./resources/images/crosshair138.png')
        ]
        self.lock_textures = [
            arcade.load_texture('./resources/images/crosshair026.png'),
            arcade.load_texture('./resources/images/crosshair027.png')
        ]
        self.move_textures = self.unlock_textures
        self.texture = self.move_textures[self.cur_texture]

    def update_animation(self, delta_time: float = 1 / 60):
        if self.cur_texture <= 30:        
            self.texture = self.move_textures[0]
        elif self.cur_texture <=60:
            self.texture = self.move_textures[1]
        else:
            self.cur_texture = 0
        self.cur_texture += 1

    def update(self):
        self.update_animation()
        
    def unlock(self):
        self.move_textures = self.unlock_textures
        # self.texture = self.move_textures[self.cur_texture%2]

    def lock(self):
        self.move_textures = self.lock_textures
        # self.texture = self.move_textures[self.cur_texture%2]


class PlayerSprite(arcade.Sprite):
    START_X = 100
    START_Y = 100


    def __init__(self, filename, sprite_scaling):

        super().__init__(filename, sprite_scaling)

        self.center_x = self.START_X
        self.center_y = self.START_Y

        self.cur_texture = 0
        self.move_textures = [
            arcade.load_texture('./resources/images/robot_idle.png'),
            arcade.load_texture('./resources/images/robot_walk0.png'),
            arcade.load_texture('./resources/images/robot_walk1.png'),
            arcade.load_texture('./resources/images/robot_walk2.png'),
            arcade.load_texture('./resources/images/robot_walk3.png'),
            arcade.load_texture('./resources/images/robot_walk4.png'),
            arcade.load_texture('./resources/images/robot_walk5.png'),
            arcade.load_texture('./resources/images/robot_walk6.png'),
            arcade.load_texture('./resources/images/robot_walk7.png')
        ]
        self.texture = self.move_textures[self.cur_texture]

    def update_animation(self, delta_time: float = 1 / 60):
            if self.cur_texture <= 6:        
                self.texture = self.move_textures[0]
            elif self.cur_texture <=12:
                self.texture = self.move_textures[1]
            elif self.cur_texture <=18:
                self.texture = self.move_textures[2]
            elif self.cur_texture <=24:
                self.texture = self.move_textures[3]
            elif self.cur_texture <=30:
                self.texture = self.move_textures[4]
            elif self.cur_texture <=36:
                self.texture = self.move_textures[5]
            elif self.cur_texture <=42:
                self.texture = self.move_textures[6]
            elif self.cur_texture <=48:
                self.texture = self.move_textures[7]
            elif self.cur_texture <=54:
                self.texture = self.move_textures[8]
            else:
                self.cur_texture = 0
            self.cur_texture += 1

    def update(self):
        self.update_animation()

class Ship(arcade.Sprite):

    def __init__(self, filename, sprite_scaling):

        super().__init__(filename, sprite_scaling)


class Coin(arcade.Sprite):

    def __init__(self, uid, _type, sprite_scaling):

        super().__init__('./resources/images/slimeBlue.png', sprite_scaling)

        self.uid = uid

        self.change_x = 0
        self.change_y = 0

        self.cur_texture = 0

        self._type = _type
        if self._type == 0:
            self.move_textures = [
                arcade.load_texture('./resources/images/slimeBlue.png'),
                arcade.load_texture('./resources/images/slimeBlue_move.png')
            ]
        elif self._type == 1:
            self.move_textures = [
                arcade.load_texture('./resources/images/slimeGreen.png'),
                arcade.load_texture('./resources/images/slimeGreen_move.png')
            ]
        self.texture = self.move_textures[self.cur_texture]
    
    def update_animation(self, delta_time: float = 1 / 60):
        if self.cur_texture <= 15:        
            self.texture = self.move_textures[0]
        elif self.cur_texture <=30:
            self.texture = self.move_textures[1]
        elif self.cur_texture <=45:
            self.texture = self.move_textures[0]
        elif self.cur_texture <=60:
            self.texture = self.move_textures[1]
        else:
            self.cur_texture = 0
        self.cur_texture += 1

    def update(self):
        self.update_animation()

        # Move the coin
        self.center_x += self.change_x
        self.center_y += self.change_y

        # If we are out-of-bounds, then 'bounce'
        if self.left < 0:
            self.change_x *= -1

        if self.right > SCREEN_WIDTH:
            self.change_x *= -1

        if self.bottom < 0:
            self.change_y *= -1

        if self.top > SCREEN_HEIGHT:
            self.change_y *= -1


class FlyingSprite(arcade.Sprite):
    '''Base class for all flying sprites
    Flying sprites include meteors
    '''

    def update(self):
        '''Update the position of the sprite
        When it moves off screen to the left, remove it
        '''

        # Move the sprite
        super().update()

        # Remove if off the screen
        if self.right < 0:
            self.remove_from_sprite_lists()


class Game(arcade.Window):
    ''' Our custom Window Class '''
    MOVEMENT_SPEED = 10
    DEAD_ZONE = 0.05

    def __init__(self):
        ''' Initializer '''
        # Call the parent class initializer
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Sounds
        self.background_music = None
        self.shoot_sound = None
        self.shoot_success_sound = None
        self.shoot_fail_sound = None

        # Variables that will hold sprite lists
        self.all_sprites_list = None
        self.coin_list = None
        self.global_coin_count = 0

        # Set up the player info
        self.player_sprite = None
        self.score = 0
        self.hit_ringggo = 0

        self.ship_sprite_list = None

        self.explosions_list = None

        self.meteors_list = None

        self.hit_check_frame = 0

        # Don't show the mouse cursor
        self.set_mouse_visible(False)

        self.joystick = None
        joysticks = arcade.get_joysticks()
        if joysticks:
            for j in joysticks:
                if j.device.name == JOYSTICK_NAME:
                    self.joystick = j
                    self.joystick.open()
                    self.joystick.push_handlers(self)
        else:
            print('There are no joysticks, plug in a joystick and run again.')
            self.joystick = None

        arcade.set_background_color(arcade.color.SPACE_CADET)

    def add_meteor(self, delta_time: float):
        '''Adds a new meteor to the screen

        Arguments:
            delta_time {float} -- How much time has passed since the last call
        '''

        METEOR_LIST = [
            './resources/images/meteorGrey_big1.png',
            './resources/images/meteorGrey_big2.png',
            './resources/images/meteorGrey_big3.png',
            './resources/images/meteorGrey_big4.png',
            './resources/images/meteorGrey_med1.png',
            './resources/images/meteorGrey_med2.png',
            './resources/images/meteorGrey_small1.png',
            './resources/images/meteorGrey_small1.png',
            './resources/images/meteorGrey_tiny1.png',
            './resources/images/meteorGrey_tiny2.png'
        ]

        # First, create the new meteor sprite
        meteor = FlyingSprite(METEOR_LIST[random.randrange(10)], 1.5)

        # Set its position to a random height and off screen right
        meteor.left = random.randint(self.width, self.width + 80)
        meteor.top = random.randint(10, self.height - 10)

        # Set its speed to a random speed heading left
        meteor.velocity = (random.randint(-5, -2), 0)

        # Add it to the meteor list
        self.meteors_list.append(meteor)
        self.all_sprites_list.append(meteor)

    def generate_coin(self, coin_count, _type=0, x=0, y=0):
        ''' create the coints '''
        for i in range(coin_count):

            # Create the coin instance
            # Coin image from kenney.nl
            coin = Coin(self.global_coin_count, _type, SPRITE_SCALING_COIN)
            self.global_coin_count += 1
            # Position the coin
            if x > 0 and y > 0:
                coin.center_x = x
                coin.center_y = y
            else:
                coin.center_x = random.randrange(SCREEN_WIDTH)
                coin.center_y = random.randrange(SCREEN_HEIGHT)
            coin.change_x = random.randrange(-1, 2)
            coin.change_y = random.randrange(-1, 2)

            # Add the coin to the lists
            self.all_sprites_list.append(coin)
            self.coin_list.append(coin)

    def sync_ship(self):
        ''' synchronize position of ringggo'''
        self.ship_sprite_list.clear()
        for k, v in RtlsService().cars.items():
            ship = Ship('./resources/images/shipGreen_manned.png', SPRITE_SCALING_SHIP)
            ship.center_x = v['x']*SCREEN_SCALING
            ship.center_y = v['y']*SCREEN_SCALING
            self.ship_sprite_list.append(ship)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.all_sprites_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.ship_sprite_list = arcade.SpriteList()
        self.explosions_list = arcade.SpriteList()
        self.meteors_list = arcade.SpriteList()

        # Score
        self.score = 0
        self.hit_ringggo = 0

        # Sound
        # self.bgm = arcade.Sound(':resources:music/funkyrobot.mp3')
        # self.bgm.play(volume=1.0, pan=0.0, loop=False, speed=1.0)

        # Set up the player
        # Character image from kenney.nl
        self.player_sprite = CrosshairSprite('./resources/images/crosshair137.png', SPRITE_SCALING_PLAYER)
        # self.player_sprite = PlayerSprite('./resources/images/robot_idle.png', SPRITE_SCALING_PLAYER)
        self.all_sprites_list.append(self.player_sprite)

        # Create the coins
        # self.generate_coin(COIN_COUNT_MAX)

        # Sync ringggo car
        self.sync_ship()

        # Spawn a new meteor every second
        arcade.schedule(self.add_meteor, 2.0)

        # Load sounds
        self.background_music = arcade.load_sound('./resources/music/funkyrobot.wav')
        self.shoot_sound = arcade.load_sound('./resources/sounds/upgrade1.wav')
        self.shoot_success_sound = arcade.load_sound('./resources/sounds/upgrade3.wav')
        self.shoot_fail_sound = arcade.load_sound('./resources/sounds/upgrade2.wav')

        # Play BGM
        arcade.play_sound(self.background_music, volume=1.5, looping=True)

    def shoot(self):
        hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)
        if hit_list:
            for coin in hit_list:
                # Make an explosion
                for i in range(PARTICLE_COUNT):
                    if coin._type == 0:
                        particle = Particle(self.explosions_list, PARTICLE_SKY_COLORS)
                    elif coin._type == 1:
                        particle = Particle(self.explosions_list, PARTICLE_GREEN_COLORS)
                    particle.position = coin.position
                    self.explosions_list.append(particle)
                smoke = Smoke(50)
                smoke.position = coin.position
                self.explosions_list.append(smoke)
                if coin._type == 0:
                    self.score += 50
                elif coin._type == 1:
                    self.score += 100
                coin.remove_from_sprite_lists()
                arcade.play_sound(self.shoot_success_sound, volume=1.5)
        else:
            arcade.play_sound(self.shoot_fail_sound, volume=1.5)

    def on_draw(self):
        """ Draw everything """
        self.clear()
        self.ship_sprite_list.draw()
        self.all_sprites_list.draw()
        self.player_sprite.draw()
        self.explosions_list.draw()

        # Put the text on the screen.
        output = 'Score: {:,}'.format(self.score)
        arcade.draw_text(output, 10, ARENA_HEIGHT-40, arcade.color.WHITE, 34)
        output = f"RINGGGO: {len(self.ship_sprite_list)}"
        arcade.draw_text(output, 10, ARENA_HEIGHT-60, arcade.color.BLUE, 14)
        output = f"RINGGGO hit: {self.hit_ringggo}"
        arcade.draw_text(output, 10, ARENA_HEIGHT-80, arcade.color.RED, 14)
        output = f"Bubble: {len(self.coin_list)}"
        arcade.draw_text(output, 10, ARENA_HEIGHT-100, arcade.color.GREEN, 14)

        output = f"Width x Height: {ARENA_WIDTH} x {ARENA_HEIGHT}"
        arcade.draw_text(output, ARENA_WIDTH-240, ARENA_HEIGHT-20, arcade.color.WHITE, 14)

        output = f"Start X,Y: (0, 0)"
        arcade.draw_text(output, 10, 20, arcade.color.WHITE, 14)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Handle Mouse Motion """

        # Move the center of the player sprite to match the mouse x, y
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        print(x, y, button, modifiers)
        return super().on_mouse_press(x, y, button, modifiers)
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        print(x, y, button, modifiers)
        self.shoot()
        return super().on_mouse_release(x, y, button, modifiers)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.all_sprites_list.update()
        self.sync_ship()
        self.ship_sprite_list.update()

        self.explosions_list.update()

        if not GameService().q.empty():
            uid = GameService().q.get()
            for c in self.coin_list:
                if uid == c.uid:
                    c.remove_from_sprite_lists()
                    print('removed bubble uid: {}'.format(uid))
                else:
                    print('invalid bubble uid: {}'.format(uid))
        GameService().clear()
        for c in self.coin_list:
            GameService().bubbles[c.uid] = dict(x=c.center_x, y=c.center_y, _type=c._type)

        # Generate a list of all sprites that collided with the player.
        lock_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)
        if lock_list:
            self.player_sprite.lock()
        else:
            self.player_sprite.unlock()
        # Loop through each colliding sprite, remove it, and add to the score.
        # for coin in lock_list:
        #     coin.remove_from_sprite_lists()
        #     self.score += 1
        
        if self.hit_check_frame > 60:
            for r in self.ship_sprite_list:
                ship_hit_list = arcade.check_for_collision_with_list(r, self.ship_sprite_list)
                for hit in ship_hit_list:
                    self.hit_ringggo += 1
                    if len(self.coin_list) <= COIN_COUNT_MAX:
                        self.generate_coin(1, 1, hit.center_x, hit.center_y)
            if len(self.coin_list) <= COIN_COUNT_MAX:
                self.generate_coin(2, 0)
            self.hit_check_frame = 0
        else:
            self.hit_check_frame += 1
        
        if self.joystick:
            self.player_sprite.change_x = self.joystick.x * self.MOVEMENT_SPEED
            if abs(self.player_sprite.change_x) < self.DEAD_ZONE:
                self.player_sprite.change_x = 0
            self.player_sprite.change_y = -self.joystick.y * self.MOVEMENT_SPEED
            if abs(self.player_sprite.change_y) < self.DEAD_ZONE:
                self.player_sprite.change_y = 0
        
        self.player_sprite.center_x += self.player_sprite.change_x
        self.player_sprite.center_y += self.player_sprite.change_y

    def on_joybutton_press(self, _joystick, button):
        if button == 9:
            arcade.play_sound(self.shoot_sound, volume=1.0)
        print('Button {} down'.format(button))

    def on_joybutton_release(self, _joystick, button):
        if button == 9:
            self.shoot()
        print('Button {} up'.format(button))

    def on_joyhat_motion(self, _joystick, hat_x, hat_y):
        print('Hat ({}, {})'.format(hat_x, hat_y))


class GameService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.bubbles = dict()
        self.q = Queue(32)
    
    def get_bubbles(self) -> bubble_model.Bubbles:
        bs_obj = bubble_model.Bubbles()
        for k, v in self.bubbles.items():
            vec = bubble_model.Vec2(x=v['x'], y=v['y'])
            bm = bubble_model.Bubble(
                uid=k,
                pos_cur=vec,
                pos_target=vec,
                speed=0.0,
                type=v['_type'])
            bs_obj.bubbles.append(bm)
        return bs_obj
    
    def clear(self):
        self.bubbles.clear()


class RtlsService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.cars = dict()
    
    def get_bubbles(self) -> bubble_model.Bubbles:
        bs_obj = bubble_model.Bubbles()
        for k, v in self.cars.items():
            vec = bubble_model.Vec2(x=v['x'], y=v['y'])
            bm = bubble_model.Bubble(
                uid=k,
                pos_cur=vec,
                pos_target=vec,
                speed=0.0,
                type=bubble_model.BubbleType.event)
            bs_obj.bubbles.append(bm)
        return bs_obj


class RtlsProtocol(protocol.DatagramProtocol):
    log = Logger()

    def __init__(self, host, port):
        self.host = host
        self.port = port
        RtlsService()

    def startProtocol(self):
        self.log.info('New connection')
        self.transport.connect(self.host, self.port)
        self.log.info('connected')

        packet = Packet(
            sender=Header.SENDER_ADMIN,
            code=Header.PK_POSITION_LISTEN)
        self.transport.write(packet.to_bytes())

    def stopProtocol(self):
        self.log.info('Disconnected')

    def datagramReceived(self, data, addr):
        self.log.debug('received {} from {}'.format(data, addr))
        p = Packet.from_bytes(data)
        self.log.debug('header code: {}'.format(p.header.code))
        for c in p.body:
            RtlsService().cars[c.object_number] = dict(
                x=c.position_noti.position_x,
                y=c.position_noti.position_y
            )
            self.log.debug('{}, {}, {}'.format(c.object_number, c.position_noti.position_x, c.position_noti.position_y))
        self.log.debug('car list: {cars}'.format(cars=RtlsService().cars))
        # packet = Packet(
        #     sender=Header.SENDER_ADMIN,
        #     code=Header.PK_POSITION_LISTEN_STOP)
        # self.transport.write(packet.to_bytes())

    def connectionRefused(self):
        self.log.info('No one listening')


class State(object):
    welcome = 0
    connect = 1

class Echo(protocol.Protocol):
    log = Logger()

    def __init__(self, users, players, bubbles):
        self.users = users
        self.user = None
        self.players = players
        self.bubbles = bubbles
        self.state = State.welcome

    def connectionMade(self):
        self.log.info('New connection')
        req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
        self.log.debug('Request: {}'.format(str(req)))
        self.transport.write(bytes(req))

    def connectionLost(self, reason):
        self.log.info(str(reason))
        if self.user.uid in self.users:
            del self.users[self.user.uid]
            for p in self.players.players:
                if p.uid == self.user.uid:
                    self.players.players.remove(p)
                    self.log.info('connection lost: {}'.format(self.user.username))
                    break

    def dataReceived(self, buf):
        if self.user:
            self.log.info('{} {} Receive Data'.format(self.user.uid, self.user.username))
        else:
            self.log.info('Receive Data')
        self.log.info('Bytes Length: {}'.format(len(buf)))
        self.log.debug('Bytes: {}'.format(str(buf)))
        pac_size = int.from_bytes(buf[0:2], 'big')
        if len(buf) == pac_size:
            self.log.info('valid packet size ===  header: {}, packet: {}'.format(pac_size, len(buf)))
            pac = buf[2:]
        elif len(buf) > pac_size:
            self.log.warn('!!! large packet size <<< header: {}, packet: {}'.format(pac_size, len(buf)))
            pac = buf[:pac_size][2:]
        else:
            self.log.warn('!!! small packet size >>> header: {}, packet: {}'.format(pac_size, len(buf)))
            return
        if self.state == State.welcome:
            self._handle_welcome(pac)
        elif self.state == State.connect:
            self._handle_connect(pac)
        else:
            self.log.warn('wrong state')
    
    def _handle_welcome(self, buf):
        res= Response.Response.GetRootAsResponse(buf, 0)
        self.log.debug('Timestamp: {}'.format(str(res.Timestamp())))
        self.log.debug('Command: {}'.format(str(res.Command())))
        self.log.debug('ErrorCode: {}'.format(str(res.ErrorCode())))
        self.log.debug('Data: {}'.format(str(res.Data())))
        if res.Command() == Command.Command.welcome:
        #if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
            player = Player.Player()
            player.Init(res.Data().Bytes, res.Data().Pos)
            self.user = player_model.Player(
                uid=player.Uid(),
                username=player.Username(),
                image_url=player.ImageUrl(),
                score=player.Score(),
                status=player.Status())
            self.log.info(str(self.user))
            self.users[self.user.uid] = self
            self.players.players.append(self.user)
            self.state = State.connect
            self.log.debug(str(self.users))
            self.log.debug(str(self.players))
        else:
            self.log.warn('Error command')

    def _handle_connect(self, buf):
        req = Request.Request.GetRootAsRequest(buf, 0)
        self.log.debug('Handler: {}, {}, {}, {}'.format(str(req.Timestamp()), str(req.Command()), str(req.Sender()), str(req.Data())))
        if req.Command() == Command.Command.ping:
            self.log.info('request ping command OK')
            res = bytearray()
        elif req.Command() == Command.Command.bubble_get and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_get command OK')
            bubble = Bubble.Bubble()
            bubble.Init(req.Data().Bytes, req.Data().Pos)
            GameService().q.put(bubble.Uid())
            res = response_packet_builder(Command.Command.bubble_get, error_code=0)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.bubble_status and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_status command OK')
            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=GameService().get_bubbles().bubbles)
            # res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=self.bubbles.bubbles)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_get and req.Sender() == Sender.Sender.client:
            self.log.info('request player_get command OK')
            res = response_packet_builder(Command.Command.player_get, error_code=0, data=self.user)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_status and req.Sender() == Sender.Sender.client:
            self.log.info('request player_status command OK')
            res = response_packet_builder(Command.Command.player_status, error_code=0, data=self.players.players)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_ready and req.Sender() == Sender.Sender.client:
            self.log.info('request game_ready command OK')
            self.user.status = player_model.PlayerStatus.ready
            for p in self.players.players:
                if p.uid == self.user.uid:
                    p.status = player_model.PlayerStatus.ready
            res = response_packet_builder(Command.Command.game_ready, error_code=0) 
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_start and req.Sender() == Sender.Sender.client:
            self.log.info('request game_start command OK')
            self.user.status = player_model.PlayerStatus.game
            for p in self.players.players:
                p.status = player_model.PlayerStatus.game
            res = response_packet_builder(Command.Command.game_start, error_code=0) 
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_finish and req.Sender() == Sender.Sender.client:
            self.log.info('request game_finish command OK')
            self.user.status = player_model.PlayerStatus.idle
            for p in self.players.players:
                p.status = player_model.PlayerStatus.idle
            res = response_packet_builder(Command.Command.game_finish, error_code=0) 
            self.transport.write(bytes(res))
        else:
            self.log.warn('request wrong command')
        self.log.info('response lenth: {}'.format(len(res)))
        self.log.debug('response data: {}'.format(str(res)))

        # message = '{}: {}'.format(self.name, data)
        # print(message) 
        # for name, protocol in self.users.items():
        #     if protocol != self:
        #         protocol.transport.write(message.encode('utf-8'))


class EchoFactory(protocol.ServerFactory):
    log = Logger()
    def __init__(self):
        self.users = {}
        self.players = player_model.Players()
        self.bubbles = generate_bubbles()

    def buildProtocol(self, addr):
        self.log.info(str(addr))
        return Echo(self.users, self.players, self.bubbles)
    
    def startFactory(self):
        self.log.info('start factory')

    def stopFactory(self):
        self.log.info('stop factory')

class ScheduleTask:
    log = Logger()

    BULLET_MAX = 5
    FRAME = 60
    GYRO_Y_THRESHOLD = -5000
    RELOAD_TIME_OFFSET = 1.5

    prev_zr = 0
    reload_time = time.time()

    @classmethod
    def run_ping_task(cls, users, players, bubbles):
        cls.log.info('ping task: {}'.format(datetime.now()))
        cls.log.info(str(players))
        for u in users.values():
            req = request_packet_builder(Command.Command.ping, Sender.Sender.server)
            cls.log.debug(str(req))
            u.transport.write(bytes(req))

            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=GameService().get_bubbles().bubbles)
            u.transport.write(bytes(res))


    @classmethod
    def run_joycon_task(cls, users):
        cls.log.debug('joycon task: {}'.format(datetime.now()))
        left = JoyconService().get_status_left()
        right = JoyconService().get_status_right()
        if left and right:
            joycon = joycon_model.Joycon(
                right_y=right['buttons']['right']['y'],
                right_x=right['buttons']['right']['x'],
                right_a=right['buttons']['right']['a'],
                right_b=right['buttons']['right']['b'],
                right_r=right['buttons']['right']['r'],
                right_zr=right['buttons']['right']['zr'],
                right_horizontal=right['analog-sticks']['right']['horizontal'],
                right_vertical=right['analog-sticks']['right']['vertical'],
                right_accel_x=right['accel']['x'],
                right_accel_y=right['accel']['y'],
                right_accel_z=right['accel']['z'],
                right_gyro_x=right['gyro']['x'],
                right_gyro_y=right['gyro']['y'],
                right_gyro_z=right['gyro']['z'],
                right_battery_charging=right['battery']['charging'],
                right_battery_level=right['battery']['level'],
                right_home=right['buttons']['shared']['home'],

                left_down=left['buttons']['left']['down'],
                left_up=left['buttons']['left']['up'],
                left_right=left['buttons']['left']['right'],
                left_left=left['buttons']['left']['left'],
                left_l=left['buttons']['left']['l'],
                left_zl=left['buttons']['left']['zl'],
                left_horizontal=left['analog-sticks']['left']['horizontal'],
                left_vertical=left['analog-sticks']['left']['vertical'],
                left_accel_x=left['accel']['x'],
                left_accel_y=left['accel']['y'],
                left_accel_z=left['accel']['z'],
                left_gyro_x=left['gyro']['x'],
                left_gyro_y=left['gyro']['y'],
                left_gyro_z=left['gyro']['z'],
                left_battery_charging=left['battery']['charging'],
                left_battery_level=left['battery']['level']
            )
            for u in users.values():
                req = request_packet_builder(Command.Command.joycon, Sender.Sender.server, joycon)
                cls.log.debug(str(req))
                u.transport.write(bytes(req))
        else:
            cls.log.error('check paring joycon left: {}, right: {}'.format(left, right))

    @classmethod
    def run_joycon_event_task(cls, users):
        cls.log.debug('joycon event task: {}'.format(datetime.now()))
        JoyconService()
        left = JoyconService().get_status_left()
        right = JoyconService().get_status_right()
        if left and right:
            if right['gyro']['y'] < cls.GYRO_Y_THRESHOLD and (time.time() - cls.reload_time) > cls.RELOAD_TIME_OFFSET:
                cls.reload_time = time.time()
                cls.log.info('reload event')
                JoyconService().set_rumble_right(1.2, 0.3)
                JoyconService().set_rumble_left(0.5, 0.5)
                for u in users.values():
                    req = request_packet_builder(Command.Command.reload, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            if right['buttons']['right']['zr'] == 1 and cls.prev_zr == 0:
                cls.log.info('shoot event')
                JoyconService().set_rumble_right(1.2, 0.3)
                JoyconService().set_rumble_left(0.5, 0.5)
                for u in users.values():
                    req = request_packet_builder(Command.Command.shoot, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            if right['buttons']['right']['zr'] == 0 and cls.prev_zr == 1:
                cls.log.info('shoot release event')
                for u in users.values():
                    req = request_packet_builder(Command.Command.shoot_release, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            cls.prev_zr = right['buttons']['right']['zr']
        else:
            print('disconnected')

    @classmethod
    def cbLoopDone(cls, result):
        cls.log.info(result)

    @classmethod
    def ebLoopFailed(cls, failure):
        cls.log.error(failure.getBriefTraceback())

BUBBLE_COUNT = 10
BUBBLE_POS_OFFSET = 140

def generate_bubbles() -> bubble_model.Bubbles:
    bs_obj = bubble_model.Bubbles()
    for i in range(BUBBLE_COUNT):
        vec = bubble_model.Vec2(x=i*BUBBLE_POS_OFFSET, y=0)
        bm = bubble_model.Bubble(
            uid=i,
            pos_cur=vec,
            pos_target=vec,
            speed=0.0,
            type=bubble_model.BubbleType.normal)
        bs_obj.bubbles.append(bm)
    return bs_obj

@click.command()
@click.option('--port', default=1234, type=click.INT, required=True, help='set port (default: 1234)')
@click.option('--ping', default=0.0, type=click.FLOAT, help='set interval of ping (default: 0.0 seconds)')
@click.option('--log-level', default='info', type=click.Choice(['debug', 'info', 'warn', 'error', 'critical'], case_sensitive=False), help='set log level (default: info)')
@click.option('--rtls', default='192.168.40.254:9999', type=click.STRING, required=True, help='set rtls host:port(default: 192.168.40.254:9999)')
@click.option('--joycon', is_flag=True, help='get status of joycon(left/right)')
def main(port, ping, log_level, rtls, joycon):
    log = Logger('MainThread')
    predicate = LogLevelFilterPredicate(defaultLogLevel=LOG_LEVELS.get(log_level))
    observer = FilteringLogObserver(textFileLogObserver(outFile=sys.stdout), [predicate])
    observer._encoding = 'utf-8'
    globalLogPublisher.addObserver(observer)

    ep = endpoints.TCP4ServerEndpoint(reactor, port)
    ef = EchoFactory()
    ep.listen(ef)

    if ping:
        loop_ping = task.LoopingCall(ScheduleTask.run_ping_task, ef.users, ef.players, ef.bubbles)
        loop_ping_deferred = loop_ping.start(ping, False)
        loop_ping_deferred.addCallback(ScheduleTask.cbLoopDone)
        loop_ping_deferred.addErrback(ScheduleTask.ebLoopFailed)

    if joycon:
        loop_joycon = task.LoopingCall(ScheduleTask.run_joycon_task, ef.users)
        loop_joycon_deferred = loop_joycon.start(0.1, False)
        loop_joycon_deferred.addCallback(ScheduleTask.cbLoopDone)
        loop_joycon_deferred.addErrback(ScheduleTask.ebLoopFailed)

    loop_joycon_event = task.LoopingCall(ScheduleTask.run_joycon_event_task, ef.users)
    loop_joycon_event_deferred = loop_joycon_event.start(0.1, False)
    loop_joycon_event_deferred.addCallback(ScheduleTask.cbLoopDone)
    loop_joycon_event_deferred.addErrback(ScheduleTask.ebLoopFailed)

    log.info('Let\'s go ANTIFRAGILE')
    rhost, rport = rtls.split(':')
    reactor.listenUDP(0, RtlsProtocol(rhost, int(rport)))

    def shutdown_handler(_=None, __=None):
        arcade.exit()
        reactor.callFromThread(reactor.stop)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    threading.Thread(target=reactor.run, args=(False,)).start()

    GameService()

    game = Game()
    game.center_window()
    game.setup()
    arcade.run()


if __name__ == '__main__':
    main()
