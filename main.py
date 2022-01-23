import pygame
from pygame.locals import *
import pickle
import subprocess
import os


# Define variables
display_width = 700
display_height = 700

fps = 60
tile_size = display_width // 20
lvl_num = 1
max_lvls = len([name for name in os.listdir("lvl")]) - 2

running = True
main_menu = True
paused = False
changes_made = True
out_of_levels = False
game_over = False

# Developer mode
dev = False

clock = pygame.time.Clock()


class World():
    def __init__(self, screen, data, tile_size) -> None:
        self.screen = screen
        self.data = data
        self.tile_size = tile_size
        self.tile_list = []

        self.block_changed = False
        self.right_click = False

        self.dirt_img = pygame.image.load("img/platformIndustrial_005.png")
        self.grass_img = pygame.image.load("img/platformIndustrial_001.png")
        self.enemy_img = pygame.image.load("img/blob.png")
        self.exit_img = pygame.image.load("img/exit.png")

        self.start = (0, 0)
        self.finish = (0, 0)
        self.finish_data = []
        self.update(changes_made, self.data)

    def update(self, changes_made, world_data):
        if changes_made:
            self.tile_list = []
            coins_group.empty()
            enemies_group.empty()
            lava_group.empty()

            row_ct = 0
            for row in world_data:
                col_ct = 0
                for tile in row:
                    if tile == -1:
                        self.start = (col_ct * tile_size, row_ct * tile_size)
                    if tile == 1:
                        img = pygame.transform.scale(
                            self.dirt_img, (self.tile_size, self.tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        self.tile_list.append((img, img_rect))
                    if tile == 2:
                        img = pygame.transform.scale(
                            self.grass_img, (tile_size, tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        self.tile_list.append((img, img_rect))
                    if tile == 3:
                        blob = Enemy(col_ct * tile_size, row_ct *
                                     tile_size, tile_size)
                        enemies_group.add(blob)
                    if tile == 6:
                        lava = Lava(col_ct * tile_size, row_ct *
                                    tile_size + tile_size // 2, tile_size)
                        lava_group.add(lava)
                    if tile == 7:
                        coin = Coin(col_ct * tile_size, row_ct *
                                    tile_size, tile_size)
                        coins_group.add(coin)
                    if tile == 8:
                        finish_img = pygame.transform.scale(
                            self.exit_img, (tile_size, 2 * tile_size))
                        finish_rect = img.get_rect()
                        finish_rect.x = col_ct * self.tile_size
                        finish_rect.y = row_ct * tile_size - tile_size
                        self.finish_data = [finish_img, finish_rect]
                        self.finish = (col_ct * tile_size, row_ct * tile_size)
                    col_ct += 1
                row_ct += 1
            changes_made = False
            return changes_made

        self.screen.blit(self.finish_data[0], self.finish_data[1])
        for tile in self.tile_list:
            self.screen.blit(tile[0], tile[1])
            if dev:
                pygame.draw.rect(screen, (255, 255, 255), tile[1], 2)

    def restart(self):
        coins_group.empty()
        row_ct = 0
        for row in world_data:
            col_ct = 0
            for tile in row:
                if tile == 7:
                    coin = Coin(col_ct * self.tile_size, row_ct *
                                self.tile_size, self.tile_size)
                    coins_group.add(coin)
                col_ct += 1
            row_ct += 1

    def update_data(self, data):
        self.data = data


class Player():
    def __init__(self, x, y) -> None:
        # Load all the players sprites
        self.start = (x, y)
        self.hp = 5
        self.dead = False

        self.direction = 1
        self.counter = 0
        self.walk_cooldown = 20
        self.index = 0

        self.images_right = []
        self.images_left = []

        for num in range(1, 5):
            img_right = pygame.image.load(f"img/guy{num}.png")
            img_right = pygame.transform.scale(
                img_right, (display_width // 25, display_width // 12))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)

        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        self.speed = display_width * 0.006
        self.vel_y = 0
        self.jvel_y = -self.speed * 2.6
        self.dvel_y = abs(self.jvel_y * 0.06)  # 0.1
        self.lvel_y = abs(self.jvel_y * 1.2)  # 5
        self.in_jump = False

        self.coins = 0
        self.overall_coins = 0

        # Audio initialization
        self.coin_audio = pygame.mixer.Sound("img/coin.wav")
        self.jump_audio = pygame.mixer.Sound("img/jump.wav")
        self.death_audio = pygame.mixer.Sound("img/game_over.wav")

    def update(self):
        global coins
        dx = 0
        dy = 0

        # Keypress handler
        key = pygame.key.get_pressed()
        if (key[pygame.K_UP] or key[pygame.K_SPACE]) and not self.in_jump:
            self.vel_y = self.jvel_y
            self.in_jump = True
            self.jump_ct = 0
            self.jump_audio.play()

        if key[pygame.K_LEFT] or key[pygame.K_a]:
            dx -= self.speed
            self.counter += 1
            self.direction = -1
        if key[pygame.K_RIGHT] or key[pygame.K_d]:
            dx += self.speed
            self.counter += 1
            self.direction = 1

        # Gravity
        self.vel_y += self.dvel_y
        if self.vel_y > self.lvel_y:
            self.vel_y = self.lvel_y
        dy += self.vel_y

        # Animation
        if self.counter > self.walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images_right):
                self.index = 0

        # Flip the character sprite when turn around
        if self.direction == 1:
            self.image = self.images_right[self.index]
        if self.direction == -1:
            self.image = self.images_left[self.index]

        # Check for collision
        for tile in world.tile_list:
            # Ox collision
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0

            # Oy collision
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # Player jumping (below the block)
                if self.vel_y < 0:
                    dy = tile[1].bottom - self.rect.top
                    self.vel_y = 0
                # Player falling (above the block)
                elif self.vel_y > 0:
                    self.in_jump = False
                    dy = tile[1].top - self.rect.bottom
                    self.vel_y = 0

            if tile[1].colliderect(self.rect.x, self.rect.y, self.width, 0):
                self.in_jump = True

        # Death
        if pygame.sprite.spritecollide(self, enemies_group, False) or pygame.sprite.spritecollide(self, lava_group, False):
            self.dead = True

        # Coin collection
        if pygame.sprite.spritecollide(self, coins_group, True):
            self.coins += 1
            self.coin_audio.play()

        # Update player's coordinates
        self.rect.x += dx
        self.rect.y += dy

        # (Optional?) World bottom border
        if self.rect.bottom > display_height:
            self.rect.bottom = display_height
            dy = 0
        if self.rect.x <= 0:
            self.rect.x = 0
        if self.rect.x >= display_width - tile_size:
            self.rect.x = display_width - tile_size

        # Draw the player on the screen
        screen.blit(self.image, self.rect)

        # Show the player's collision box
        if dev:
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_size) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("img/blob.png")
        self.image = pygame.transform.scale(self.image, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1

        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_size) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("img/lava.png")
        self.image = pygame.transform.scale(
            self.image, (tile_size, tile_size // 2 + 5))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_size) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("img/coin.png")
        self.image = pygame.transform.scale(self.image, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Button():
    def __init__(self, x, y, image_path, scale, label, sound) -> None:
        font = pygame.font.SysFont("arial", 20)
        self.render = font.render(label, 1, (0, 0, 0))
        self.sound = sound
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(
            self.image, (scale[0], scale[1]))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self, offset_x, offset_y):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True
                self.sound.play()

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)
        screen.blit(self.render, (self.rect.x +
                    offset_x, self.rect.y + offset_y))

        return action


def load_data(file_name):
    try:
        with open(file_name, "rb") as input:
            data = pickle.load(input)
    except:
        raise IOError("Error when reading data")
    return data


pygame.init()

# Display initialization
screen = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Platformer")

# Music stuff
pygame.mixer.init()
bg_music = pygame.mixer.music.load("img/music.mp3")
click_sound = pygame.mixer.Sound("img/click.wav")
pygame.mixer.music.set_volume(0.7)
pygame.mixer.music.play(-1, 0.0)
next_level_sound = pygame.mixer.Sound("img/next_level.mp3")

font = pygame.font.SysFont("Arial", 15)

# Load images
btn_path = "img/btn_bg.png"
start_btn_path = "img/start_btn.png"

hp_img = pygame.transform.scale(pygame.image.load("img/hp.png"), (20, 20))
coin_img = pygame.transform.scale(pygame.image.load("img/coin.png"), (20, 20))
bg_img = pygame.image.load("img/bg.png")
sun_img = pygame.image.load("img/sun.png")

# Main menu buttons
start_btn = Button(display_width // 2 - 110,
                   display_height // 2 - 20, start_btn_path, (display_width // 3, display_height // 12), "start", click_sound)

editor_btn = Button(display_width // 2 - 150, display_height // 2 + 100, btn_path,
                    (display_width // 6, display_height // 14), "editor", click_sound)
exit_btn = Button(display_width // 2 + 50, display_height //
                  2 + 100, btn_path, (display_width // 6, display_height // 14), "exit", click_sound)

# Pause menu buttons
resume_btn = Button(display_width // 2 - 150, display_height //
                    2, btn_path, (display_width // 6, display_height // 14), "resume", click_sound)
main_menu_btn = Button(display_width // 2 + 50, display_height // 2,
                       btn_path, (display_width // 6, display_height // 14), "menu", click_sound)


# Load the deafult level
world_data = load_data(f"lvl/world_data{lvl_num}.pkl")

# Create empty sprite groups
enemies_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()

# Create main objects
world = World(screen, world_data, tile_size)
player = Player(world.start[0], world.start[1])

out_of_lvls_label = font.render(
    f"You completed all {lvl_num} levels! Start over?", 1, (0, 0, 0))
out_of_hps_label = font.render("Ouch! You lost. Try again?", 1, (0, 0, 0))


while running:
    clock.tick(fps)

    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (50, 50))

    # Main menu loop
    if main_menu:
        if out_of_levels:
            screen.blit(out_of_lvls_label, (display_width // 2 - 115, 300))
            screen.blit(pygame.transform.scale(coin_img, (25, 25)),
                        (display_width // 2 - 20, 245))
            screen.blit(font.render(str(player.overall_coins), 1,
                        (0, 0, 0)), (display_width // 2 + 20, 250))
        if game_over:
            screen.blit(out_of_hps_label, (display_width // 2 - 80, 300))

        player.hp = 5
        lvl_num = 1
        world_data = load_data(f"lvl/world_data{lvl_num}.pkl")
        changes_made = True

        # Handle buttons
        if start_btn.draw(100, 20):
            game_over = False
            out_of_levels = False
            main_menu = False
        if exit_btn.draw(40, 10):
            running = False
        if editor_btn.draw(35, 10):
            subprocess.Popen("python3 level_editor.py", shell=True)
            running = False

    # Pause menu loop
    elif paused:
        if resume_btn.draw(27, 10):
            paused = False
        if main_menu_btn.draw(35, 10):
            paused = False
            main_menu = True
            player.dead = True

    # Update the world and the player
    else:
        player.update()

        changes_made = world.update(changes_made, world_data)

        screen.blit(pygame.transform.scale(coin_img, (20, 20)), (10, 5))
        screen.blit(font.render(str(player.coins), 1, (0, 0, 0)), (35, 5))
        screen.blit(hp_img, (display_width - 30, 5))
        screen.blit(font.render(str(player.hp), 1, (0, 0, 0)),
                    (display_width - 40, 5))

        # Draw the sprites on the screen
        enemies_group.draw(screen)
        enemies_group.update()
        lava_group.draw(screen)
        coins_group.draw(screen)

        # Level completed
        if world.finish_data[1].colliderect(player.rect):
            player.rect.x -= 10
            player.overall_coins += player.coins
            player.coins = 0
            next_level_sound.play()
            
            if lvl_num <= max_lvls:
                lvl_num += 1
                world_data = load_data(f"lvl/world_data{lvl_num}.pkl")
                changes_made = True
                changes_made = world.update(changes_made, world_data)
                player.rect.x = world.start[0]
                player.rect.y = world.start[1]
            else:
                out_of_levels = True
                main_menu = True
           
            
        # Reset progress if player died
        if player.dead:
            player.death_audio.play()
            player.hp -= 1
            player.rect.x = world.start[0]
            player.rect.y = world.start[1]
            player.coins = 0
            world.restart()
            player.dead = False

            if player.hp <= 0:
                game_over = True
                main_menu = True

    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                player.dead = True
            if event.key == pygame.K_ESCAPE:
                if not main_menu:
                    paused = True if not paused else False

    pygame.display.update()

pygame.quit()
