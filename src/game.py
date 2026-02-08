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

MEDIA_COIN = "mario_coin_sound.mp3"
MEDIA_LEVELUP = "mario_mushroom_levUp.mp3"
MEDIA_GAMEOVER = "mario_game_over.mp3"
MEDIA_LOSTLIFE = "mario_pipedown_life_lost.mp3"


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

        # Level-up feedback tracking
        self.level_up_timer = 0.0
        self.level_up_duration = 2.0  # Show message for 2 seconds

        # Load level-up sound effect
        self._load_media()

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

        # Spawn slow zone away from player start position
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randrange(40, self.w - SLOW_ZONE_WIDTH - 40)
            y = random.randrange(HUD_HEIGHT + 20, self.h - SLOW_ZONE_HEIGHT - 40)
            self.slow_zone = pygame.Rect(x, y, SLOW_ZONE_WIDTH, SLOW_ZONE_HEIGHT)

            # Check if slow zone overlaps with player start (give 150px buffer)
            player_start_x = self.w // 2 - PLAYER_SIZE
            player_start_y = HUD_HEIGHT + (self.h - HUD_HEIGHT) // 2 - PLAYER_SIZE
            player_start_rect = pygame.Rect(
                player_start_x - 75,
                player_start_y - 75,
                PLAYER_SIZE + 150,
                PLAYER_SIZE + 150,
            )

            if not self.slow_zone.colliderect(player_start_rect):
                break  # Valid position found

        self.score = 0
        self.alive_time = 0.0

        self.enemy_rects: list[pygame.Rect] = []
        self.enemy_vs: list[pygame.Vector2] = []

        for _ in range(self.level):
            # Try to spawn enemy away from player
            max_attempts = 50
            for _ in range(max_attempts):
                rect = pygame.Rect(
                    random.randrange(40, self.w - 40),
                    random.randrange(HUD_HEIGHT + 20, self.h - 40),
                    ENEMY_SIZE,
                    ENEMY_SIZE,
                )

                # Check distance from player (at least 180 pixels away)
                distance = (
                    (rect.centerx - self.player.centerx) ** 2
                    + (rect.centery - self.player.centery) ** 2
                ) ** 0.5

                if distance >= 180:
                    break  # Good position found

            vel = pygame.Vector2(
                random.choice([-1, 1]) * ENEMY_SPEED_X,
                random.choice([-1, 1]) * ENEMY_SPEED_Y,
            )
            self.enemy_rects.append(rect)
            self.enemy_vs.append(vel)

        self.coin = self._spawn_coin()

    def _spawn_coin(self) -> pygame.Rect:
        # Keep coin away from top HUD area, slow zone and player
        max_attempts = 100
        for _ in range(max_attempts):
            coin = pygame.Rect(
                random.randrange(20, self.w - 20),
                random.randrange(HUD_HEIGHT + 30, self.h - 20),
                COIN_SIZE,
                COIN_SIZE,
            )

            # Check if coin is too close to player (within 100 pixels)
            player_distance = (
                (coin.centerx - self.player.centerx) ** 2
                + (coin.centery - self.player.centery) ** 2
            ) ** 0.5
            if player_distance < 100:
                continue

            # Check if coin overlaps with slow zone
            if coin.colliderect(self.slow_zone):
                continue

            # Valid position found
            return coin

        # Fallback if no valid position found after max_attempts
        return pygame.Rect(
            random.randrange(20, self.w - 20),
            random.randrange(HUD_HEIGHT + 30, self.h - 20),
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
                    # Respawn enemies away from player
                    for i, r in enumerate(self.enemy_rects):
                        max_attempts = 50
                        for _ in range(max_attempts):
                            new_x = random.randrange(40, self.w - 40)
                            new_y = random.randrange(HUD_HEIGHT + 20, self.h - 40)

                            # Check distance from player (at least 180 pixels away)
                            distance = (
                                (new_x - self.player.centerx) ** 2
                                + (new_y - self.player.centery) ** 2
                            ) ** 0.5

                            if distance >= 180:
                                r.x = new_x
                                r.y = new_y
                                break  # Good position found

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
        """Main game update loop - delegates to helper methods."""
        if self.state != STATE_PLAYING or self.pause_state:
            return

        # Update level-up timer
        if self.level_up_timer > 0:
            self.level_up_timer -= dt

        self._update_player(dt)

        self._update_enemies(dt)
        self._handle_coin_collision()
        self._handle_enemy_collision()

    def draw(self) -> None:
        self.screen.fill(COLORS.bg)

        if self.state == STATE_TITLE:
            self._draw_title()
        elif self.state == STATE_PLAYING:
            self._draw_playing()
        else:
            self._draw_gameover()

    def _draw_hud(self) -> None:
        panel = pygame.Rect(12, 12, self.w - 24, HUD_HEIGHT - 20)
        pygame.draw.rect(self.screen, COLORS.panel, panel, border_radius=10)

        coins_needed = self.to_next_level_coins - self.curr_level_coins
        text = (
            f"Player: {self.p_name} | Score: {self.score} | "
            f"High: {self.high_score} | Lives: {self.lives} | "
            f"Level: {self.level} | Coins to next level: {coins_needed}"
        )
        surf = self.font.render(text, True, COLORS.text)
        self.screen.blit(
            surf, (panel.x + 12, panel.y + (panel.height - surf.get_height()) // 2)
        )

    def _draw_playing(self) -> None:
        self._draw_hud()

        pygame.draw.rect(
            self.screen, self.slow_zone_color, self.slow_zone, border_radius=12
        )
        pygame.draw.rect(self.screen, COLORS.coin, self.coin, border_radius=7)

        for r in self.enemy_rects:
            pygame.draw.rect(self.screen, COLORS.enemy, r, border_radius=8)

        pygame.draw.rect(self.screen, COLORS.player, self.player, border_radius=8)

        # Draw pause message LAST so it's on top
        if self.pause_state == PAUSE_LOST_LIFE:
            msg = self.big_font.render(
                "Life lost! Enter to continue, Esc to quit", True, (255, 100, 100)
            )
            self.screen.blit(
                msg, (self.w // 2 - msg.get_width() // 2, self.h // 2 - 50)
            )

        # Draw level-up message with flash effect
        if self.level_up_timer > 0:
            # Calculate alpha for fade effect (bright at start, fades out)
            alpha = int(255 * (self.level_up_timer / self.level_up_duration))
            color = (50, 255, 50) if alpha > 128 else (100, 220, 100)

            msg = self.big_font.render(f"LEVEL {self.level}!", True, color)
            self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, HUD_HEIGHT + 80))

    def _draw_title(self) -> None:
        title = self.big_font.render("Intro Arcade", True, COLORS.text)
        hint = self.font.render(
            "Move with arrows/WASD. Avoid red. Collect gold.", True, COLORS.text
        )
        hint2 = self.font.render(
            "Press Enter to start. Esc to quit.", True, COLORS.text
        )
        yModHH = HUD_HEIGHT + 100

        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, yModHH))
        self.screen.blit(hint, (self.w // 2 - hint.get_width() // 2, yModHH + 60))
        self.screen.blit(hint2, (self.w // 2 - hint2.get_width() // 2, yModHH + 90))

    def _draw_gameover(self) -> None:
        yModHH = HUD_HEIGHT + 100
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
        # Spawn new enemy away from player
        max_attempts = 50
        for _ in range(max_attempts):
            rect = pygame.Rect(
                random.randrange(40, self.w - 40),
                random.randrange(HUD_HEIGHT + 20, self.h - 40),
                ENEMY_SIZE,
                ENEMY_SIZE,
            )

            # Check distance from player (at least 180 pixels away)
            distance = (
                (rect.centerx - self.player.centerx) ** 2
                + (rect.centery - self.player.centery) ** 2
            ) ** 0.5

            if distance >= 180:
                break  # Good position found

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
        # Spawn slow zone away from player and coin
        max_attempts = 100
        for _ in range(max_attempts):
            self.slow_zone = pygame.Rect(
                random.randrange(80, self.w - SLOW_ZONE_WIDTH),
                random.randrange(HUD_HEIGHT + 20, self.h - SLOW_ZONE_HEIGHT),
                SLOW_ZONE_WIDTH,
                SLOW_ZONE_HEIGHT,
            )

            # Check distance from player (at least 120 pixels away)
            player_distance = (
                (self.slow_zone.centerx - self.player.centerx) ** 2
                + (self.slow_zone.centery - self.player.centery) ** 2
            ) ** 0.5
            if player_distance < 120:
                continue

            # Check distance from coin (at least 80 pixels away)
            coin_distance = (
                (self.slow_zone.centerx - self.coin.centerx) ** 2
                + (self.slow_zone.centery - self.coin.centery) ** 2
            ) ** 0.5
            if coin_distance < 80:
                continue

            # Valid position found
            break

    def _update_player(self, dt: float) -> None:
        """Handle player movement and input."""
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

    def _update_enemies(self, dt: float) -> None:
        """Handle enemy movement and bouncing."""
        bounds = pygame.Rect(0, HUD_HEIGHT, self.w, self.h - HUD_HEIGHT)
        for i, r in enumerate(self.enemy_rects):
            v = self.enemy_vs[i]
            r.x += int(v.x * dt)
            r.y += int(v.y * dt)

            if r.left <= bounds.left or r.right >= bounds.right:
                v.x *= -1
            if r.top <= bounds.top or r.bottom >= bounds.bottom:
                v.y *= -1

    def _handle_coin_collision(self) -> None:
        """Check and handle coin collection."""
        if self.player.colliderect(self.coin):
            self.score += 1
            self.curr_level_coins += 1
            self.coin = self._spawn_coin()

            # Play coin sound
            if self.coin_sound:
                self.coin_sound.play()

            if self.curr_level_coins >= self.to_next_level_coins:
                self.curr_level_coins = 0
                self.level += 1
                self._next_level()
                # Trigger level-up visual feedback
                self.level_up_timer = self.level_up_duration

                # Play level-up sound
                if self.level_up_sound:
                    self.level_up_sound.play()

    def _handle_enemy_collision(self) -> None:
        """Check and handle player hitting an enemy."""
        if self.player.collidelist(self.enemy_rects) != -1:
            if self.lives > 1:
                self.lives -= 1
                # Pause for a lost life
                self.pause_state = PAUSE_LOST_LIFE
                self.player.center = (
                    self.w // 2,
                    HUD_HEIGHT + (self.h - HUD_HEIGHT) // 2,
                )
                self.player_v.update(0, 0)
                # Play lost life sound
                if self.lostlife_sound:
                    self.lostlife_sound.play()
            else:
                # No more lives, game over
                self.state = STATE_GAMEOVER
                if self.score > self.high_score:
                    self.high_score = self.score
                    self._save_high_score()

                # Play game over sound
                if self.gameover_sound:
                    self.gameover_sound.play()

    def _load_media(self) -> None:
        """Load all sound effects from assets/media folder."""
        media_path = Path(__file__).resolve().parent.parent / "assets" / "media"

        # Adjust volume: self.coin_sound.set_volume(0.3)

        # Load coin sound
        try:
            coin_path = media_path / MEDIA_COIN
            self.coin_sound = pygame.mixer.Sound(coin_path)

        except Exception as e:
            print(f"Could not load coin sound: {e}")
            self.coin_sound = None

        # Load level-up sound
        try:
            levelup_path = media_path / MEDIA_LEVELUP
            self.level_up_sound = pygame.mixer.Sound(levelup_path)
        except Exception as e:
            print(f"Could not load level-up sound: {e}")
            self.level_up_sound = None

        # Load game over sound
        try:
            gameover_path = media_path / MEDIA_GAMEOVER
            self.gameover_sound = pygame.mixer.Sound(gameover_path)
        except Exception as e:
            print(f"Could not load game over sound: {e}")
            self.gameover_sound = None

        # Load lost life sound
        try:
            lostlife_path = media_path / MEDIA_LOSTLIFE
            self.lostlife_sound = pygame.mixer.Sound(lostlife_path)
        except Exception as e:
            print(f"Could not load lost life sound: {e}")
            self.lostlife_sound = None
