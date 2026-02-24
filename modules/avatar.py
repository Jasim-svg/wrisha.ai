"""
modules/avatar.py — Animated Avatar UI for Wrisha v3.0

Premium Upgrades:
  - Dark-purple gradient background
  - Stylish name header with glow effect
  - HUD overlay: mood emoji, user emotion, session stats
  - Subtitle panel: scrolling text of what Wrisha says
  - Idle breathing animation (vertical bob)
  - Talking animation (frame toggling + lip-sync pulse dots)
  - Smooth sprite cross-fade between emotion states
  - Floating sparkle particles in background
  - Transition flash on mood change
"""

import pygame
import math
import random
import time
import os
import config

# ── Color Palette ─────────────────────────────────────────────────────────────
BG_TOP        = (14,  8,  28)      # Deep midnight purple
BG_BOTTOM     = (35, 18, 65)      # Rich violet
ACCENT        = (155,  90, 255)   # Vivid purple
ACCENT2       = (90,  200, 255)   # Cyan highlight
TEXT_COLOR    = (230, 220, 255)   # Soft lavender white
SUBTITLE_BG   = (20,  10, 40, 180)
HUD_BG        = (10,   5, 25, 160)
SPARKLE_CLR   = [(255,220,255), (200,160,255), (100,220,255), (255,255,200)]


class Particle:
    """A tiny floating sparkle."""
    __slots__ = ["x", "y", "vx", "vy", "life", "max_life", "color", "size"]

    def __init__(self, w, h):
        self.reset(w, h)

    def reset(self, w, h):
        self.x       = random.randint(0, w)
        self.y       = random.randint(0, h)
        self.vx      = random.uniform(-0.3, 0.3)
        self.vy      = random.uniform(-0.8, -0.2)
        self.max_life = random.randint(120, 300)
        self.life    = self.max_life
        self.color   = random.choice(SPARKLE_CLR)
        self.size    = random.randint(1, 3)

    def update(self, w, h):
        self.x   += self.vx
        self.y   += self.vy
        self.life -= 1
        if self.life <= 0 or self.y < -10:
            self.reset(w, h)

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        r, g, b = self.color
        try:
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (self.size, self.size), self.size)
            surf.blit(s, (int(self.x), int(self.y)))
        except Exception:
            pass


class Avatar:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.W, self.H = config.WINDOW_W, config.WINDOW_H
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # State
        self.emotion        = "neutral"
        self.is_speaking    = False
        self.subtitle_text  = ""
        self.user_emotion   = "neutral"
        self.session_stats  = {}
        self.face_detected  = False
        self.eye_contact    = False

        # Animation
        self._tick          = 0
        self._bob_offset    = 0.0
        self._prev_sprite   = None
        self._curr_sprite   = None
        self._blend_alpha   = 255
        self._blend_start   = 0
        self._flash_alpha   = 0
        self._mood_emoji    = "😊"

        # Particles
        self._particles = [Particle(self.W, self.H) for _ in range(60)]

        # Fonts
        self._load_fonts()

        # Assets
        self.assets = {}
        self._load_assets()

        # Gradient surface (precomputed)
        self._gradient = self._make_gradient()

        print("Avatar: ✅ Premium UI initialized")

    # ─── Setup ───────────────────────────────────────────────────

    def _load_fonts(self):
        try:
            # Try to load system Japanese / friendly font
            self.font_title    = pygame.font.SysFont("segoeui", 28, bold=True)
            self.font_subtitle = pygame.font.SysFont("segoeui", 20)
            self.font_hud      = pygame.font.SysFont("consolas", 16)
            self.font_emoji    = pygame.font.SysFont("segoeuiemoji", 26)
        except Exception:
            self.font_title    = pygame.font.Font(None, 32)
            self.font_subtitle = pygame.font.Font(None, 22)
            self.font_hud      = pygame.font.Font(None, 18)
            self.font_emoji    = pygame.font.Font(None, 28)

    def _load_assets(self):
        asset_dir = "assets"
        TARGET_H  = int(self.H * 0.72)

        def load(name):
            path = os.path.join(asset_dir, name)
            if not os.path.exists(path):
                print(f"Avatar: ⚠ '{path}' not found — using placeholder")
                surf = pygame.Surface((300, TARGET_H), pygame.SRCALPHA)
                surf.fill((130, 80, 200, 180))
                return surf
            img = pygame.image.load(path).convert_alpha()
            sf  = TARGET_H / img.get_height()
            return pygame.transform.smoothscale(img, (int(img.get_width() * sf), TARGET_H))

        self.assets["neutral"]  = load("body_idle.png")
        self.assets["talking"]  = load("body_talking.png")
        self.assets["happy"]    = load("body_happy.png")
        self.assets["sad"]      = load("body_sad.png")
        self.assets["excited"]  = self.assets["happy"]   # reuse
        self.assets["curious"]  = self.assets["neutral"] # reuse
        self.assets["shy"]      = self.assets["happy"]   # slight tint applied dynamically
        self.assets["angry"]    = self.assets["sad"]     # reuse
        self.assets["loving"]   = self.assets["happy"]   # reuse
        self.assets["peaceful"] = self.assets["neutral"] # reuse

        self._curr_sprite = self.assets["neutral"]

    def _make_gradient(self) -> pygame.Surface:
        """Precompute vertical gradient background."""
        surf = pygame.Surface((self.W, self.H))
        for y in range(self.H):
            t  = y / self.H
            r  = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
            g  = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
            b  = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.W, y))
        return surf

    # ─── State Updates ───────────────────────────────────────────

    def update_expression(self, emotion: str, is_speaking: bool = False,
                          user_emotion: str = "neutral", mood_emoji: str = "😊",
                          face_detected: bool = False, eye_contact: bool = False):
        prev_emotion = self.emotion
        self.emotion      = emotion
        self.is_speaking  = is_speaking
        self.user_emotion = user_emotion
        self._mood_emoji  = mood_emoji
        self.face_detected = face_detected
        self.eye_contact   = eye_contact

        # Trigger cross-fade on emotion change
        if emotion != prev_emotion:
            self._prev_sprite  = self._curr_sprite
            self._blend_alpha  = 0
            self._blend_start  = self._tick
            self._flash_alpha  = 80   # Mood-change flash

    def set_subtitle(self, text: str):
        self.subtitle_text = text

    def update_stats(self, stats: dict):
        self.session_stats = stats

    # ─── Drawing ─────────────────────────────────────────────────

    def draw(self) -> bool:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        self._tick += 1

        # ── Background ───────────────────────────────────────────
        self.screen.blit(self._gradient, (0, 0))

        # ── Particles ────────────────────────────────────────────
        for p in self._particles:
            p.update(self.W, self.H)
            p.draw(self.screen)

        # ── Title Header ─────────────────────────────────────────
        self._draw_header()

        # ── Avatar Sprite + Breathing ────────────────────────────
        self._draw_sprite()

        # ── Mood flash overlay ───────────────────────────────────
        if self._flash_alpha > 0:
            flash_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            flash_surf.fill((*ACCENT, self._flash_alpha))
            self.screen.blit(flash_surf, (0, 0))
            self._flash_alpha = max(0, self._flash_alpha - 5)

        # ── HUD Panel ────────────────────────────────────────────
        self._draw_hud()

        # ── Talking Indicator ────────────────────────────────────
        if self.is_speaking:
            self._draw_talking_dots()

        # ── Subtitle Panel ───────────────────────────────────────
        if self.subtitle_text:
            self._draw_subtitle()

        pygame.display.flip()
        self.clock.tick(config.TARGET_FPS)
        return True

    def _draw_header(self):
        HEADER_H = 64
        # Background bar
        bar = pygame.Surface((self.W, HEADER_H), pygame.SRCALPHA)
        bar.fill((20, 8, 45, 200))
        self.screen.blit(bar, (0, 0))

        # Glow accent line
        pygame.draw.line(self.screen, ACCENT, (0, HEADER_H - 1), (self.W, HEADER_H - 1), 2)

        # Title
        title_surf = self.font_title.render(f"✨ {config.PERSONA_NAME} AI", True, TEXT_COLOR)
        self.screen.blit(title_surf, (20, 18))

        # Status pill (right side)
        pill_text = "● LIVE" if self.face_detected else "● WAITING"
        pill_clr  = (100, 255, 140) if self.face_detected else (180, 100, 100)
        pill_surf = self.font_hud.render(pill_text, True, pill_clr)
        self.screen.blit(pill_surf, (self.W - pill_surf.get_width() - 16, 24))

    def _draw_sprite(self):
        # Select target sprite
        if self.is_speaking:
            # Alternate idle/talking for lip-sync
            sprite = self.assets.get(
                "talking" if (self._tick // 8) % 2 == 0 else "neutral"
            )
        else:
            sprite = self.assets.get(self.emotion, self.assets.get("neutral"))

        self._curr_sprite = sprite

        if sprite is None:
            return

        # Breathing bob
        bob = math.sin(self._tick * 0.03) * 6   # ±6px vertical sway

        # Cross-fade blend
        blend = min(255, (self._tick - self._blend_start) * 12)
        self._blend_alpha = blend

        cx = self.W // 2
        cy = int(self.H * 0.52 + bob)
        HEADER_H = 64

        rect = sprite.get_rect(center=(cx, cy))

        if self._prev_sprite and self._blend_alpha < 255:
            prev_rect = self._prev_sprite.get_rect(center=(cx, cy))
            tmp = self._prev_sprite.copy()
            tmp.set_alpha(255 - self._blend_alpha)
            self.screen.blit(tmp, prev_rect)

            tmp2 = sprite.copy()
            tmp2.set_alpha(self._blend_alpha)
            self.screen.blit(tmp2, rect)
        else:
            self.screen.blit(sprite, rect)

    def _draw_hud(self):
        """Small info panel in bottom-left corner."""
        lines = [
            f"{self._mood_emoji}  Wrisha: {self.emotion}",
            f"👤 User: {self.user_emotion}",
        ]
        if self.eye_contact:
            lines.append("👁️  Eye contact ✓")
        if self.session_stats.get("memory_facts"):
            lines.append(f"🧠 {self.session_stats['memory_facts']} memories")

        pad   = 10
        lh    = 22
        panel_h = len(lines) * lh + pad * 2
        panel_w = 210

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 5, 25, 160))
        pygame.draw.rect(panel, ACCENT, (0, 0, panel_w, panel_h), 1, border_radius=8)

        for i, line in enumerate(lines):
            try:
                s = self.font_hud.render(line, True, TEXT_COLOR)
                panel.blit(s, (pad, pad + i * lh))
            except Exception:
                pass

        self.screen.blit(panel, (10, self.H - panel_h - 10))

    def _draw_talking_dots(self):
        """Animated pulsing dots during speech."""
        cx  = self.W // 2
        cy  = self.H - 90
        for i in range(3):
            phase = (self._tick + i * 10) % 30
            r     = 5 + int(3 * math.sin(phase * 0.2 * math.pi))
            alpha = 200 if phase < 20 else 100
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*ACCENT, alpha), (r + 1, r + 1), r)
            self.screen.blit(s, (cx - 30 + i * 30 - r, cy - r))

    def _draw_subtitle(self):
        """Semi-transparent subtitle strip at the bottom."""
        MAX_W   = self.W - 40
        pan_h   = 70
        panel   = pygame.Surface((self.W, pan_h), pygame.SRCALPHA)
        panel.fill((18, 8, 38, 200))
        pygame.draw.line(panel, ACCENT2, (0, 0), (self.W, 0), 1)

        # Word-wrap if too long
        words   = self.subtitle_text.split()
        lines   = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if self.font_subtitle.size(test)[0] < MAX_W:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        lines = lines[-2:]  # Max 2 lines

        for i, line in enumerate(lines):
            surf = self.font_subtitle.render(line, True, TEXT_COLOR)
            panel.blit(surf, ((self.W - surf.get_width()) // 2, 10 + i * 26))

        self.screen.blit(panel, (0, self.H - pan_h))

    # ─── Cleanup ─────────────────────────────────────────────────

    def quit(self):
        pygame.quit()
