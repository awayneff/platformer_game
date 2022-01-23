import pygame
from pygame.locals import *
import pickle
from pathlib import Path
import subprocess


pygame.init()

screen_width = 840
screen_height = 700
tile_size = screen_height // 20

default_level = "lvl/world_data0.pkl"
current_level = default_level
lvl_num = 0

running = True
changes_made = True

bg_img = pygame.image.load("img/bg.png")
bg_img = pygame.transform.scale(bg_img, (screen_width, screen_height))

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Level editor")

font = pygame.font.SysFont("Arial", 15)


class World():
    def __init__(self, screen, data, tile_size) -> None:
        self.screen = screen
        self.data = data
        self.tile_size = tile_size

        self.block_changed = False
        self.right_click = False

        self.dirt_img = pygame.image.load("img/platformIndustrial_005.png")
        self.grass_img = pygame.image.load("img/platformIndustrial_001.png")
        self.enemy_img = pygame.image.load("img/blob.png")

        # 6 and on
        self.lava_img = pygame.image.load("img/lava.png")
        self.coin_img = pygame.image.load("img/coin.png")
        self.exit_img = pygame.image.load("img/exit.png")
        self.guy_img = pygame.image.load("img/guy1.png")

        self.start_pos = []
        self.finish_pos = []

    def update(self, changes_made):
        tiles = []
        if changes_made:
            row_ct = 0
            for row in self.data:
                col_ct = 0
                for tile in row:
                    if tile == 1:
                        img = pygame.transform.scale(
                            self.dirt_img, (self.tile_size, self.tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        tiles.append((img, img_rect))
                    if tile == 2:
                        img = pygame.transform.scale(
                            self.grass_img, (tile_size, tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        tiles.append((img, img_rect))
                    if tile == 3:
                        img = pygame.transform.scale(
                            self.enemy_img, (tile_size, tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        tiles.append((img, img_rect))
                    if tile == 6:
                        img = pygame.transform.scale(
                            self.lava_img, (tile_size, tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        tiles.append((img, img_rect))
                    if tile == 7:
                        img = pygame.transform.scale(
                            self.coin_img, (tile_size, tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size
                        tiles.append((img, img_rect))
                    if tile == 8:
                        img = pygame.transform.scale(
                            self.exit_img, (tile_size, 2 * tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size - tile_size
                        tiles.append((img, img_rect))
                    if tile == -1:
                        img = pygame.transform.scale(
                            self.guy_img, (tile_size, 2 * tile_size))
                        img_rect = img.get_rect()
                        img_rect.x = col_ct * self.tile_size
                        img_rect.y = row_ct * tile_size - tile_size
                        tiles.append((img, img_rect))
                    col_ct += 1
                row_ct += 1

            changes_made = False

        for tile in tiles:
            self.screen.blit(tile[0], tile[1])

        # Draw the background for the GUI
        dirt_img = pygame.transform.scale(
            self.dirt_img, (self.tile_size, self.tile_size))

        for i in range(6):
            for j in range(20):
                screen.blit(dirt_img, ((700 + tile_size * i), tile_size * j))

        # World edit block
        pos = pygame.mouse.get_pos()
        # Prevent the out of bounds error when click in the GUI field
        if pos[0] <= screen_height:
            # Basic blocks edit with LMB
            if pygame.mouse.get_pressed()[0] == 1 and not self.block_changed:
                # Get the tile pos in matrix
                dim1 = pos[1] // tile_size
                dim2 = pos[0] // tile_size
                # Change the block to the next one
                self.data[dim1][dim2] += 1

                # Skip the 4, 5 nums
                if self.data[dim1][dim2] == 4:
                    self.data[dim1][dim2] = 6

                # Reset the block code
                if self.data[dim1][dim2] > 7:
                    self.data[dim1][dim2] = 0
                self.block_changed = True

            if pygame.mouse.get_pressed()[0] == 0:
                self.block_changed = False
                self.changes_made = True

            if pos[1] >= tile_size:
                # Special blocks edit with RMB (start/ finish points)
                if pygame.mouse.get_pressed()[2] == 1 and not self.right_click:
                    dim1 = pos[1] // tile_size
                    dim2 = pos[0] // tile_size

                    if self.data[dim1][dim2] == -1:
                        self.data[dim1][dim2] = 8
                        if (dim1, dim2) not in self.finish_pos:
                            self.finish_pos.append((dim1, dim2))

                    elif 8 >= self.data[dim1][dim2] >= 0:
                        self.data[dim1][dim2] = -1
                        if (dim1, dim2) not in self.start_pos:
                            self.start_pos.append((dim1, dim2))
                    self.right_click = True

                if pygame.mouse.get_pressed()[2] == 0:
                    self.right_click = False
                    self.changes_made = True

    # Force update data when level loaded
    def update_data(self, data):
        self.data = data


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


class TextField():
    def __init__(self, x, y, width, height, font) -> None:
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = "world_data"
        self.text_field = font.render(self.text, True, (255, 255, 255))
        self.active = False

        # Define active and inactive outline colors
        self.color_inactive = (0, 0, 0)
        self.color_active = (0, 150, 0)
        self.color = self.color_inactive

    def update(self, event):
        # Choose the color depending on the text field state
        self.color = self.color_active if self.active else self.color_inactive

        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0] == 1:
            self.active = True
        if not self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0] == 1:
            self.active = False

        # Typing mechanism
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.active = False
                else:
                    self.text += event.unicode

    def draw(self, screen):
        self.text_field = self.font.render(self.text, True, (0, 0, 0))
        screen.blit(self.text_field, (self.rect.x + 2, self.rect.y + 2))
        pygame.draw.rect(screen, self.color, self.rect, 1)

    def get_text(self):
        return self.text


def save_data(world_data, file_name):
    try:
        with open(file_name, "wb") as output:
            pickle.dump(world_data, output, pickle.HIGHEST_PROTOCOL)
    except:
        raise IOError("Error when writing data")


def load_data(file_name):
    try:
        with open(file_name, "rb") as input:
            data = pickle.load(input)
    except:
        raise IOError("Error when reading data")
    return data


click_sound = pygame.mixer.Sound("img/click.wav")
btn_path = "img/btn_bg.png"

world_data = load_data(default_level)

world = World(screen, world_data, tile_size)
save_btn = Button(int(0.85*screen_width), tile_size * 2 - 10, btn_path,
                  (screen_width // 6, screen_height // 14), "save", click_sound)
load_btn = Button(int(0.85*screen_width), tile_size * 5, btn_path,
                  (screen_width // 6, screen_height // 14), "load", click_sound)
game_btn = Button(int(0.85*screen_width), tile_size * 7, btn_path,
                  (screen_width // 6, screen_height // 14), "game", click_sound)
exit_btn = Button(int(0.85*screen_width), tile_size * 9, btn_path,
                  (screen_width // 6, screen_height // 14), "exit", click_sound)

current_level_t = font.render(
    current_level[4:len(current_level) - 4], True, (0, 0, 0))

current_level_tf = TextField(
    int(0.85*screen_width), tile_size * 4, 150, 20, font)


while running:
    screen.blit(bg_img, (0, 0))

    world.update(changes_made)

    screen.blit(current_level_t, (int(0.85*screen_width) + 10, tile_size))

    current_level_tf.draw(screen)

    # Load selected level
    if load_btn.draw(40, 10):
        current_level = "lvl/" + current_level_tf.get_text() + ".pkl"

        if not Path(current_level).is_file():
            num = int(current_level[14:len(current_level) - 4])
            level_to_save = f"lvl/world_data{num}.pkl"
            save_data(load_data(default_level), level_to_save)

        current_level_t = font.render(
            current_level[4:len(current_level) - 4], True, (0, 0, 0))
        world_data = load_data(current_level)
        world.update_data(world_data)
        changes_made = True

    # Save the current level
    if save_btn.draw(40, 10):
        save_data(world_data, current_level)

    # Open the game
    if game_btn.draw(40, 10):
        subprocess.Popen("python3 main.py", shell=True)
        running = False
    
    # Exit the editor
    if exit_btn.draw(40, 10):
        running = False

    # UI border
    pygame.draw.line(screen, (0, 150, 0), (700, 0), (700, 700), 1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        current_level_tf.update(event)
    pygame.display.update()

pygame.quit()
