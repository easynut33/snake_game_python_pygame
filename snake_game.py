import random
import sys
from dataclasses import dataclass

import pygame


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720
TOP_BAR_HEIGHT = 90
GRID_AREA_MARGIN = 20
MIN_TICK_MS = 70


@dataclass
class GridOption:
    label: str
    cols: int
    rows: int


@dataclass
class SpeedOption:
    label: str
    tick_ms: int


GRID_OPTIONS = [
    GridOption("Small (20 x 12)", 20, 12),
    GridOption("Medium (30 x 18)", 30, 18),
    GridOption("Large (40 x 24)", 40, 24),
]

SPEED_OPTIONS = [
    SpeedOption("Slow", 190),
    SpeedOption("Normal", 140),
    SpeedOption("Fast", 95),
]


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake - Pygame")
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("consolas", 38, bold=True)
        self.body_font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)

        self.bg = (18, 22, 30)
        self.panel = (28, 34, 45)
        self.text = (238, 241, 247)
        self.muted = (160, 172, 189)
        self.snake_head = (58, 220, 110)
        self.snake_body = (42, 168, 84)
        self.food_color = (239, 83, 80)
        self.grid_line = (41, 48, 64)
        self.highlight = (61, 149, 255)

        self.grid_option: GridOption = GRID_OPTIONS[1]
        self.speed_option: SpeedOption = SPEED_OPTIONS[1]
        self.tick_ms = self.speed_option.tick_ms
        self.last_update_ms = 0

        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake: list[tuple[int, int]] = []
        self.food = (0, 0)
        self.score = 0
        self.game_over = False

        self.cell_size = 20
        self.board_left = 0
        self.board_top = 0
        self.board_width_px = 0
        self.board_height_px = 0

    def run(self) -> None:
        if not self.select_options():
            pygame.quit()
            return

        self.reset_game()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False
                    elif not self.game_over:
                        requested = self.direction_from_key(event.key)
                        if requested and not self.is_opposite(self.direction, requested):
                            self.next_direction = requested
                    elif self.game_over and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_game()

            now = pygame.time.get_ticks()
            if not self.game_over and now - self.last_update_ms >= self.tick_ms:
                self.update_game()
                self.last_update_ms = now

            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def select_options(self) -> bool:
        step = 0
        grid_idx = 1
        speed_idx = 1
        selecting = True

        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return False

                if step == 0:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        grid_idx = (grid_idx - 1) % len(GRID_OPTIONS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        grid_idx = (grid_idx + 1) % len(GRID_OPTIONS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        step = 1
                else:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        speed_idx = (speed_idx - 1) % len(SPEED_OPTIONS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        speed_idx = (speed_idx + 1) % len(SPEED_OPTIONS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selecting = False

            self.draw_menu(step, grid_idx, speed_idx)
            self.clock.tick(60)

        self.grid_option = GRID_OPTIONS[grid_idx]
        self.speed_option = SPEED_OPTIONS[speed_idx]
        self.tick_ms = self.speed_option.tick_ms
        return True

    def draw_menu(self, step: int, grid_idx: int, speed_idx: int) -> None:
        self.screen.fill(self.bg)
        title = self.title_font.render("Snake (Pygame)", True, self.text)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 70))

        subtitle = self.body_font.render("Choose grid size and speed", True, self.muted)
        self.screen.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, 130))

        panel = pygame.Rect(180, 190, 600, 340)
        pygame.draw.rect(self.screen, self.panel, panel, border_radius=8)

        labels = [
            "1) Grid Size",
            "2) Snake Speed",
        ]
        for i, label in enumerate(labels):
            y = 230 + i * 160
            active = step == i
            color = self.highlight if active else self.text
            text = self.body_font.render(label, True, color)
            self.screen.blit(text, (220, y))

        self.draw_menu_options(260, 270, [o.label for o in GRID_OPTIONS], grid_idx, step == 0)
        self.draw_menu_options(260, 430, [o.label for o in SPEED_OPTIONS], speed_idx, step == 1)

        help_text = self.small_font.render("Use Up/Down or W/S, Enter to confirm, Q to quit", True, self.muted)
        self.screen.blit(help_text, (WINDOW_WIDTH // 2 - help_text.get_width() // 2, 590))
        pygame.display.flip()

    def draw_menu_options(self, x: int, y: int, options: list[str], selected: int, active: bool) -> None:
        for i, option in enumerate(options):
            is_selected = i == selected
            color = self.highlight if is_selected and active else self.text if is_selected else self.muted
            prefix = "> " if is_selected else "  "
            text = self.body_font.render(prefix + option, True, color)
            self.screen.blit(text, (x, y + i * 34))

    def reset_game(self) -> None:
        self.score = 0
        self.game_over = False
        self.tick_ms = self.speed_option.tick_ms
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.setup_board_metrics()

        cx = self.grid_option.cols // 2
        cy = self.grid_option.rows // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.spawn_food()
        self.last_update_ms = pygame.time.get_ticks()

    def setup_board_metrics(self) -> None:
        available_w = WINDOW_WIDTH - GRID_AREA_MARGIN * 2
        available_h = WINDOW_HEIGHT - TOP_BAR_HEIGHT - GRID_AREA_MARGIN * 2
        self.cell_size = min(
            available_w // self.grid_option.cols,
            available_h // self.grid_option.rows,
        )

        self.board_width_px = self.cell_size * self.grid_option.cols
        self.board_height_px = self.cell_size * self.grid_option.rows
        self.board_left = (WINDOW_WIDTH - self.board_width_px) // 2
        self.board_top = TOP_BAR_HEIGHT + (WINDOW_HEIGHT - TOP_BAR_HEIGHT - self.board_height_px) // 2

    def spawn_food(self) -> None:
        while True:
            candidate = (
                random.randrange(self.grid_option.cols),
                random.randrange(self.grid_option.rows),
            )
            if candidate not in self.snake:
                self.food = candidate
                return

    def update_game(self) -> None:
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        next_head = (head_x + dx, head_y + dy)

        out_of_bounds = (
            next_head[0] < 0
            or next_head[0] >= self.grid_option.cols
            or next_head[1] < 0
            or next_head[1] >= self.grid_option.rows
        )
        if out_of_bounds or next_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, next_head)
        if next_head == self.food:
            self.score += 10
            self.tick_ms = max(MIN_TICK_MS, self.tick_ms - 3)
            self.spawn_food()
        else:
            self.snake.pop()

    def draw(self) -> None:
        self.screen.fill(self.bg)
        self.draw_top_bar()
        self.draw_board()
        if self.game_over:
            self.draw_game_over_overlay()
        pygame.display.flip()

    def draw_top_bar(self) -> None:
        bar = pygame.Rect(0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, self.panel, bar)

        title = self.body_font.render("Snake", True, self.text)
        score_text = self.body_font.render(f"Score: {self.score}", True, self.text)
        info = self.small_font.render(
            f"Grid: {self.grid_option.cols}x{self.grid_option.rows} | Speed: {self.speed_option.label} | Q: Quit",
            True,
            self.muted,
        )

        self.screen.blit(title, (20, 14))
        self.screen.blit(score_text, (20, 44))
        self.screen.blit(info, (220, 30))

    def draw_board(self) -> None:
        board_rect = pygame.Rect(self.board_left, self.board_top, self.board_width_px, self.board_height_px)
        pygame.draw.rect(self.screen, (14, 18, 25), board_rect)
        pygame.draw.rect(self.screen, (88, 98, 120), board_rect, width=2)

        for col in range(1, self.grid_option.cols):
            x = self.board_left + col * self.cell_size
            pygame.draw.line(self.screen, self.grid_line, (x, self.board_top), (x, self.board_top + self.board_height_px))

        for row in range(1, self.grid_option.rows):
            y = self.board_top + row * self.cell_size
            pygame.draw.line(self.screen, self.grid_line, (self.board_left, y), (self.board_left + self.board_width_px, y))

        for i, segment in enumerate(self.snake):
            x, y = self.cell_to_pixel(segment)
            rect = pygame.Rect(x + 1, y + 1, self.cell_size - 2, self.cell_size - 2)
            color = self.snake_head if i == 0 else self.snake_body
            pygame.draw.rect(self.screen, color, rect, border_radius=4)

        fx, fy = self.cell_to_pixel(self.food)
        center = (fx + self.cell_size // 2, fy + self.cell_size // 2)
        radius = max(4, self.cell_size // 3)
        pygame.draw.circle(self.screen, self.food_color, center, radius)

    def draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(WINDOW_WIDTH // 2 - 230, WINDOW_HEIGHT // 2 - 110, 460, 220)
        pygame.draw.rect(self.screen, self.panel, panel, border_radius=10)
        pygame.draw.rect(self.screen, self.highlight, panel, width=2, border_radius=10)

        over = self.title_font.render("Game Over", True, self.text)
        score = self.body_font.render(f"Final score: {self.score}", True, self.text)
        hint = self.small_font.render("Press Enter/Space to restart", True, self.muted)

        self.screen.blit(over, (WINDOW_WIDTH // 2 - over.get_width() // 2, WINDOW_HEIGHT // 2 - 70))
        self.screen.blit(score, (WINDOW_WIDTH // 2 - score.get_width() // 2, WINDOW_HEIGHT // 2 - 10))
        self.screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT // 2 + 38))

    def cell_to_pixel(self, cell: tuple[int, int]) -> tuple[int, int]:
        return (
            self.board_left + cell[0] * self.cell_size,
            self.board_top + cell[1] * self.cell_size,
        )

    @staticmethod
    def direction_from_key(key: int) -> tuple[int, int] | None:
        if key in (pygame.K_UP, pygame.K_w):
            return (0, -1)
        if key in (pygame.K_DOWN, pygame.K_s):
            return (0, 1)
        if key in (pygame.K_LEFT, pygame.K_a):
            return (-1, 0)
        if key in (pygame.K_RIGHT, pygame.K_d):
            return (1, 0)
        return None

    @staticmethod
    def is_opposite(current: tuple[int, int], requested: tuple[int, int]) -> bool:
        return current[0] + requested[0] == 0 and current[1] + requested[1] == 0


if __name__ == "__main__":
    try:
        SnakeGame().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
