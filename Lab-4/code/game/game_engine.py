import random
import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
HUD_H = 66
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + HUD_H
FPS = 60

# Difficulty ramp settings
RAMP_INTERVAL_MS = 15000   # how often enemies speed up
RAMP_STEP = 2              # frames removed from move_interval each step
MIN_MOVE_INTERVAL = 5      # enemies never move faster than this

# Power pellet settings
FREEZE_FRAMES = 300        # how long enemies stay frozen after pickup
PELLET_RADIUS = 8
PELLET_COLOR = (255, 220, 0)

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.small_font = pygame.font.SysFont("monospace", 13, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        # One enemy per remaining corner; each runs its own BFS every update.
        self.enemies = [
            Enemy(ROWS-1, COLS-1, (220, 60, 60)),    # bottom-right (red)
            Enemy(0, COLS-1,      (230, 140, 30)),   # top-right (orange)
            Enemy(ROWS-1, 0,      (160, 60, 200)),   # bottom-left (purple)
        ]
        self.exit_rect = pygame.Rect((COLS//2)*CELL+5, (ROWS//2)*CELL+5, CELL-10, CELL-10)
        self.caught = False
        self.won = False
        # Survival score (1 point per frame alive)
        self.score = 0
        # Difficulty ramp state
        self.start_ticks = pygame.time.get_ticks()
        self.elapsed_ms = 0
        self.tier = 0  # number of speed-ups applied so far
        # Power pellet state
        self._place_pellet()
        self.freeze_frames = 0

    def _place_pellet(self):
        # Any cell except the four corners (player/enemy starts) and the exit cell
        excluded = {(0, 0), (0, COLS-1), (ROWS-1, 0), (ROWS-1, COLS-1), (ROWS//2, COLS//2)}
        cells = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in excluded]
        r, c = random.choice(cells)
        cx, cy = c*CELL + CELL//2, r*CELL + CELL//2
        self.pellet_center = (cx, cy)
        self.pellet_rect = pygame.Rect(cx - PELLET_RADIUS, cy - PELLET_RADIUS,
                                       PELLET_RADIUS*2, PELLET_RADIUS*2)
        self.pellet_active = True

    def _enemies_maxed(self):
        return all(e.move_interval <= MIN_MOVE_INTERVAL for e in self.enemies)

    def _apply_difficulty_ramp(self):
        # Apply one speed-up per elapsed 15s block (loop in case a frame was long).
        while self.elapsed_ms >= (self.tier + 1) * RAMP_INTERVAL_MS and not self._enemies_maxed():
            for enemy in self.enemies:
                enemy.move_interval = max(MIN_MOVE_INTERVAL, enemy.move_interval - RAMP_STEP)
            self.tier += 1

    def _update_freeze(self):
        # Count down an active freeze; unfreeze everyone when it runs out.
        if self.freeze_frames > 0:
            self.freeze_frames -= 1
            if self.freeze_frames == 0:
                for enemy in self.enemies:
                    enemy.frozen = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.caught or self.won: return  # timer, tier, freeze and score all stop on game over
        self.elapsed_ms = pygame.time.get_ticks() - self.start_ticks
        self._apply_difficulty_ramp()
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)

        # Power pellet: tick any running freeze first, then check for pickup
        self._update_freeze()
        if self.pellet_active and self.player.rect.colliderect(self.pellet_rect):
            self.pellet_active = False
            for enemy in self.enemies:
                enemy.frozen = True
            self.freeze_frames = FREEZE_FRAMES

        for enemy in self.enemies:
            enemy.update(self.walls, self.player, ROWS, COLS)  # no-op while frozen
        if any(self.player.rect.colliderect(e.rect) for e in self.enemies):
            self.caught = True
        elif self.player.rect.colliderect(self.exit_rect):
            self.won = True

        # Survival score: +1 for every frame the player is still alive
        if not (self.caught or self.won):
            self.score += 1

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc=(50,40,60)
        for r in range(ROWS):
            for c in range(COLS):
                x,y=c*CELL,r*CELL
                w=self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen,wc,(x,y),(x+CELL,y),3)
                if w[1]: pygame.draw.line(self.screen,wc,(x,y+CELL),(x+CELL,y+CELL),3)
                if w[2]: pygame.draw.line(self.screen,wc,(x+CELL,y),(x+CELL,y+CELL),3)
                if w[3]: pygame.draw.line(self.screen,wc,(x,y),(x,y+CELL),3)
        pygame.draw.rect(self.screen,(80,200,80),self.exit_rect,border_radius=4)
        lbl=self.small_font.render("EXIT",True,(20,80,20))
        self.screen.blit(lbl,lbl.get_rect(center=self.exit_rect.center))

        if self.pellet_active:
            pygame.draw.circle(self.screen, PELLET_COLOR, self.pellet_center, PELLET_RADIUS)
            pygame.draw.circle(self.screen, (170, 130, 0), self.pellet_center, PELLET_RADIUS, 2)

        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # HUD: hint, then time / speed tier (+ freeze), then survival score
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,HUD_H)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        info=self.hud_font.render("Reach EXIT before the enemy catches you!  R=Restart",True,(200,200,200))
        self.screen.blit(info,(8,ROWS*CELL+5))

        secs = self.elapsed_ms // 1000
        tier_label = f"Speed tier {self.tier + 1}" + (" MAX" if self._enemies_maxed() else "")
        interval = self.enemies[0].move_interval
        status = f"Time {secs//60:02d}:{secs%60:02d}   {tier_label}   (enemy moves every {interval}f)"
        status_color = (240, 120, 100) if self._enemies_maxed() else (160, 220, 160)
        stat=self.small_font.render(status,True,status_color)
        self.screen.blit(stat,(8,ROWS*CELL+27))

        if self.freeze_frames > 0:
            secs_left = (self.freeze_frames + FPS - 1) // FPS  # round up
            fz=self.small_font.render(f"FROZEN {secs_left}s",True,(140,200,255))
            self.screen.blit(fz,(WIDTH-fz.get_width()-8,ROWS*CELL+27))

        surv=self.small_font.render(f"Survived: {self.score // 60}s",True,(255,230,120))
        self.screen.blit(surv,(8,ROWS*CELL+46))

        if self.caught:
            self._overlay("CAUGHT!", (220,60,60))
        elif self.won:
            self._overlay("ESCAPED!", (80,220,80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf=pygame.Surface((WIDTH,ROWS*CELL),pygame.SRCALPHA)
        surf.fill((0,0,0,140))
        self.screen.blit(surf,(0,0))
        mid=ROWS*CELL//2
        msg=self.big_font.render(text,True,color)
        score_txt=self.font.render(f"Survived: {self.score // 60}s (score {self.score})",True,(255,230,120))
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,mid-50))
        self.screen.blit(score_txt,(WIDTH//2-score_txt.get_width()//2,mid+5))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,mid+40))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()