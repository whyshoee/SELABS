import pygame
from game.maze import CELL, bfs

SPEED = 2
WALL_T = 3  # wall thickness in pixels (matches the line width used in draw)
FROZEN_TINT = (140, 200, 255)


def wall_rects_for_cell(walls, r, c):
    """Return thin collision rects for every wall present on cell (r, c)."""
    x, y = c * CELL, r * CELL
    t = WALL_T
    h = t // 2  # lines are drawn centred on the cell edge
    rects = []
    w = walls[r][c]
    if w[0]: rects.append(pygame.Rect(x - h, y - h, CELL + t, t))          # top
    if w[1]: rects.append(pygame.Rect(x - h, y + CELL - h, CELL + t, t))   # bottom
    if w[2]: rects.append(pygame.Rect(x + CELL - h, y - h, t, CELL + t))   # right
    if w[3]: rects.append(pygame.Rect(x - h, y - h, t, CELL + t))          # left
    return rects


class Player:
    def __init__(self, r, c):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-10, cy-10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = SPEED
        # Move one axis at a time so the player can slide along walls
        nr = self.rect.move(dx, 0)
        if self._valid(nr, walls, rows, cols): self.rect = nr
        nr = self.rect.move(0, dy)
        if self._valid(nr, walls, rows, cols): self.rect = nr

    def _valid(self, rect, walls, rows, cols):
        # Stay inside the maze area
        if rect.left < 0 or rect.top < 0 or rect.right > cols * CELL or rect.bottom > rows * CELL:
            return False
        # Check walls of every cell the rect overlaps
        r0, r1 = rect.top // CELL, (rect.bottom - 1) // CELL
        c0, c1 = rect.left // CELL, (rect.right - 1) // CELL
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                for wr in wall_rects_for_cell(walls, r, c):
                    if rect.colliderect(wr):
                        return False
        return True

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)


class Enemy:
    def __init__(self, r, c, color=(220, 60, 60)):
        self.r, self.c = r, c
        cx, cy = c*CELL+CELL//2, r*CELL+CELL//2
        self.rect = pygame.Rect(cx-12, cy-12, 24, 24)
        self.color = color
        self.timer = 0
        self.move_interval = 20  # frames between cell moves
        self.frozen = False      # set by the power pellet

    def update(self, walls, player, rows, cols):
        if self.frozen:
            return  # frozen enemies do nothing (timer is paused too)
        self.timer += 1
        if self.timer >= self.move_interval:
            self.timer = 0
            pr, pc = player.rect.centery//CELL, player.rect.centerx//CELL
            step = bfs(walls, (self.r, self.c), (pr, pc), rows, cols)
            if step:
                dr, dc = step
                self.r += dr; self.c += dc
                cx, cy = self.c*CELL+CELL//2, self.r*CELL+CELL//2
                self.rect.center = (cx, cy)

    def draw(self, screen):
        if self.frozen:
            # Blend the enemy's own color toward ice blue so enemies stay distinguishable
            body = tuple((a + b) // 2 for a, b in zip(self.color, FROZEN_TINT))
        else:
            body = self.color
        pygame.draw.rect(screen, body, self.rect, border_radius=5)
        if self.frozen:
            pygame.draw.rect(screen, (225, 245, 255), self.rect, width=2, border_radius=5)
        # eyes
        for ex in [self.rect.x+4, self.rect.x+14]:
            pygame.draw.circle(screen, (255,255,255), (ex, self.rect.y+8), 4)
            pygame.draw.circle(screen, (0,0,0), (ex+1, self.rect.y+8), 2)