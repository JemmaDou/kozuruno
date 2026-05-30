import pygame
import math
import sys
import os

# macOS 显示驱动（如果在 Windows/Linux 上运行，可注释掉下一行）
os.environ['SDL_VIDEODRIVER'] = 'cocoa'

pygame.init()
WIDTH, HEIGHT = 1400, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI投掷模拟：12米无人机目标 + 数据看板")
clock = pygame.time.Clock()

try:
    font = pygame.font.SysFont("stheitilight", 24)
    font_small = pygame.font.SysFont("stheitilight", 18)
    font_big = pygame.font.SysFont("stheitilight", 32)
    font_data = pygame.font.SysFont("stheitilight", 16)
except:
    font = pygame.font.SysFont("arial", 24)
    font_small = pygame.font.SysFont("arial", 18)
    font_big = pygame.font.SysFont("arial", 32)
    font_data = pygame.font.SysFont("arial", 16)

SCALE = 60
G = 9.8
RHO = 1.225
GROUND_Y = 500
SLING_X, SLING_Y = 150, GROUND_Y - 50
TARGET_X = SLING_X + 12 * SCALE
TARGET_Y = GROUND_Y - 40

# ==================== 物理参数优化 ====================
OBJECTS = [
    {
        "name": "篮球",
        "mass": 0.62, "d": 0.24, "Cd": 0.47,
        "color": (255, 140, 0), "r": 12, "max_v": 12,
        "hit_rate": 0.30
    },
    {
        "name": "网球",
        "mass": 0.057, "d": 0.067, "Cd": 0.50,
        "color": (50, 205, 50), "r": 6, "max_v": 40,
        "hit_rate": 0.15
    },
    {
        "name": "棒球",
        "mass": 0.145, "d": 0.074, "Cd": 0.35,
        "color": (255, 215, 0), "r": 7, "max_v": 35,
        "hit_rate": 0.40
    },
    {
        "name": "箭",
        "mass": 0.025, "d": 0.009, "Cd": 0.75,
        "color": (139, 69, 19), "r": 4, "max_v": 55,
        "hit_rate": 0.925
    },
]

current_idx = 0
projectiles = []
dragging = False
drag_current = None

# ==================== 数据统计 ====================
stats = {
    "total": [0, 0, 0, 0],
    "hits": [0, 0, 0, 0],
    "distances": [[], [], [], []]
}

def update_stats(obj_idx, hit, distance):
    stats["total"][obj_idx] += 1
    if hit:
        stats["hits"][obj_idx] += 1
    stats["distances"][obj_idx].append(distance)
    if len(stats["distances"][obj_idx]) > 20:
        stats["distances"][obj_idx].pop(0)

def draw_data_panel():
    panel_x = 950
    panel_y = 50
    panel_w = 420
    panel_h = 600

    pygame.draw.rect(screen, (245, 245, 250), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
    pygame.draw.rect(screen, (200, 200, 220), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

    title = font.render("实时数据统计", True, (0, 0, 100))
    screen.blit(title, (panel_x + 20, panel_y + 20))

    for i, obj in enumerate(OBJECTS):
        y = panel_y + 70 + i * 130

        pygame.draw.circle(screen, obj["color"], (panel_x + 30, y + 10), 10)
        name_text = font.render(obj["name"], True, (0, 0, 0))
        screen.blit(name_text, (panel_x + 50, y))

        total = stats["total"][i]
        hits = stats["hits"][i]
        actual_rate = (hits / total * 100) if total > 0 else 0
        ppt_rate = obj["hit_rate"] * 100

        rate_text = font_small.render(f"发射{total}次 命中{hits}次", True, (80, 80, 80))
        screen.blit(rate_text, (panel_x + 30, y + 30))

        rate_text2 = font_small.render(f"成功率{actual_rate:.1f}% (目标:{ppt_rate:.1f}%)", True, (80, 80, 80))
        screen.blit(rate_text2, (panel_x + 30, y + 50))

        bar_max_w = 200
        bar_h = 20
        bar_y = y + 75
        pygame.draw.rect(screen, (220, 220, 220), (panel_x + 30, bar_y, bar_max_w, bar_h), border_radius=5)
        if total > 0:
            bar_w = int(bar_max_w * (hits / total))
            pygame.draw.rect(screen, obj["color"], (panel_x + 30, bar_y, bar_w, bar_h), border_radius=5)

        dists = stats["distances"][i]
        if dists:
            hist_y = y + 105
            for j, d in enumerate(dists[-5:]):
                dot_x = panel_x + 30 + j * 40
                if d < 0.5:
                    color = (0, 200, 0)
                elif d < 2:
                    color = (255, 200, 0)
                else:
                    color = (255, 0, 0)
                pygame.draw.circle(screen, color, (dot_x, hist_y), 8)
                dot_text = font_data.render(f"{d:.1f}", True, (100, 100, 100))
                screen.blit(dot_text, (dot_x - 10, hist_y + 12))

def draw_background():
    screen.fill((240, 248, 255))
    pygame.draw.rect(screen, (34, 139, 34), (0, GROUND_Y, 900, HEIGHT - GROUND_Y))
    pygame.draw.line(screen, (0, 0, 0), (0, GROUND_Y), (900, GROUND_Y), 3)

    for m in range(0, 15, 2):
        x = SLING_X + m * SCALE
        pygame.draw.line(screen, (80, 80, 80), (x, GROUND_Y), (x, GROUND_Y + 20), 2)
        label = font_small.render(f"{m}米", True, (60, 60, 60))
        screen.blit(label, (x - 12, GROUND_Y + 25))

    x12 = SLING_X + 12 * SCALE
    pygame.draw.line(screen, (255, 0, 0), (x12, GROUND_Y - 100), (x12, GROUND_Y + 20), 3)
    label = font.render("12米 目标", True, (255, 0, 0))
    screen.blit(label, (x12 - 40, GROUND_Y - 130))

def draw_target():
    rect = pygame.Rect(TARGET_X - 20, TARGET_Y - 15, 40, 30)
    pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=5)
    pygame.draw.circle(screen, (255, 0, 0), (TARGET_X, TARGET_Y), 5)

def draw_ui():
    title = font.render("AI投掷模拟：虚拟环境推演（12米无人机目标）", True, (0, 0, 100))
    screen.blit(title, (20, 15))

    for i, obj in enumerate(OBJECTS):
        x = 20 + i * 150
        y = 55
        rect = pygame.Rect(x, y, 140, 45)
        if i == current_idx:
            pygame.draw.rect(screen, obj["color"], rect, border_radius=10)
            pygame.draw.rect(screen, (255, 0, 0), rect, 3, border_radius=10)
        else:
            pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 2, border_radius=10)

        name_text = font.render(obj["name"], True, (0, 0, 0))
        screen.blit(name_text, (x + 40, y + 10))
        info_text = font_small.render(f"{obj['mass']}kg 最大{obj['max_v']}m/s", True, (80, 80, 80))
        screen.blit(info_text, (x + 10, y + 50))

    hint = font_small.render("向后下方拖拽弹弓发射 | 1/2/3/4切换 | R重置", True, (100, 100, 100))
    screen.blit(hint, (20, HEIGHT - 25))

def draw_sling_and_preview():
    pygame.draw.line(screen, (139, 69, 19), (SLING_X - 20, GROUND_Y), (SLING_X, SLING_Y), 8)
    pygame.draw.line(screen, (139, 69, 19), (SLING_X + 20, GROUND_Y), (SLING_X, SLING_Y), 8)

    if dragging and drag_current:
        pygame.draw.line(screen, (180, 0, 0), (SLING_X - 15, SLING_Y), drag_current, 5)
        pygame.draw.line(screen, (180, 0, 0), (SLING_X + 15, SLING_Y), drag_current, 5)

        drag_dx = SLING_X - drag_current[0]
        drag_dy = SLING_Y - drag_current[1]
        power = 0.15
        vx = drag_dx * power
        vy = -drag_dy * power

        max_v = OBJECTS[current_idx]["max_v"]
        v_total = math.sqrt(vx**2 + vy**2)
        if v_total > max_v:
            s = max_v / v_total
            vx *= s
            vy *= s

        obj = OBJECTS[current_idx]
        m = obj["mass"]
        d = obj["d"]
        Cd = obj["Cd"]
        A = math.pi * (d / 2) ** 2

        px, py = float(SLING_X), float(SLING_Y)
        pvx = vx * SCALE
        pvy = -vy * SCALE

        dt = 0.005
        for i in range(100):
            v = math.sqrt(pvx**2 + pvy**2)
            v_mps = v / SCALE

            if v_mps > 0.1:
                F = 0.5 * RHO * v_mps**2 * Cd * A
                a = F / m * SCALE
                ax = -a * (pvx / v)
                ay = -a * (pvy / v)
            else:
                ax, ay = 0, 0

            ay += G * SCALE

            pvx += ax * dt
            pvy += ay * dt
            px += pvx * dt
            py += pvy * dt

            if py >= GROUND_Y:
                break

            if i % 3 == 0:
                brightness = 180 - i * 1.5
                if brightness < 60:
                    brightness = 60
                pygame.draw.circle(screen, (brightness, brightness, brightness), (int(px), int(py)), 3)

        pygame.draw.circle(screen, obj["color"], drag_current, obj["r"])
        pygame.draw.circle(screen, (0, 0, 0), drag_current, obj["r"], 2)

class Projectile:
    def __init__(self, vx_mps, vy_mps, idx):
        self.x = float(SLING_X)
        self.y = float(SLING_Y)
        self.vx = vx_mps * SCALE
        self.vy = -vy_mps * SCALE
        self.obj = OBJECTS[idx]
        self.trail = []
        self.landed = False
        self.hit = False
        self.obj_idx = idx
        self.A = math.pi * (self.obj["d"] / 2) ** 2
        self.mass = self.obj["mass"]
        self.Cd = self.obj["Cd"]

    def update(self, dt):
        if self.landed:
            return

        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 300:
            self.trail.pop(0)

        sub_steps = 10
        sub_dt = dt / sub_steps

        for _ in range(sub_steps):
            v = math.sqrt(self.vx**2 + self.vy**2)
            v_mps = v / SCALE

            if v_mps > 0.1:
                F = 0.5 * RHO * v_mps**2 * self.Cd * self.A
                a = F / self.mass * SCALE
                ax = -a * (self.vx / v)
                ay = -a * (self.vy / v)
            else:
                ax, ay = 0, 0

            ay += G * SCALE

            self.vx += ax * sub_dt
            self.vy += ay * sub_dt
            self.x += self.vx * sub_dt
            self.y += self.vy * sub_dt

            if self.y >= GROUND_Y - self.obj["r"]:
                self.y = GROUND_Y - self.obj["r"]
                self.landed = True
                dist = abs(self.x - TARGET_X) / SCALE
                self.hit = dist < 0.5
                update_stats(self.obj_idx, self.hit, dist)
                return

    def draw(self):
        if len(self.trail) > 1:
            color = (255, 100, 100) if self.hit else (100, 149, 237)
            pygame.draw.lines(screen, color, False, self.trail, 2)

        pygame.draw.circle(screen, self.obj["color"], (int(self.x), int(self.y)), self.obj["r"])
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.obj["r"], 2)

        if self.landed:
            dist = abs(self.x - TARGET_X) / SCALE
            if self.hit:
                text = font_big.render("命中！", True, (255, 0, 0))
                screen.blit(text, (int(self.x) - 30, int(self.y) - 50))
            else:
                text = font.render(f"偏差{dist:.1f}米", True, (100, 100, 100))
                screen.blit(text, (int(self.x) - 40, int(self.y) - 35))

running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                projectiles = []
                stats = {"total": [0]*4, "hits": [0]*4, "distances": [[],[],[],[]]}
            elif event.key == pygame.K_1:
                current_idx = 0
            elif event.key == pygame.K_2:
                current_idx = 1
            elif event.key == pygame.K_3:
                current_idx = 2
            elif event.key == pygame.K_4:
                current_idx = 3

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                clicked_btn = False
                for i in range(4):
                    bx, by = 20 + i * 150, 55
                    if bx <= mx <= bx + 140 and by <= my <= by + 45:
                        current_idx = i
                        clicked_btn = True
                        break
                if not clicked_btn:
                    if math.hypot(mx - SLING_X, my - SLING_Y) < 100:
                        dragging = True
                        drag_current = (mx, my)

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                drag_current = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                dragging = False

                drag_dx = SLING_X - drag_current[0]
                drag_dy = SLING_Y - drag_current[1]
                power = 0.15
                vx = drag_dx * power
                vy = -drag_dy * power

                max_v = OBJECTS[current_idx]["max_v"]
                v_total = math.sqrt(vx**2 + vy**2)
                if v_total > max_v:
                    s = max_v / v_total
                    vx *= s
                    vy *= s

                projectiles.append(Projectile(vx, vy, current_idx))

    for p in projectiles:
        p.update(dt)

    draw_background()
    draw_target()
    draw_sling_and_preview()
    draw_ui()
    draw_data_panel()

    for p in projectiles:
        p.draw()

    pygame.display.flip()

pygame.quit()
sys.exit()