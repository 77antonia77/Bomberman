import pygame
import random
import sys
import time

pygame.init()

# Setări generale
WIDTH, HEIGHT = 1000, 800
GRID_SIZE = 15
TILE_SIZE = 40
MAP_WIDTH, MAP_HEIGHT = GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
FPS = 60
FONT = pygame.font.SysFont("Arial", 18)
BIG_FONT = pygame.font.SysFont("Arial", 36)

# Culori
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
          (255, 0, 255), (0, 255, 255), (200, 100, 0), (100, 0, 200)]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bomberman Tournament")
clock = pygame.time.Clock()

# Hartă și pereți
map_data = [[" "] * GRID_SIZE for _ in range(GRID_SIZE)]
for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        if x == 0 or y == 0 or x == GRID_SIZE - 1 or y == GRID_SIZE - 1:
            map_data[y][x] = "I"
        elif x % 2 == 0 and y % 2 == 0:
            map_data[y][x] = "I"
        elif random.random() < 0.3:
            map_data[y][x] = "D"

class Player:
    def __init__(self, x, y, color, controls=None, is_human=False):
        self.x = x
        self.y = y
        self.color = color
        self.controls = controls
        self.is_human = is_human
        self.alive = True
        self.score = 0
        self.bonus = 0
        self.special_ready = False
        self.invincible = False
        self.invincible_timer = 0
        self.number = None
        self.lives = 3

    def move(self, dx, dy):
        if not self.alive or self.invincible:
            return
        new_x, new_y = self.x + dx, self.y + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            if map_data[new_y][new_x] == " ":
                self.x = new_x
                self.y = new_y
                self.bonus += 0.3

    def update(self):
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        if self.bonus >= 100:
            self.special_ready = True

players = []
spawn_points = [(1,1),(13,1),(1,13),(13,13),(1,7),(7,1),(7,13),(13,7)]
random.shuffle(spawn_points)
for i in range(8):
    x, y = spawn_points[i]
    is_human = i < 2
    controls = None
    if is_human:
        if i == 0:
            controls = {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d, "bomb": pygame.K_q, "special": pygame.K_e}
        else:
            controls = {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT, "bomb": pygame.K_RETURN, "special": pygame.K_m}
    player = Player(x, y, COLORS[i], controls, is_human)
    player.number = i + 1
    players.append(player)

bombs = []
explosions = []
round_number = 1
round_active = False
start_button_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 40, 120, 30)
eliminated_players = []
round_timer = 0
# NU resetam round_timer la inceput de runda, doar il oprim cand runda nu e activa
show_ranking = False
winner_text = ""
winner_display_timer = 0  # Timer pentru mesajul castigator
ranking_button = pygame.Rect(WIDTH//2 - 70, HEIGHT - 80, 140, 30)
game_over = False  # Variabila stare final joc

class Bomb:
    def __init__(self, x, y, owner):
        self.x = x
        self.y = y
        self.owner = owner
        self.timer = 120

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            explode(self.x, self.y)
            bombs.remove(self)

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 20

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            explosions.remove(self)

def explode(x, y):
    explosions.append(Explosion(x, y))
    for p in players:
        if p.x == x and p.y == y and not p.invincible and p.alive:
            p.lives -= 1
            if p.lives <= 0:
                p.alive = False
                if p not in eliminated_players:
                    eliminated_players.append(p)

    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        for i in range(1, 2):
            nx, ny = x + dx*i, y + dy*i
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if map_data[ny][nx] == "I":
                    break
                explosions.append(Explosion(nx, ny))
                if map_data[ny][nx] == "D":
                    map_data[ny][nx] = " "
                    for p in players:
                        if p.x == nx and p.y == ny and not p.invincible and p.alive:
                            p.bonus += 10
                            p.lives -= 1
                            if p.lives <= 0:
                                p.alive = False
                                if p not in eliminated_players:
                                    eliminated_players.append(p)
                    break
                for p in players:
                    if p.x == nx and p.y == ny and not p.invincible and p.alive:
                        p.lives -= 1
                        if p.lives <= 0:
                            p.alive = False
                            if p not in eliminated_players:
                                eliminated_players.append(p)

def draw():
    screen.fill(BLACK)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            tile = map_data[y][x]
            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if tile == "I":
                pygame.draw.rect(screen, GRAY, rect)
            elif tile == "D":
                pygame.draw.rect(screen, WHITE, rect)

    for bomb in bombs:
        pygame.draw.rect(screen, WHITE, (bomb.x*TILE_SIZE+10, bomb.y*TILE_SIZE+10, 20, 20))
    for exp in explosions:
        pygame.draw.rect(screen, YELLOW, (exp.x*TILE_SIZE, exp.y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    for p in players:
        if p.alive:
            pygame.draw.rect(screen, p.color, (p.x*TILE_SIZE+5, p.y*TILE_SIZE+5, TILE_SIZE-10, TILE_SIZE-10))
            label = "S" if p.invincible else str(p.number)
            screen.blit(FONT.render(label, True, BLACK), (p.x*TILE_SIZE+12, p.y*TILE_SIZE+10))

    for i, p in enumerate(players):
        y_offset = MAP_HEIGHT + 10 + (i*25)
        pygame.draw.rect(screen, p.color, (10, y_offset, 15, 15))
        status = f"Player {p.number} | Scor: {p.score} | Bonus: {int(p.bonus)}% | Vieti: {p.lives}"
        if not p.alive:
            status += " (Eliminat)"
        screen.blit(FONT.render(status, True, WHITE), (30, y_offset))

    screen.blit(FONT.render(f"Timp: {round_timer//FPS} sec", True, WHITE), (WIDTH - 150, HEIGHT - 20))
    screen.blit(FONT.render(f"Runda: {round_number}", True, WHITE), (WIDTH - 300, HEIGHT - 20))

    if not round_active and not game_over:
        pygame.draw.rect(screen, GREEN, start_button_rect)
        screen.blit(FONT.render("Start Runda", True, BLACK), (start_button_rect.x+10, start_button_rect.y+5))

    pygame.draw.rect(screen, BLUE, ranking_button)
    screen.blit(FONT.render("Clasament", True, BLACK), (ranking_button.x+20, ranking_button.y+5))

    # Clasament in dreapta hartii
    if show_ranking:
        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        x_rank = MAP_WIDTH + 20
        y_rank = 20
        header = BIG_FONT.render("Clasament", True, YELLOW)
        screen.blit(header, (x_rank, y_rank))
        y_rank += 50
        for idx, p in enumerate(sorted_players):
            msg = f"Locul {idx+1}: Player {p.number} - Scor: {p.score}"
            screen.blit(FONT.render(msg, True, WHITE), (x_rank, y_rank + idx*25))

    # Mesaj castigator afisat 10 secunde
    if game_over and winner_text:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        text_surface = BIG_FONT.render(winner_text, True, YELLOW)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text_surface, text_rect)

    pygame.display.flip()

running = True
while running:
    clock.tick(FPS)
    draw()

    # Timer creste doar cand runda e activa
    if round_active:
        round_timer += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not round_active and not game_over and start_button_rect.collidepoint(event.pos):
                round_active = True
                round_number += 1
                eliminated_players = []
                winner_text = ""
                show_ranking = False
                winner_display_timer = 0
            elif ranking_button.collidepoint(event.pos):
                show_ranking = not show_ranking
        elif event.type == pygame.KEYDOWN:
            for p in players:
                if p.is_human and p.controls and p.alive:
                    if event.key == p.controls["bomb"]:
                        bombs.append(Bomb(p.x, p.y, p))
                    elif event.key == p.controls["special"] and p.special_ready:
                        p.invincible = True
                        p.invincible_timer = FPS * 5
                        p.special_ready = False
                        p.bonus = 0

    if round_active:
        for p in players:
            if p.alive:
                p.update()
                if p.is_human and p.controls:
                    keys = pygame.key.get_pressed()
                    if keys[p.controls["up"]]: p.move(0, -1)
                    if keys[p.controls["down"]]: p.move(0, 1)
                    if keys[p.controls["left"]]: p.move(-1, 0)
                    if keys[p.controls["right"]]: p.move(1, 0)
                else:
                    if random.random() < 0.1:
                        p.move(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
                    if random.random() < 0.02:
                        bombs.append(Bomb(p.x, p.y, p))

        for b in bombs[:]:
            b.update()
        for e in explosions[:]:
            e.update()

        alive_players = [p for p in players if p.alive]

        # Daca 2 sau mai multi eliminati -> pauza, castigatorii primesc punct
        if len(eliminated_players) >= 2:
            round_active = False
            for p in players:
                if p.alive:
                    p.score += 1
            winner_display_timer = 0

        # Daca mai e un singur jucator in viata, final de joc
        if len(alive_players) == 1:
            round_active = False
            game_over = True
            winner_text = f"Jucatorul {alive_players[0].number} a rezistat cel mai mult! Timp: {round_timer//FPS}s"
            alive_players[0].score += 1  # +1 la scor pentru ultimul jucător
            show_ranking = True
            winner_display_timer = FPS * 10  # 10 secunde afisare mesaj

    # Timer pentru afisarea mesajului castigator
    if game_over and winner_display_timer > 0:
        winner_display_timer -= 1
        if winner_display_timer == 0:
            winner_text = ""
            game_over = False
            # round_timer nu se reseteaza, ramane la valoarea cumulata

pygame.quit()
sys.exit()
