"""2050: Letters from the Future — TENSOR TITANS
Premium-styled 2D Pygame edition. No Ursina and no external image assets.

Run from your activated VS Code terminal:
    python -m pip install pygame
    python 2050_Letters_From_The_Future_2D.py

Controls: mouse to select; type your name on the name screen; Enter continues;
Backspace edits your name; Esc returns to the title screen; close the window to quit.
"""
import math
import random
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 1280, 720
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2050 | Letters from the Future — TENSOR TITANS")
CLOCK = pygame.time.Clock()

# Premium night-teal / jade / warm-champagne palette
BG_TOP = (9, 23, 39)
BG_BOTTOM = (24, 64, 70)
INK = (8, 23, 34)
INK_SOFT = (15, 38, 48)
PANEL = (12, 31, 43)
PANEL_EDGE = (60, 111, 112)
CREAM = (241, 238, 220)
MUTED = (176, 199, 194)
MINT = (147, 229, 191)
JADE = (45, 151, 119)
JADE_BRIGHT = (75, 194, 151)
GOLD = (244, 197, 112)
CORAL = (235, 119, 102)
RIVER_DIRTY = (25, 91, 118)
RIVER_CLEAN = (25, 143, 177)
WHITE = (250, 250, 242)

# Font fallbacks make the game work on ordinary Windows installations.
def get_font(size, bold=False):
    for name in ("Aptos", "Segoe UI", "Arial", "Verdana"):
        font = pygame.font.SysFont(name, size, bold=bold)
        if font:
            return font
    return pygame.font.Font(None, size)

FONT_TINY = get_font(14)
FONT_SMALL = get_font(17)
FONT_BODY = get_font(20)
FONT_MED = get_font(25, True)
FONT_HEAD = get_font(34, True)
FONT_HERO = get_font(78, True)
FONT_KICKER = get_font(13, True)

STATE = {
    "screen": "intro", "name": "", "letter": 0,
    "collected": 0, "total": 0, "score": 0, "decisions": 0,
    "targets": [], "notice": "", "notice_until": 0,
}

LETTERS = [
    ("01 / THE VANISHING RIVER",
     "I am writing from 2050. The river beside my home is almost unrecognisable. "
     "Plastic bags snag near the drain, cans and bottles drift past, and newspaper "
     "scraps cling to the banks.\n\nI have only seen pictures of the clear river my "
     "grandparents remember. Please help us change what happens next."),
    ("02 / A CITY WITHOUT SHADE",
     "Our streets are hotter now, and trees that once shaded our neighbourhood are "
     "missing. The river is full of litter, and blocked drains carry rubbish further "
     "into the city.\n\nSmall choices made today can give tomorrow more shade, cleaner "
     "water and hope."),
    ("03 / THE LAST CLEAN DROP",
     "Clean water should never be a luxury. Rubbish is caught in our drains, and "
     "pollution has damaged the river we depend on. The future is not written yet.\n\n"
     "Will you help us give the river a second chance?"),
]

# Deterministic background props: scenery does not flicker between frames.
_bg_rng = random.Random(2050)
STARS = [( _bg_rng.randint(15, WIDTH-15), _bg_rng.randint(16, 230), _bg_rng.randint(1, 3),
           _bg_rng.random()*math.tau) for _ in range(70)]
CITY = []
for i in range(13):
    x = i * 108 - 12
    w = _bg_rng.randint(60, 91)
    h = _bg_rng.randint(65, 145)
    CITY.append((x, 270-h, w, h, _bg_rng.randint(0, 2)))
BG_LITTER = []
for i in range(24):
    x = _bg_rng.randint(25, WIDTH-25)
    y = int(310 + .13*x + 34*math.sin((x+40)/180) + _bg_rng.randint(-48, 48))
    BG_LITTER.append((x, y, i % 4, _bg_rng.randint(-18, 18)))
PARTICLES = [{"x": _bg_rng.uniform(0, WIDTH), "y": _bg_rng.uniform(0, HEIGHT),
              "r": _bg_rng.choice((1, 1, 2)), "speed": _bg_rng.uniform(3, 10),
              "phase": _bg_rng.uniform(0, 10)} for _ in range(36)]


def clamp(value, low, high):
    return max(low, min(high, value))


def blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_gradient():
    for y in range(HEIGHT):
        t = y / HEIGHT
        pygame.draw.line(SCREEN, blend(BG_TOP, BG_BOTTOM, t), (0, y), (WIDTH, y))


def draw_text(text, font, colour, pos, align="center"):
    surface = font.render(str(text), True, colour)
    rect = surface.get_rect()
    if align == "center":
        rect.center = (int(pos[0]), int(pos[1]))
    elif align == "left":
        rect.midleft = (int(pos[0]), int(pos[1]))
    elif align == "right":
        rect.midright = (int(pos[0]), int(pos[1]))
    SCREEN.blit(surface, rect)
    return rect


def wrap_text(text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            candidate = word if not line else line + " " + word
            if font.size(candidate)[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def draw_wrapped(text, font, colour, x, y, max_width, line_gap=7, align="left"):
    for line in wrap_text(text, font, max_width):
        if line:
            if align == "center":
                draw_text(line, font, colour, (x, y), "center")
            else:
                draw_text(line, font, colour, (x, y), "left")
            y += font.get_linesize() + line_gap
        else:
            y += font.get_linesize() // 2
    return y


def rounded_panel(rect, fill=(10, 28, 40, 238), border=PANEL_EDGE, radius=22, shadow=True):
    r = pygame.Rect(rect)
    if shadow:
        shadow_surface = pygame.Surface((r.w+24, r.h+24), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 85), (12, 12, r.w, r.h), border_radius=radius)
        SCREEN.blit(shadow_surface, (r.x-12, r.y-5))
    panel_surface = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, fill, (0, 0, r.w, r.h), border_radius=radius)
    SCREEN.blit(panel_surface, r.topleft)
    pygame.draw.rect(SCREEN, border, r, 1, border_radius=radius)
    # Small top-edge glint gives the glass-card look without overwhelming the text.
    pygame.draw.line(SCREEN, (105, 159, 151), (r.x+radius, r.y+1), (r.right-radius, r.y+1), 1)


def draw_button(label, rect, mouse, clicked=False, primary=True, font=FONT_BODY):
    r = pygame.Rect(rect)
    hover = r.collidepoint(mouse)
    pygame.draw.rect(SCREEN, (0, 0, 0, 80), r.move(0, 5), border_radius=12)
    if primary:
        base = JADE_BRIGHT if hover else JADE
        edge = (126, 225, 178)
        text_colour = (5, 35, 39)
    else:
        base = (26, 57, 67) if hover else (18, 43, 54)
        edge = (75, 123, 123) if hover else (53, 91, 98)
        text_colour = CREAM
    pygame.draw.rect(SCREEN, base, r, border_radius=12)
    pygame.draw.rect(SCREEN, edge, r, 1, border_radius=12)
    if primary:
        pygame.draw.line(SCREEN, blend(base, WHITE, .18), (r.x+14, r.y+2), (r.right-14, r.y+2), 1)
    draw_text(label, font, text_colour, r.center)
    return clicked and hover


def draw_pill(label, x, y, width, active=True):
    rect = pygame.Rect(x, y, width, 28)
    fill = (24, 91, 74) if active else (22, 48, 57)
    edge = (81, 173, 133) if active else (54, 88, 95)
    pygame.draw.rect(SCREEN, fill, rect, border_radius=14)
    pygame.draw.rect(SCREEN, edge, rect, 1, border_radius=14)
    draw_text(label, FONT_KICKER, MINT if active else MUTED, rect.center)


def river_y(x):
    return int(310 + .13*x + 34*math.sin((x+40)/180))


def river_polygon(half_width=83):
    upper, lower = [], []
    for x in range(-100, WIDTH+130, 12):
        y = river_y(x)
        dy = .13 + (34/180)*math.cos((x+40)/180)
        norm = math.sqrt(1 + dy*dy)
        off_x = half_width * dy / norm
        off_y = half_width / norm
        upper.append((int(x + off_x), int(y - off_y)))
        lower.append((int(x - off_x), int(y + off_y)))
    return upper + list(reversed(lower))


def draw_tree(x, base_y, scale=1.0, autumn=False):
    # layered crown with a subtle offset shadow
    trunk_w = max(5, int(9*scale))
    trunk_h = int(35*scale)
    pygame.draw.ellipse(SCREEN, (16, 48, 45), (x-int(25*scale), base_y-int(5*scale), int(50*scale), int(13*scale)))
    pygame.draw.rect(SCREEN, (105, 75, 49), (x-trunk_w//2, base_y-trunk_h, trunk_w, trunk_h), border_radius=3)
    greens = [(45, 121, 76), (56, 145, 83), (76, 166, 94)] if not autumn else [(119, 112, 53),(160,126,54),(183,148,66)]
    for dx, dy, rad, col in [(-13,-40,18,greens[0]),(7,-48,21,greens[1]),(-1,-61,17,greens[2]),(17,-37,15,greens[1])]:
        pygame.draw.circle(SCREEN, (23, 73, 59), (x+int((dx+3)*scale), base_y+int((dy+3)*scale)), int(rad*scale))
        pygame.draw.circle(SCREEN, col, (x+int(dx*scale), base_y+int(dy*scale)), int(rad*scale))


def draw_bridge():
    cx = 700
    deck_y = river_y(cx) - 2
    # bridge shadow and stone spans
    pygame.draw.line(SCREEN, (14, 42, 48), (500, deck_y+8), (900, deck_y+8), 27)
    pygame.draw.line(SCREEN, (118, 129, 119), (500, deck_y), (900, deck_y), 20)
    pygame.draw.line(SCREEN, (190, 190, 165), (500, deck_y-10), (900, deck_y-10), 5)
    pygame.draw.line(SCREEN, (68, 91, 88), (500, deck_y+10), (900, deck_y+10), 3)
    for x in (535, 590, 645, 700, 755, 810, 865):
        pygame.draw.line(SCREEN, (89, 107, 101), (x, deck_y-3), (x, deck_y-18), 3)
    # stone piers blend into the waterbanks
    for x in (575, 690, 805):
        pygame.draw.polygon(SCREEN, (104, 116, 105), [(x-9,deck_y+7),(x+9,deck_y+7),(x+14,deck_y+55),(x-14,deck_y+55)])
        pygame.draw.line(SCREEN, (156, 158, 138), (x-4,deck_y+12), (x-8,deck_y+48), 2)
    # parapet blocks
    for x in range(510, 895, 28):
        pygame.draw.rect(SCREEN, (148, 153, 133), (x, deck_y-22, 20, 8), border_radius=2)


def draw_litter_shape(kind, x, y, scale=1.0, highlighted=False):
    if highlighted:
        pygame.draw.circle(SCREEN, (250, 213, 133), (int(x), int(y)), int(19*scale), 2)
        pygame.draw.circle(SCREEN, (250, 213, 133), (int(x), int(y)), int(23*scale), 1)
    if kind in ("plastic bag", "drain rubbish"):
        col = (20, 29, 29) if not highlighted else (239, 188, 85)
        pts = [(x-13*scale,y-5*scale),(x+7*scale,y-10*scale),(x+14*scale,y+4*scale),(x-6*scale,y+9*scale)]
        pygame.draw.polygon(SCREEN, col, [(int(a),int(b)) for a,b in pts])
        pygame.draw.line(SCREEN, (88, 99, 87), (int(x-5*scale),int(y-3*scale)),(int(x+5*scale),int(y+2*scale)), max(1,int(1.5*scale)))
    elif kind == "newspaper":
        col = (226, 216, 188) if not highlighted else (239, 188, 85)
        pts = [(x-13*scale,y-8*scale),(x+11*scale,y-9*scale),(x+14*scale,y+7*scale),(x-11*scale,y+8*scale)]
        pygame.draw.polygon(SCREEN, col, [(int(a),int(b)) for a,b in pts])
        for delta in (-3, 1, 4):
            pygame.draw.line(SCREEN, (103, 104, 93), (int(x-7*scale),int(y+delta*scale)),(int(x+8*scale),int(y+delta*scale)),1)
    elif kind == "tin can":
        col = (188, 83, 71) if not highlighted else (239, 188, 85)
        rect = pygame.Rect(int(x-7*scale),int(y-11*scale),max(5,int(14*scale)),max(8,int(22*scale)))
        pygame.draw.rect(SCREEN, col, rect, border_radius=3)
        pygame.draw.line(SCREEN, (241, 205, 170), (rect.x+2,rect.y+4),(rect.right-2,rect.y+4),1)
        pygame.draw.line(SCREEN, (241, 205, 170), (rect.x+2,rect.bottom-4),(rect.right-2,rect.bottom-4),1)
    else:
        col = (44, 133, 93) if not highlighted else (239, 188, 85)
        rect = pygame.Rect(int(x-6*scale),int(y-9*scale),max(7,int(12*scale)),max(10,int(19*scale)))
        pygame.draw.rect(SCREEN, col, rect, border_radius=4)
        pygame.draw.rect(SCREEN, (184, 214, 187), (int(x-3*scale),int(y-13*scale),max(4,int(6*scale)),max(4,int(5*scale))), border_radius=1)
        pygame.draw.line(SCREEN, (145, 205, 164), (int(x-2*scale),int(y-3*scale)), (int(x+2*scale),int(y+5*scale)), 2)


def draw_world(clean=False, drain=False, ambient=True):
    draw_gradient()
    # Stars and a low, soft horizon glow
    for sx, sy, radius, phase in STARS:
        twinkle = .65 + .35*math.sin(pygame.time.get_ticks()/1100 + phase) if ambient else .75
        c = int(78 + 75*twinkle)
        pygame.draw.circle(SCREEN, (c, min(220,c+28), min(225,c+35)), (sx, sy), radius)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (70, 176, 154, 28), (90, 165, 1100, 250))
    SCREEN.blit(glow, (0,0))

    # distant hills and a layered city silhouette
    pygame.draw.polygon(SCREEN, (25, 75, 76), [(0,270),(120,228),(260,259),(390,208),(540,257),(705,216),(860,258),(1045,213),(1280,249),(1280,520),(0,520)])
    pygame.draw.polygon(SCREEN, (24, 58, 66), [(0,290),(165,259),(305,286),(490,239),(645,281),(825,251),(1000,286),(1150,251),(1280,275),(1280,550),(0,550)])
    for x, y, w, h, variant in CITY:
        building_col = (20+variant*3, 46+variant*5, 57+variant*4)
        pygame.draw.rect(SCREEN, building_col, (x,y,w,h))
        pygame.draw.line(SCREEN, (57, 94, 94), (x,y), (x+w,y), 2)
        for wx in range(x+11, x+w-5, 17):
            for wy in range(y+13, y+h-8, 20):
                if ((wx*3 + wy*7) % 5) in (0,2):
                    pygame.draw.rect(SCREEN, (198, 176, 112), (wx,wy,4,6))

    # banks beneath the winding river
    pygame.draw.rect(SCREEN, (26, 75, 63), (0, 320, WIDTH, HEIGHT-320))
    pygame.draw.polygon(SCREEN, (41, 105, 74), [(0,275),(160,294),(320,328),(490,360),(650,380),(850,419),(1050,453),(1280,474),(1280,720),(0,720)])
    pygame.draw.polygon(SCREEN, (22, 83, 65), [(0,550),(180,544),(380,520),(580,504),(770,498),(980,479),(1140,458),(1280,430),(1280,720),(0,720)])
    # bank-edge grasses are repeatable, hand-placed strokes
    for i in range(95):
        x = (i*47+13) % WIDTH
        y = river_y(x) + (92 if i%2 else -91)
        col = (73, 143, 84) if i%3 else (103, 159, 90)
        pygame.draw.line(SCREEN, col, (x,y), (x+(i%5)-2,y-5-(i%4)), 2)

    # winding water with layered current lines
    poly = river_polygon(84)
    pygame.draw.polygon(SCREEN, (15, 48, 59), poly)
    water = RIVER_CLEAN if clean else RIVER_DIRTY
    pygame.draw.lines(SCREEN, water, False, [(x,river_y(x)) for x in range(-30,WIDTH+40,12)], 152)
    pygame.draw.lines(SCREEN, (87, 193, 207) if clean else (57, 130, 150), False,
                      [(x,river_y(x)-48) for x in range(-30,WIDTH+40,20)], 3)
    pygame.draw.lines(SCREEN, (11, 71, 86) if clean else (18, 70, 87), False,
                      [(x,river_y(x)+49) for x in range(-30,WIDTH+40,20)], 5)
    # calm water glints
    for i in range(28):
        x = (i*53 + 21) % WIDTH
        y = river_y(x) + ((i%5)-2)*18
        glint_col = (127, 221, 221) if clean else (65, 150, 170)
        pygame.draw.line(SCREEN, glint_col, (x,y), (x+12+(i%4)*4,y-1), 2 if i%3 else 3)

    if not clean:
        for x,y,kind,tilt in BG_LITTER:
            draw_litter_shape(("plastic bag","newspaper","tin can","plastic bottle")[kind],x,y,.72)
        # a few dark pollution patches add contrast, without hiding the river
        for i in range(11):
            x = 45 + i*113
            y = river_y(x) + (i%3-1)*39
            pygame.draw.ellipse(SCREEN, (27, 66, 68), (x,y,32,11))

    # A deliberate alternating row of trees hugs both banks of the river.
    # Their trunks sit just outside the water edge, so the scene reads clearly.
    tree_data = []
    for tx, scale in ((48,.86),(250,.78),(430,.68),(990,.72),(1200,.88)):
        tree_data.append((tx, river_y(tx)-91, scale))
    for tx, scale in ((155,.78),(350,.72),(835,.72),(1080,.82),(1235,.70)):
        tree_data.append((tx, river_y(tx)+97, scale))
    for tx, base, scale in tree_data:
        draw_tree(tx, base, scale, autumn=(tx % 3 == 0))

    draw_bridge()
    if drain:
        dx, dy = 1050, river_y(1050)+31
        pygame.draw.ellipse(SCREEN, (9, 34, 40), (dx-86,dy-41,174,86))
        pygame.draw.ellipse(SCREEN, (101, 118, 110), (dx-80,dy-37,162,78), 9)
        pygame.draw.ellipse(SCREEN, (8, 27, 33), (dx-66,dy-26,134,56))
        for x in range(dx-54, dx+55, 18):
            pygame.draw.line(SCREEN, (132, 151, 139), (x,dy-22),(x,dy+23),4)
        pygame.draw.line(SCREEN, (132, 151, 139), (dx-61,dy),(dx+61,dy),4)

    # Floating dust in the air gives subtle movement, not a distracting animation.
    if ambient:
        now = pygame.time.get_ticks()/1000
        for p in PARTICLES:
            x = int((p["x"] + now*p["speed"]) % WIDTH)
            y = int(p["y"] + math.sin(now*.7+p["phase"])*5)
            pygame.draw.circle(SCREEN, (102, 177, 156), (x,y), p["r"])


def draw_header(kicker, title, subtitle=""):
    pygame.draw.rect(SCREEN, (7, 25, 36), (24, 18, WIDTH-48, 88), border_radius=17)
    pygame.draw.rect(SCREEN, (61, 112, 111), (24, 18, WIDTH-48, 88), 1, border_radius=17)
    draw_text(kicker.upper(), FONT_KICKER, GOLD, (48, 38), "left")
    draw_text(title, FONT_MED, CREAM, (48, 65), "left")
    if subtitle:
        draw_text(subtitle, FONT_SMALL, MUTED, (WIDTH-48, 65), "right")


def draw_intro(mouse, click):
    draw_world(False, ambient=True)
    # cinematic left-side veil, keeping the river illustration visible on the right
    veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x in range(0, 870, 2):
        alpha = int(226 * (1 - x/980))
        pygame.draw.line(veil, (5, 20, 31, max(0,alpha)), (x,0),(x,HEIGHT))
    SCREEN.blit(veil,(0,0))
    draw_text("TENSOR TITANS  /  SDG 13", FONT_KICKER, GOLD, (75, 92), "left")
    pygame.draw.line(SCREEN, GOLD, (75,116),(142,116),2)
    draw_text("2050", FONT_HERO, CREAM, (70, 210), "left")
    draw_text("LETTERS FROM", FONT_HEAD, MINT, (75, 282), "left")
    draw_text("THE FUTURE", FONT_HEAD, MINT, (75, 324), "left")
    draw_wrapped("A river. A message. One chance to change tomorrow.", FONT_BODY, MUTED, 78, 385, 420, 8)
    draw_pill("CLIMATE ACTION", 75, 458, 150, True)
    draw_pill("INTERACTIVE STORY", 235, 458, 168, False)
    draw_button("BEGIN YOUR STORY   →", (75, 520, 310, 58), mouse, click, True, FONT_BODY)
    draw_text("SMALL CHOICES. BIGGER TOMORROWS.", FONT_KICKER, (155, 196, 183), (77, 627), "left")
    draw_text("A TENSOR TITANS ORIGINAL", FONT_TINY, (151, 179, 174), (WIDTH-35, HEIGHT-27), "right")
    return pygame.Rect(75,520,310,58).collidepoint(mouse) and click


def draw_name(mouse, click):
    draw_world(False, ambient=True)
    # centered, clean form card
    rounded_panel((270, 135, 740, 450), (9, 27, 40, 245), (76, 131, 126), 24)
    draw_pill("PERSONALISE YOUR STORY", 524, 169, 232, True)
    draw_text("What should Jennifer call you?", FONT_HEAD, CREAM, (640, 239))
    draw_text("Your name will appear in the letters from 2050.", FONT_SMALL, MUTED, (640, 281))
    name_box = pygame.Rect(390, 326, 500, 66)
    pygame.draw.rect(SCREEN, (17, 43, 53), name_box, border_radius=12)
    pygame.draw.rect(SCREEN, (83, 157, 136), name_box, 2, border_radius=12)
    shown = STATE["name"] if STATE["name"] else "Type your name..."
    draw_text(shown, FONT_BODY if STATE["name"] else FONT_SMALL,
              CREAM if STATE["name"] else (121, 155, 153), name_box.center)
    draw_text("Up to 18 characters  ·  Backspace to edit", FONT_TINY, MUTED, (640, 422))
    draw_button("CONTINUE   →", (490, 465, 300, 55), mouse, click, True, FONT_BODY)
    draw_text("ESC  /  MAIN MENU", FONT_KICKER, (149, 178, 173), (640, 548))
    return pygame.Rect(490,465,300,55).collidepoint(mouse) and click


def draw_letter(mouse, click):
    draw_world(False, ambient=True)
    rounded_panel((170, 72, 940, 570), (8, 26, 39, 246), (72, 133, 126), 24)
    # letter's small dossier marker
    pygame.draw.rect(SCREEN, GOLD, (205, 112, 4, 58), border_radius=2)
    draw_text("INCOMING MESSAGE  /  2050", FONT_KICKER, GOLD, (226, 117), "left")
    title, body = LETTERS[STATE["letter"]]
    draw_text(title, FONT_HEAD, CREAM, (220, 164), "left")
    pygame.draw.line(SCREEN, (63, 105, 105), (220, 204), (1060, 204), 1)
    message = "Dear " + (STATE["name"] or "Friend") + ",\n\n" + body + "\n\n— Jennifer, 2050"
    draw_wrapped(message, FONT_BODY, (218, 229, 218), 220, 233, 820, 6)
    draw_text("THREE MISSIONS. ONE CHANCE TO CHANGE THE FUTURE.", FONT_KICKER, MINT, (640, 548))
    draw_button("BEGIN THE RIVER RESCUE   →", (425, 575, 430, 49), mouse, click, True, FONT_SMALL)
    return pygame.Rect(425,575,430,49).collidepoint(mouse) and click


def make_targets():
    rng = random.Random()
    targets = []
    kinds = ["plastic bag", "newspaper", "tin can", "plastic bottle"]
    # Scatter over the actual water ribbon and keep target centres away from HUD/footer.
    for i in range(34):
        x = rng.randint(45, WIDTH-45)
        y = river_y(x) + rng.randint(-55, 55)
        y = clamp(y, 280, 555)
        size = rng.randint(30, 38)
        targets.append({"kind": rng.choice(kinds), "rect": pygame.Rect(0,0,size,size), "active": True})
        targets[-1]["rect"].center = (x,y)
    for i in range(6):
        x = rng.randint(990, 1110)
        y = river_y(x) + rng.randint(-26, 35)
        targets.append({"kind": "drain rubbish", "rect": pygame.Rect(0,0,38,36), "active": True})
        targets[-1]["rect"].center = (x,y)
    return targets


def start_cleanup():
    STATE.update(screen="cleanup", collected=0, total=0, score=0, decisions=0,
                 targets=[], notice="", notice_until=0)
    STATE["targets"] = make_targets()
    STATE["total"] = len(STATE["targets"])


def draw_mission_header(mouse):
    pygame.draw.rect(SCREEN, (7, 25, 36), (24, 17, WIDTH-48, 88), border_radius=17)
    pygame.draw.rect(SCREEN, (61, 112, 111), (24,17,WIDTH-48,88),1,border_radius=17)
    draw_text("MISSION 01 / 03", FONT_KICKER, GOLD, (48, 36), "left")
    draw_text("Rescue the river", FONT_MED, CREAM, (48, 65), "left")
    draw_text(f"COLLECTED  {STATE['collected']:02d} / {STATE['total']:02d}", FONT_SMALL, MINT, (WIDTH-48, 43), "right")
    # progress bar
    bar = pygame.Rect(WIDTH-300, 62, 252, 8)
    pygame.draw.rect(SCREEN, (34, 64, 71), bar, border_radius=4)
    fraction = STATE["collected"] / max(1,STATE["total"])
    pygame.draw.rect(SCREEN, JADE_BRIGHT, (bar.x,bar.y,int(bar.w*fraction),bar.h), border_radius=4)
    draw_text("Click the highlighted rubbish to collect it", FONT_TINY, MUTED, (WIDTH//2, 124))


def draw_cleanup(mouse, click):
    draw_world(False, drain=True, ambient=True)
    # light translucent mid-screen wash improves target readability
    wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(wash, (5, 19, 29, 35), (0, 110, WIDTH, 515))
    SCREEN.blit(wash,(0,0))
    draw_mission_header(mouse)
    hovered = None
    for item in STATE["targets"]:
        if item["active"]:
            is_hover = item["rect"].collidepoint(mouse)
            draw_litter_shape(item["kind"], *item["rect"].center, 1.0, is_hover)
            if is_hover:
                hovered = item
    # bottom instruction dock
    pygame.draw.rect(SCREEN, (8, 27, 39), (24, 620, WIDTH-48, 77), border_radius=15)
    pygame.draw.rect(SCREEN, (56, 99, 101), (24, 620, WIDTH-48, 77), 1, border_radius=15)
    draw_text("BAGS", FONT_KICKER, MUTED, (65, 643))
    draw_litter_shape("plastic bag", 65, 671, .72)
    draw_text("PAPER", FONT_KICKER, MUTED, (144, 643))
    draw_litter_shape("newspaper", 144, 671, .72)
    draw_text("CANS", FONT_KICKER, MUTED, (221, 643))
    draw_litter_shape("tin can", 221, 671, .72)
    draw_text("BOTTLES", FONT_KICKER, MUTED, (303, 643))
    draw_litter_shape("plastic bottle", 303, 671, .72)
    draw_button("FINISH MISSION   →", (900, 635, 320, 47), mouse, click, True, FONT_SMALL)
    return hovered, pygame.Rect(900,635,320,47).collidepoint(mouse) and click


def draw_choice_screen(mouse, click, mission):
    draw_world(clean=(mission==3), drain=(mission==2), ambient=True)
    rounded_panel((190, 124, 900, 475), (8, 26, 39, 245), (72, 133, 126), 24)
    if mission == 2:
        kicker = "MISSION 02 / 03"
        title = "Unblock the drain"
        prompt = "Plastic is trapped at the drain mouth. What is the safest response?"
        choices = [("Use proper tools and protective gloves", True),
                   ("Push the rubbish deeper inside", False),
                   ("Pour chemicals into the river", False)]
    else:
        kicker = "MISSION 03 / 03"
        title = "Protect tomorrow"
        prompt = "How can the community stop rubbish from returning?"
        choices = [("Sort waste, reduce plastic and spread awareness", True),
                   ("Leave litter for someone else to collect", False),
                   ("Burn plastic beside the river", False)]
    draw_pill(kicker, 520, 154, 240, True)
    draw_text(title, FONT_HEAD, CREAM, (640, 222))
    draw_text(prompt, FONT_BODY, MUTED, (640, 267))
    choice_rects = [(300, 325, 680, 58), (340, 399, 600, 54), (340, 468, 600, 54)]
    for idx, ((label, good), rect) in enumerate(zip(choices, choice_rects)):
        chosen = draw_button(label, rect, mouse, click, idx == 0, FONT_SMALL)
        if chosen:
            return good
    draw_text("CHOOSE RESPONSIBLY  ·  YOUR DECISIONS SHAPE THE ENDING", FONT_KICKER, GOLD, (640, 555))
    return None


def final_score():
    collection = round(STATE["collected"] / max(1,STATE["total"]) * 60)
    score = min(100, collection + STATE["decisions"]*20)
    return 100 if STATE["collected"] == STATE["total"] and STATE["decisions"] == 2 else score


def draw_ending(mouse, click):
    draw_world(True, ambient=True)
    rounded_panel((170, 54, 940, 610), (8, 26, 39, 245), (72, 133, 126), 24)
    draw_pill("FUTURE TIMELINE UPDATED", 516, 79, 248, True)
    draw_text("The future is still ours.", FONT_HEAD, CREAM, (640, 133))
    score = final_score()
    draw_text(f"{score:02d}", FONT_HERO, MINT, (640, 225))
    draw_text("IMPACT SCORE  /  100", FONT_KICKER, GOLD, (640, 274))
    # progress rail
    rail = pygame.Rect(390, 296, 500, 8)
    pygame.draw.rect(SCREEN, (33, 65, 72), rail, border_radius=5)
    pygame.draw.rect(SCREEN, JADE_BRIGHT, (rail.x,rail.y,int(rail.w*score/100),rail.h), border_radius=5)
    draw_text(f"River rubbish collected:  {STATE['collected']} / {STATE['total']}", FONT_SMALL, MUTED, (640, 333))
    draw_text(f"Responsible decisions:  {STATE['decisions']} / 2", FONT_SMALL, MUTED, (640, 360))
    thanks = (f"Dear {STATE['name'] or 'Friend'}, Jennifer can hardly believe the change. "
              "The river is shining blue again, and the community is choosing to care. "
              "Cleaner water begins with everyday decisions: sorting waste, using less plastic, "
              "and protecting the places we share. You have given the future a little more hope.\n\n"
              "Thank you for writing a better tomorrow with me.  — Jennifer, 2050")
    draw_wrapped(thanks, FONT_SMALL, (222, 233, 221), 640, 407, 770, 5, "center")
    draw_button("PLAY AGAIN", (340, 588, 250, 48), mouse, click, True, FONT_SMALL)
    draw_button("MAIN MENU", (690, 588, 250, 48), mouse, click, False, FONT_SMALL)
    return (pygame.Rect(340,588,250,48).collidepoint(mouse) and click,
            pygame.Rect(690,588,250,48).collidepoint(mouse) and click)


def go_to_intro():
    STATE.update(screen="intro", name="", letter=0, collected=0, total=0, score=0,
                 decisions=0, targets=[], notice="", notice_until=0)


def main():
    running = True
    while running:
        CLOCK.tick(FPS)
        mouse = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    go_to_intro()
                elif STATE["screen"] == "name":
                    if event.key == pygame.K_RETURN:
                        STATE["screen"] = "letter"
                        STATE["letter"] = random.randrange(len(LETTERS))
                    elif event.key == pygame.K_BACKSPACE:
                        STATE["name"] = STATE["name"][:-1]
                    else:
                        char = event.unicode
                        if char and char.isprintable() and (char.isalnum() or char in " -_'") and len(STATE["name"]) < 18:
                            STATE["name"] += char

        screen = STATE["screen"]
        if screen == "intro":
            if draw_intro(mouse, click):
                STATE["screen"] = "name"
        elif screen == "name":
            if draw_name(mouse, click):
                STATE["screen"] = "letter"
                STATE["letter"] = random.randrange(len(LETTERS))
        elif screen == "letter":
            if draw_letter(mouse, click):
                start_cleanup()
        elif screen == "cleanup":
            hovered, finish_clicked = draw_cleanup(mouse, click)
            if click and hovered is not None and hovered["active"]:
                hovered["active"] = False
                STATE["collected"] += 1
                STATE["score"] += 1
                if STATE["collected"] == STATE["total"]:
                    STATE["notice"] = "PERFECT CLEAN-UP  ·  EVERY PIECE COLLECTED"
                    STATE["notice_until"] = pygame.time.get_ticks() + 2200
            elif finish_clicked:
                STATE["screen"] = "drain"
        elif screen == "drain":
            answer = draw_choice_screen(mouse, click, 2)
            if answer is not None:
                if answer:
                    STATE["score"] += 20
                    STATE["decisions"] += 1
                STATE["screen"] = "community"
        elif screen == "community":
            answer = draw_choice_screen(mouse, click, 3)
            if answer is not None:
                if answer:
                    STATE["score"] += 20
                    STATE["decisions"] += 1
                STATE["screen"] = "ending"
        elif screen == "ending":
            play_again, main_menu = draw_ending(mouse, click)
            if play_again:
                start_cleanup()
            elif main_menu:
                go_to_intro()

        if STATE["notice"] and pygame.time.get_ticks() < STATE["notice_until"]:
            pygame.draw.rect(SCREEN, (7, 27, 38), (310, 564, 660, 38), border_radius=10)
            pygame.draw.rect(SCREEN, GOLD, (310,564,660,38), 1, border_radius=10)
            draw_text(STATE["notice"], FONT_TINY, GOLD, (640, 583))
        elif STATE["notice"] and pygame.time.get_ticks() >= STATE["notice_until"]:
            STATE["notice"] = ""

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
