from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import pygame


@dataclass
class Colors:
    bg: tuple[int, int, int] = (22, 24, 28)
    panel: tuple[int, int, int] = (34, 38, 46)
    text: tuple[int, int, int] = (236, 239, 244)

    player: tuple[int, int, int] = (136, 192, 208)
    enemy: tuple[int, int, int] = (191, 97, 106)
    coin: tuple[int, int, int] = (235, 203, 139)


FPS = 60
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

HUD_HEIGHT = 60

PLAYER_SIZE = 32
PLAYER_SPEED = 360.0
PLAYER_SLOW_SPEED = 133.0

ENEMY_SIZE = 36
ENEMY_SPEED_X = 220
ENEMY_SPEED_Y = 180

COIN_SIZE = 18
COINS_PER_LEVEL = 5

SLOW_ZONE_WIDTH = 260
SLOW_ZONE_HEIGHT = 80

PAUSE_LOST_LIFE = "lost_life"
STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_GAMEOVER = "gameover"


COLORS = Colors()


class Game:
    def __init__(self) -> None:
        self.fps = FPS
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

        self.screen = pygame.display.set_mode((self.w, self.h))
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 48)

        self.save_path = Path(__file__).resolve().parent.parent / "data" / "save.json"
        self.high_score = self._load_high_score()

        self.state: str = STATE_TITLE  # title | playing | gameover
        self.pause_state: str | None = None

        self.p_name = "Mahran"
        self.lives = 3
        self.level = 1
        self.curr_level_coins = 0
        self.to_next_level_coins = COINS_PER_LEVEL

        self.slow_zone_color = (80, 120, 200)

        self._reset_run()

    def _load_high_score(self) -> int:
        if not self.save_path.exists():
            return 0
        try:
            raw = json.loads(self.save_path.read_text(encoding="utf-8"))
            return int(raw.get("high_score", 0))
        except Exception:
            return 0

    def _save_high_score(self) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(
            json.dumps({"high_score": int(self.high_score)}, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    def _reset_run(self) -> None:
        # set player position, reuse in case player has remaining lives in Update method if collision happens
        self.player = pygame.Rect(
            self.w // 2 - PLAYER_SIZE,
            HUD_HEIGHT + (self.h - HUD_HEIGHT) // 2 - PLAYER_SIZE,
            PLAYER_SIZE,
            PLAYER_SIZE,
        )
        self.player_v = pygame.Vector2(0, 0)

        x = random.randrange(40, self.w - SLOW_ZONE_WIDTH - 40)
        y = random.randrange(80, self.h - SLOW_ZONE_HEIGHT - 40)
        self.slow_zone = pygame.Rect(x, y, SLOW_ZONE_WIDTH, SLOW_ZONE_HEIGHT)

        self.score = 0
        self.alive_time = 0.0

        self.enemy_rects: list[pygame.Rect] = []
        self.enemy_vs: list[pygame.Vector2] = []

        for _ in range(self.level):
            rect = pygame.Rect(
                random.randrange(40, self.w - 40),
                random.randrange(80, self.h - 40),
                ENEMY_SIZE,
                ENEMY_SIZE,
            )
            vel = pygame.Vector2(
                random.choice([-1, 1]) * ENEMY_SPEED_X,
                random.choice([-1, 1]) * ENEMY_SPEED_Y,
            )
            self.enemy_rects.append(rect)
            self.enemy_vs.append(vel)

        self.coin = self._spawn_coin()

    def _spawn_coin(self) -> pygame.Rect:
        # Keep coin away from top HUD area.
        return pygame.Rect(
            random.randrange(20, self.w - 20),
            random.randrange(HUD_HEIGHT+30, self.h - 20),
            COIN_SIZE,
            COIN_SIZE,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN:
            if self.pause_state == PAUSE_LOST_LIFE:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif event.key == pygame.K_RETURN:
                    self.pause_state = None
                    for i, r in enumerate(self.enemy_rects):
                        r.x = random.randrange(40, self.w - 40)
                        r.y = random.randrange(80, self.h - 40)
                        self.enemy_vs[i] = pygame.Vector2(
                            random.choice([-1, 1]) * ENEMY_SPEED_X,
                            random.choice([-1, 1]) * ENEMY_SPEED_Y,
                        )
                    self.coin = self._spawn_coin()
                return

            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

            elif event.key == pygame.K_RETURN:
                if self.state in (STATE_TITLE, STATE_GAMEOVER):
                    self.lives = 3
                    self.level = 1
                    self.curr_level_coins = 0
                    self._reset_run()
                    self.state = STATE_PLAYING

    def update(self, dt: float) -> None:
        if self.state != STATE_PLAYING or self.pause_state:
            return

        keys = pygame.key.get_pressed()
        input_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        input_y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (
            keys[pygame.K_UP] or keys[pygame.K_w]
        )

        speed = (
            PLAYER_SLOW_SPEED
            if self.player.colliderect(self.slow_zone)
            else PLAYER_SPEED
        )
        self.player_v.update(input_x * speed, input_y * speed)

        self.player.x += int(self.player_v.x * dt)
        self.player.y += int(self.player_v.y * dt)
        self.player.clamp_ip(pygame.Rect(0, HUD_HEIGHT, self.w, self.h - HUD_HEIGHT))

        bounds = pygame.Rect(0, HUD_HEIGHT, self.w, self.h - HUD_HEIGHT)
        for i, r in enumerate(self.enemy_rects):
            v = self.enemy_vs[i]
            r.x += int(v.x * dt)
            r.y += int(v.y * dt)

            if r.left <= bounds.left or r.right >= bounds.right:
                v.x *= -1
            if r.top <= bounds.top or r.bottom >= bounds.bottom:
                v.y *= -1

        if self.player.colliderect(self.coin):
            self.score += 1
            self.curr_level_coins += 1
            self.coin = self._spawn_coin()

            if self.curr_level_coins >= self.to_next_level_coins:
                self.curr_level_coins = 0
                #move to the next level, add enemy, update flow zone
                self.level += 1
                self._next_level()

        if self.player.collidelist(self.enemy_rects) != -1:
            if self.lives > 1:
                self.lives -= 1
                #pause for a lost life
                self.pause_state = PAUSE_LOST_LIFE
                self.player.center = (
                    self.w // 2,
                    HUD_HEIGHT + (self.h - HUD_HEIGHT) // 2,
                )
                self.player_v.update(0, 0)
            else:
                # no more lives, game over
                self.state = STATE_GAMEOVER
                if self.score > self.high_score:
                    self.high_score = self.score
                    self._save_high_score()

    def draw(self) -> None:
        self.screen.fill(COLORS.bg)

        if self.state == STATE_TITLE:
            self._draw_title()
        elif self.state == STATE_PLAYING:
            self._draw_playing()
        else:
            self._draw_gameover()

    def _draw_hud(self) -> None:
        panel = pygame.Rect(12, 12, self.w-24, HUD_HEIGHT-20)
        pygame.draw.rect(self.screen, COLORS.panel, panel, border_radius=10)

        text = (
            f"Player: {self.p_name}   Score: {self.score}   "
            f"High: {self.high_score}   Lives: {self.lives}   Level: {self.level}"
        )
        surf = self.font.render(text, True, COLORS.text)
        self.screen.blit(surf, (panel.x + 12, panel.y + (panel.height - surf.get_height()) //2 ))

    def _draw_playing(self) -> None:
        if self.pause_state == PAUSE_LOST_LIFE:
            msg = self.big_font.render(
                "Life lost! Enter to continue, Esc to quit", True, (255, 100, 100)
            )
            self.screen.blit(
                msg,
                (self.w // 2 - msg.get_width() // 2, self.h // 2 - 50),
            )

        self._draw_hud()
        pygame.draw.rect(
            self.screen, self.slow_zone_color, self.slow_zone, border_radius=12
        )
        pygame.draw.rect(self.screen, COLORS.coin, self.coin, border_radius=7)

        for r in self.enemy_rects:
            pygame.draw.rect(self.screen, COLORS.enemy, r, border_radius=8)

        pygame.draw.rect(self.screen, COLORS.player, self.player, border_radius=8)

    def _draw_title(self) -> None:
        title = self.big_font.render("Intro Arcade", True, COLORS.text)
        hint = self.font.render(
            "Move with arrows/WASD. Avoid red. Collect gold.", True, COLORS.text
        )
        hint2 = self.font.render(
            "Press Enter to start. Esc to quit.", True, COLORS.text
        )
        yModHH= HUD_HEIGHT +100

        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, yModHH))
        self.screen.blit(hint, (self.w // 2 - hint.get_width() // 2, yModHH + 60 ))
        self.screen.blit(hint2, (self.w // 2 - hint2.get_width() // 2, yModHH + 90))

    def _draw_gameover(self) -> None:
        yModHH= HUD_HEIGHT +100
        title = self.big_font.render("Game Over", True, COLORS.text)
        msg = self.font.render(
            f"Score: {self.score}   High: {self.high_score}", True, COLORS.text
        )
        hint = self.font.render(
            "Press Enter to play again. Esc to quit.", True, COLORS.text
        )

        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, yModHH))
        self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, yModHH + 60))
        self.screen.blit(hint, (self.w // 2 - hint.get_width() // 2, yModHH + 90))

    def _next_level(self):
        rect = pygame.Rect(
            random.randrange(40, self.w - 40),
            random.randrange(80, self.h - 40),
            ENEMY_SIZE,
            ENEMY_SIZE,
        )
        vel = pygame.Vector2(
            random.choice([-1, 1]) * ENEMY_SPEED_X,
            random.choice([-1, 1]) * ENEMY_SPEED_Y,
        )

        self.enemy_rects.append(rect)
        self.enemy_vs.append(vel)

        self.slow_zone_color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
        )
        self.slow_zone = pygame.Rect(
            random.randrange(80, self.w - SLOW_ZONE_WIDTH),
            random.randrange(HUD_HEIGHT + 20, self.h - SLOW_ZONE_HEIGHT),
            SLOW_ZONE_WIDTH,
            SLOW_ZONE_HEIGHT,
        )
