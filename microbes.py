#! /usr/bin/env python
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program. If not, see http://www.gnu.org/licenses/.

#Created for Ludum Dare 27, 2013.
#Wesley Werner 

import os
import math
import pickle
from random import randint
from random import choice
import pygame
from pygame.locals import *

MUSIC = True
FPS = 30
ANIMATE_DELAY = 1000
ONE_SECOND = 1000

WHITE = (255, 255, 255)
GREEN = (107, 255, 99)
RED = (255, 101, 132)
MAGENTA = (255, 0, 255)
PALE_BLUE = (22, 42, 55)
LITE_BLUE = (148, 196, 211)
YELLOW = (223, 229, 146)

class Microbe(pygame.sprite.Sprite):
    def __init__(self, name):
        super(Microbe, self).__init__()
        self.name = name
        self.angle = 0.0
        self.scale = (0, 0)
        self.images = []
        self.frame = 0
        self.image = None
        self.rect = None
        self.draw_rect = None
        self.collide_rect = None
        self.speed = 0
        self.isfood = False
        self.can_collide = False
        self.scale_mode = 1
        self.alive = True
        self.life_count = 10
        self.draw_healthbar = False
        self.remove_sprite = False
        self.indicator_color = (0, 0, 0)
        self.kills = 0
        self.kill_turn = 0

    def load_frames(self, source, source_rect, frames):
        for i in range(0, frames):
            self.images.append(source.subsurface(source_rect.move(i * source_rect.width, 0)))
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.collide_rect = self.rect.inflate(-16, -16)
        self.draw_rect = self.rect.copy()

    def update(self):
        self.image = pygame.transform.rotate(self.images[self.frame], self.angle)
        if self.scale_mode != 0:
            # reset scale mode
            if self.scale_mode == -1 and self.scale == (0, 0):
                self.scale_mode = 0
                self.remove_sprite = True
            elif self.scale_mode == 1 and self.scale == self.rect.size:
                self.scale_mode = 0
            self.scale = (self.scale[0] + (2 * self.scale_mode), self.scale[1] + (2 * self.scale_mode))
            self.image = pygame.transform.scale(self.image, self.scale)
        self.can_collide = self.scale == self.rect.size
        self.draw_rect = self.image.get_rect()
        self.draw_rect.center = self.rect.center
    
    def animate(self):
        if self.frame < len(self.images) - 1:
            self.frame +=1
        else:
            self.frame = 0
    
    def draw(self, target, draw_indicator=False):
        target.blit(self.image, self.draw_rect)
        if draw_indicator:
            #pygame.draw.rect(target, self.indicator_color, self.rect, 1)
            font = pygame.font.Font(None, 18)
            pix = font.render(self.name, False, self.indicator_color, MAGENTA)
            pix.set_colorkey(MAGENTA)
            target.blit(pix, self.rect.move(0, -16))
        if self.draw_healthbar and self.alive:
            pygame.draw.rect(
                target, 
                self.indicator_color,
                Rect(
                    self.rect.x, 
                    self.rect.y + self.rect.height + 8, 
                    self.rect.width * (float(self.life_count) / 10), 
                    3),
                1)

    def turnate(self, amount=20.0):
        self.angle = (self.angle + amount) % 360

    def travelate(self, acceleration, boundary):
        # accelerate or decelerate
        if acceleration:
            self.speed = clamp(self.speed + acceleration, 0, 10)
        elif self.speed > 0:
            self.speed -= 1
        # move towards angle at speed
        if self.speed > 0:
            x2 = math.cos(math.radians(-self.angle)) * self.speed
            y2 = math.sin(math.radians(-self.angle)) * self.speed
            self.rect.x += x2
            self.rect.y += y2
        # wrap around the canvas
        if boundary:
            if self.rect.x > boundary.width:
                self.rect.x = 0
            if self.rect.x < 0:
                self.rect.x = boundary.width
            if self.rect.y > boundary.height:
                self.rect.y = 0
            if self.rect.y < 0:
                self.rect.y = boundary.height
        # close touch
        self.collide_rect.center = self.rect.center

    def destroy(self):
        self.alive = False
        self.scale_mode = -1
    
    def die_slowly(self):
        self.take_damage(1)
    
    def take_damage(self, amount=2):
        if self.alive:
            self.life_count -= amount
            print('%s has %s life left' % (self.name, self.life_count))
            if self.life_count < 1:
                self.destroy()
        
    def heal(self):
        print('%s heals' % self.name)
        self.life_count = clamp(self.life_count + 5, 0, 10)
    
    def add_kill(self):
        self.kills += 1

class PingEffect(pygame.sprite.Sprite):
    def __init__(self, position, color, size, fill):
        super(PingEffect, self).__init__()
        self.rect = Rect(position, (0, 0))
        self.lifetime = size
        self.radius = 1
        self.color = color
        self.fill = fill

    def tick(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def update(self):
        self.radius += 1
    
    def draw(self, target):
        pygame.draw.circle(target, self.color, self.rect.center, self.radius, self.fill)

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def save_scores(score_card):
    jar = pickle.Pickler(open('scores', 'w'))
    jar.dump(score_card)
    jar = None

def load_scores():
    if os.path.exists('scores'):
        jar = pickle.Unpickler(open('scores', 'r'))
        score_card = jar.load()
        jar = None
        return score_card
    else:
        return [
                ('squigly', 90), ('spikey', 80), ('feebly', 70),
                ('bulby', 60), ('flatty', 50), ('doggy', 40),
                ('fishy', 30), ('algy', 20), ('wezley', 10)
                ]

play_area = Rect(0, 0, 600, 600)
result = pygame.init()
screen = pygame.display.set_mode(play_area.size)
clock = pygame.time.Clock()
last_animation_tick = 0.0
last_life_tick = 0.0
running = True
in_menu = True
turn = 0

image_map = pygame.image.load('tiles.png').convert()
image_map.set_colorkey(MAGENTA)
help_image = pygame.image.load('help.png').convert()
help_image.set_colorkey(MAGENTA)
background = image_map.subsurface((128, 64, 32, 32))
background = pygame.transform.scale(background, play_area.size)
expired_image = image_map.subsurface(128, 96, 425, 64)

if MUSIC:
    pygame.mixer.music.load('darknet2.xm')
    pygame.mixer.music.play(-1)

# amount, source loc, frames, is food
microbe_types = {
    'squigly': ((32, 128), 2, True),
    'spikey': ((32, 160), 2, False),
    'feebly': ((32, 192), 2, False),
    'bulby': ((32, 224), 1, False),
    'flatty': ((32, 256), 2, True),
    'doggy': ((32, 288), 2, False),
    'fishy': ((32, 320), 2, True),
    'algy': ((32, 352), 1, True),
    'sushi': ((32, 384), 2, True),
    'fractey': ((32, 416), 1, False),
    'crystley': ((32, 448), 1, False),
    'pulsey': ((32, 480), 2, True),
}

def spawn(amount):
    menagerie = []
    for amt in range(0, amount):
        miccy = choice(microbe_types.keys())
        data = microbe_types[miccy]
        evilution = Microbe(miccy)
        maploc = Rect(data[0], (32, 32))
        evilution.load_frames(image_map, maploc, data[1])
        evilution.rect.x = randint(1, play_area.width)
        evilution.rect.y = randint(1, play_area.height)
        # foodies?
        if data[2]:
            evilution.indicator_color = GREEN
            evilution.isfood = True
        else:
            evilution.indicator_color = RED
        menagerie.append(evilution)
    return menagerie

def draw_score_card(score_card):
    font = pygame.font.Font(None, 24)
    score_list = []
    for score in score_card:
        score_list.append(font.render(
                str(score[1]) + ': ' + score[0],
                False, 
                WHITE,
                MAGENTA)
                )
    total_height = sum([i.get_height() for i in score_list])
    scores_image = pygame.Surface((200, total_height))
    scores_image.set_colorkey(MAGENTA)
    scores_image.fill(MAGENTA)
    y_pos = 0
    for pix in score_list:
        scores_image.blit(pix, (0, y_pos))
        y_pos += pix.get_height()
    return scores_image
    
def add_score(score_card, score_name, score_value):
    score_card.append((score_name, score_value))
    score_card = sorted(score_card, key=lambda tup: tup[1], reverse=True)
    score_card = score_card[:9]
    return score_card

effects = []
score_card = load_scores()
score_card_image = draw_score_card(score_card)
score_font = pygame.font.Font(None, 20)
score_image = pygame.Surface((100, 30))
score_image.set_colorkey(MAGENTA)
score_image.fill(MAGENTA)
p1, p2 = (None, None)

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if in_menu:
                    running = False
                else:
                    # store existing player score
                    for p in players:
                        if p.kill_turn > 0:
                            score_card = add_score(score_card, p.name, p.kill_turn + p.kills)
                            score_card_image = draw_score_card(score_card)
                            p.kill_turn = 0
                    in_menu = True
            elif event.key == K_SPACE:
                if p1.alive or (p2 and p2.alive):
                    in_menu = in_menu ^ True
            elif event.key == K_1 and in_menu:
                turn = 1
                microbes = spawn(0)
                players = []
                p1 = Microbe('YOU')
                p1.load_frames(image_map, Rect(32, 96, 32, 32), 2)
                p1.rect.x = randint(60, play_area.width - 60)
                p1.rect.y = randint(60, play_area.height - 60)
                p1.indicator_color = WHITE
                p1.draw_healthbar = True
                microbes.append(p1)
                players.append(p1)
                in_menu = in_menu ^ True
            elif event.key == K_2 and in_menu:
                turn = 1
                microbes = spawn(5)
                players = []
                p1 = Microbe('YOU')
                p1.load_frames(image_map, Rect(32, 96, 32, 32), 2)
                p1.rect.x = randint(60, play_area.width - 60)
                p1.rect.y = randint(60, play_area.height - 60)
                p1.indicator_color = WHITE
                p1.draw_healthbar = True
                microbes.append(p1)
                players.append(p1)
                p2 = Microbe('FRIEND')
                p2.load_frames(image_map, Rect(32, 96, 32, 32), 2)
                p2.rect.x = randint(60, play_area.width - 60)
                p2.rect.y = randint(60, play_area.height - 60)
                p2.indicator_color = YELLOW
                p2.draw_healthbar = True
                microbes.append(p2)
                players.append(p2)
                in_menu = in_menu ^ True

    # animate sprites
    this_time = pygame.time.get_ticks()
    animate_sprites = False
    if (this_time - last_animation_tick > ANIMATE_DELAY):
        last_animation_tick = this_time
        animate_sprites = True

    #screen.fill(PALE_BLUE)
    screen.blit(background, (0, 0))
    
    if in_menu:
        screen.blit(help_image, (0, 0))
        screen.blit(score_card_image, (90, 200))
    else:

        # player movement
        pressed = pygame.key.get_pressed()
        
        if pressed[K_LEFT]:
            p1.turnate(20)
        if pressed[K_RIGHT]:
            p1.turnate(-20)
        if pressed[K_UP]:
            p1.travelate(acceleration=1, boundary=play_area)
        else:
            p1.travelate(acceleration=None, boundary=play_area)
        
        if pressed[K_a]:
            p2.turnate(20)
        if pressed[K_d]:
            p2.turnate(-20)
        if pressed[K_w]:
            p2.travelate(acceleration=1, boundary=play_area)
        else:
            if p2:
                p2.travelate(acceleration=None, boundary=play_area)
        
        # effects
        dequeue = []
        for fx in effects:
            if fx.tick():
                fx.update()
                fx.draw(screen)
            else:
                dequeue.append(fx)
        for old_fx in dequeue:
            effects.remove(old_fx)
        
        # ai movement and collisions
        death_list = []
        for miccy in microbes:
            miccy.update()
            miccy.draw(screen, draw_indicator=pressed[K_TAB])
            if animate_sprites:
                miccy.animate()
            if miccy.remove_sprite:
                death_list.append(miccy)
            if miccy not in players:
                rnd = randint(0, 10)
                if miccy.name == 'squigly':
                    if rnd == 0:
                        miccy.turnate(20)
                    elif rnd == 5:
                        miccy.turnate(-20)
                    if rnd == 10:
                        miccy.travelate(acceleration=5, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'spikey':
                    if rnd == 0:
                        miccy.turnate(30)
                    elif rnd == 5:
                        miccy.turnate(-30)
                    if rnd > 3:
                        miccy.travelate(acceleration=0.5, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'feebly':
                    if rnd == 0:
                        miccy.turnate(10)
                    elif rnd == 5:
                        miccy.turnate(-10)
                    if rnd > 0:
                        miccy.travelate(acceleration=0.5, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'bulby':
                    if rnd == 0:
                        miccy.turnate(50)
                    elif rnd == 5:
                        miccy.turnate(-50)
                    if rnd > 5:
                        miccy.travelate(acceleration=0.7, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'flatty':
                    if rnd == 3:
                        miccy.turnate(15)
                    elif rnd == 6:
                        miccy.turnate(-15)
                    if rnd > 7:
                        miccy.travelate(acceleration=1, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'doggy':
                    if rnd < 3:
                        miccy.turnate(5)
                    elif rnd > 6:
                        miccy.turnate(-5)
                    if rnd in (1, 3, 5, 7, 9):
                        miccy.travelate(acceleration=2, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'fishy':
                    if rnd == 5:
                        miccy.turnate(12)
                    elif rnd == 6:
                        miccy.turnate(-12)
                    if rnd > 6:
                        miccy.travelate(acceleration=2, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'algy':
                    if rnd == 5:
                        miccy.turnate(12)
                    elif rnd == 6:
                        miccy.turnate(-12)
                    if rnd > 6:
                        miccy.travelate(acceleration=1, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'sushi':
                    if rnd < 5:
                        miccy.turnate(12)
                    elif rnd > 5:
                        miccy.turnate(-12)
                    if rnd == 0:
                        miccy.travelate(acceleration=10, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'fractey':
                    if rnd < 2:
                        miccy.turnate(12)
                    elif rnd > 8:
                        miccy.turnate(-12)
                    if rnd > 6:
                        miccy.travelate(acceleration=5, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'crystley':
                    if rnd < 2:
                        miccy.turnate(12)
                    elif rnd > 8:
                        miccy.turnate(-12)
                    if rnd > 6:
                        miccy.travelate(acceleration=5, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                elif miccy.name == 'pulsey':
                    if rnd != 5:
                        miccy.turnate(12)
                    elif rnd == 5:
                        miccy.turnate(-12)
                    if rnd > 4:
                        miccy.travelate(acceleration=1, boundary=play_area)
                    else:
                        miccy.travelate(acceleration=None, boundary=play_area)
                
                for p in players:
                    if p.alive and miccy.can_collide and p.collide_rect.colliderect(miccy.collide_rect):
                        miccy.destroy()
                        if miccy.isfood:
                            p.heal()
                            p.add_kill()
                            effects.append(PingEffect(p.rect.center, GREEN, 20, 1))
                        else:
                            p.take_damage()
                            effects.append(PingEffect(p.rect.center, RED, 20, 1))
                            if not p.alive:
                                p.kill_turn = turn
                                effects.append(PingEffect(p.rect.center, RED, 50, 0))
                        print('%s collides with %s' % (p.name, miccy.name))
        
        for corpse in death_list:
            microbes.remove(corpse)
        
        # count life
        if (this_time - last_life_tick > ONE_SECOND):
            last_life_tick = this_time
            turn += 1
            print('%s seconds passed' % (turn))
            if (turn % 1) == 0 and len(microbes) < 100:
                microbes.extend(spawn(1))
            for p in players:
                if p.alive:
                    p.die_slowly()
                    if not p.alive:
                        p.kill_turn = turn
                        effects.append(PingEffect(p.rect.center, RED, 50, 0))
        
        # expired yet?
        if not p1.alive and (p2 and not p2.alive or not p2):
            screen.blit(expired_image, ((play_area.width - expired_image.get_width()) / 2, 0))

        if p1.alive:
            score_image.fill(MAGENTA, (0, 0, 100, 15))
            pix = score_font.render('p1 score: %s' % (turn + p1.kills), False, LITE_BLUE, MAGENTA)
            pix.set_colorkey(MAGENTA)
            score_image.blit(pix, (0, 0))
        if p2 and p2.alive:
            score_image.fill(MAGENTA, (0, 15, 100, 15))
            pix = score_font.render('p2 score: %s' % (turn + p2.kills), False, LITE_BLUE, MAGENTA)
            pix.set_colorkey(MAGENTA)
            score_image.blit(pix, (0, 16))

        screen.blit(score_image, (10, 10))

    # main loop
    pygame.display.flip()
    clock.tick(10)
save_scores(score_card)