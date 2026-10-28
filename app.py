import pygame
import sys

# Pygame 초기화
pygame.init()
pygame.font.init()

# 화면 설정
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("화학 원소 밀도 & 상태 시뮬레이터")
clock = pygame.time.Clock()

# 폰트 설정 (한글 폰트 적용 - 시스템 폰트 사용)
try:
    font = pygame.font.SysFont("malgungothic", 16)
    font_small = pygame.font.SysFont("malgungothic", 12)
    font_large = pygame.font.SysFont("malgungothic", 22, bold=True)
except:
    font = pygame.font.SysFont(None, 20)
    font_small = pygame.font.SysFont(None, 14)
    font_large = pygame.font.SysFont(None, 24)

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
BEAKER_COLOR = (180, 220, 255, 150)
SKY_BLUE = (173, 216, 230)

# 1~118번 원소 데이터 (기본 25℃ 상태 기준: S=고체, L=액체, G=기체)
# [기호, 이름, 원자량(g/mol), 25℃ 상태, RGB색상]
ELEMENTS_DATA = [
    (1, "H", "수소", 1.008, "G", (230, 240, 255)),
    (2, "He", "헬륨", 4.0026, "G", (255, 230, 240)),
    (3, "Li", "리튬", 6.94, "S", (200, 150, 150)),
    (4, "Be", "베릴륨", 9.0122, "S", (180, 200, 150)),
    (5, "B", "붕소", 10.81, "S", (150, 180, 150)),
    (6, "C", "탄소", 12.011, "S", (50, 50, 50)),
    (7, "N", "질소", 14.007, "G", (200, 220, 255)),
    (8, "O", "산소", 15.999, "G", (180, 200, 255)),
    (9, "F", "플루오린", 18.998, "G", (255, 255, 180)),
    (10, "Ne", "네온", 20.180, "G", (255, 200, 220)),
    (11, "Na", "나트륨", 22.990, "S", (170, 170, 210)),
    (12, "Mg", "마그네슘", 24.305, "S", (150, 220, 150)),
    (13, "Al", "알루미늄", 26.982, "S", (210, 210, 220)),
    (14, "Si", "규소", 28.085, "S", (140, 150, 160)),
    (15, "P", "인", 30.974, "S", (255, 160, 100)),
    (16, "S", "황", 32.06, "S", (240, 230, 80)),
    (17, "Cl", "염소", 35.45, "G", (200, 240, 160)),
    (18, "Ar", "아르곤", 39.948, "G", (190, 190, 230)),
    (19, "K", "칼륨", 39.098, "S", (160, 140, 200)),
    (20, "Ca", "칼슘", 40.078, "S", (230, 220, 190)),
    (35, "Br", "브로민", 79.904, "L", (165, 42, 42)), # 액체 예시
    (80, "Hg", "수은", 200.59, "L", (170, 170, 180)), # 액체 예시
]

# 나머지 원소 자동 생성 (데이터 단순화 처리)
known_atomic_nums = [e[0] for e in ELEMENTS_DATA]
for z in range(1, 119):
    if z not in known_atomic_nums:
        # 93번 이후는 인공원소(고체 추정), 대략적인 원자량 계산
        approx_mass = z * 2.5
        state = "S"
        color = (120 + (z*7)%100, 120 + (z*13)%100, 120 + (z*17)%100)
        ELEMENTS_DATA.append((z, f"E{z}", f"원소_{z}", approx_mass, state, color))

ELEMENTS_DATA.sort(key=lambda x: x[0])

# 비커 좌표 정의
BEAKER_X = 100
BEAKER_Y = 200
BEAKER_W = 350
BEAKER_H = 400

class ElementParticle:
    """비커 안이나 밖에서 움직이는 원소 물질 객체"""
    def __init__(self, data, qty):
        self.z, self.symbol, self.name, self.mass, self.state, self.color = data
        self.qty = qty
        self.x = BEAKER_X + BEAKER_W // 2
        self.y = BEAKER_Y + 50
        self.target_y = self.y
        self.size = max(8, min(40, qty * 4)) # 개수에 따른 크기
        self.speed = 3
        self.escaped = False # 기체 날아감 여부

    def update(self):
        if self.state == "G": # 기체는 상승
            self.y -= self.speed
            if self.y < -50:
                self.escaped = True
        else: # 액체/고체는 지정된 높이로 이동
            if self.y < self.target_y:
                self.y = min(self.target_y, self.y + self.speed)
            elif self.y > self.target_y:
                self.y = max(self.target_y, self.y - self.speed)

class BeakerSimulation:
    def __init__(self):
        self.contents = [] # 비커 내부 원소들
        self.selected_idx = 0
        self.qty = 1
        self.scroll_offset = 0

    def add_element(self):
        data = ELEMENTS_DATA[self.selected_idx]
        particle = ElementParticle(data, self.qty)
        self.contents.append(particle)
        self.recalculate_positions()

    def clear(self):
        self.contents.clear()

    def recalculate_positions(self):
        """무거울수록 아래로, 고체는 맨 아래로 정렬"""
        solids = [p for p in self.contents if p.state == "S"]
        liquids = [p for p in self.contents if p.state == "L"]
        
        # 원자량(질량) 기준으로 정렬 (무거운 것이 먼저/아래에)
        solids.sort(key=lambda p: p.mass, reverse=True)
        liquids.sort(key=lambda p: p.mass, reverse=True)

        current_bottom = BEAKER_Y + BEAKER_H - 10

        # 1. 고체 쌓기 (맨 바닥에 방형/결정 형태)
        for p in solids:
            p.target_y = current_bottom - p.size // 2
            current_bottom -= (p.size + 4)

        # 2. 액체 층 쌓기 (고체 위에 밀도 순서대로)
        for p in liquids:
            p.target_y = current_bottom - p.size // 2
            current_bottom -= (p.size + 2)

    def update(self):
        for p in self.contents:
            p.update()
        # 하늘로 날아간 기체 제거
        self.contents = [p for p in self.contents if not p.escaped]

    def draw(self, surface):
        # 1. 하늘 / 배경
        pygame.draw.rect(surface, SKY_BLUE, (0, 0, WIDTH, BEAKER_Y))
        
        # 2. 비커 그리기 (유리 겉면)
        beaker_rect = pygame.Rect(BEAKER_X, BEAKER_Y, BEAKER_W, BEAKER_H)
        pygame.draw.rect(surface, (230, 240, 255), beaker_rect) # 비커 내부 배경
        pygame.draw.rect(surface, (100, 150, 200), beaker_rect, 4) # 테두리

        # 3. 비커 눈금
        for i in range(1, 5):
            y = BEAKER_Y + BEAKER_H - (BEAKER_H // 5) * i
            pygame.draw.line(surface, (150, 150, 150), (BEAKER_X, y), (BEAKER_X + 30, y), 2)

        # 4. 원소 입자/층 그리기
        for p in self.contents:
            if p.state == "S": # 고체: 사각형 모양 (바닥에 침전)
                rect = pygame.Rect(BEAKER_X + 20, p.y - p.size//2, BEAKER_W - 40, p.size)
                pygame.draw.rect(surface, p.color, rect, border_radius=4)
                pygame.draw.rect(surface, DARK_GRAY, rect, 1, border_radius=4)
                txt = font_small.render(f"[고체] {p.name} ({p.mass}g)", True, BLACK)
                surface.blit(txt, (rect.x + 10, rect.y + 2))
                
            elif p.state == "L": # 액체: 둥근 층 형태
                rect = pygame.Rect(BEAKER_X + 5, p.y - p.size//2, BEAKER_W - 10, p.size)
                pygame.draw.ellipse(surface, p.color, rect)
                txt = font_small.render(f"[액체] {p.name} ({p.mass}g)", True, BLACK)
                surface.blit(txt, (rect.x + 10, rect.y + 2))

            elif p.state == "G": # 기체: 공기 방울 형태로 위로 날아감
                pygame.draw.circle(surface, p.color, (int(p.x), int(p.y)), p.size)
                pygame.draw.circle(surface, WHITE, (int(p.x), int(p.y)), p.size, 2)
                txt = font_small.render(f"[기체] {p.name} ↑", True, BLACK)
                surface.blit(txt, (p.x + p.size + 5, p.y - 5))

sim = BeakerSimulation()

# UI 조작용 변수
LIST_X = 520
LIST_Y = 80
LIST_W = 440
LIST_H = 500

running = True
while running:
    screen.fill((245, 245, 245))

    # --- 이벤트 처리 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: # 마우스 휠 위로 (리스트 스크롤)
                sim.scroll_offset = max(0, sim.scroll_offset - 1)
            elif event.button == 5: # 마우스 휠 아래로
                sim.scroll_offset = min(len(ELEMENTS_DATA) - 15, sim.scroll_offset + 1)
                
            elif event.button == 1:
                mx, my = event.pos
                # 원소 선택 클릭
                if LIST_X <= mx <= LIST_X + LIST_W and LIST_Y <= my <= LIST_Y + LIST_H:
                    clicked_idx = (my - LIST_Y) // 30 + sim.scroll_offset
                    if 0 <= clicked_idx < len(ELEMENTS_DATA):
                        sim.selected_idx = clicked_idx

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: # 스페이스바: 원소 투입
                sim.add_element()
            elif event.key == pygame.K_c: # C키: 비커 비우기
                sim.clear()
            elif event.key == pygame.K_UP: # 개수 증가
                sim.qty = min(10, sim.qty + 1)
            elif event.key == pygame.K_DOWN: # 개수 감소
                sim.qty = max(1, sim.qty - 1)

    # 시뮬레이션 업데이트
    sim.update()
    
    # 시뮬레이션/비커 그리기
    sim.draw(screen)

    # --- UI 및 안내 텍스트 ---
    # 헤더
    title = font_large.render("화학 원소 밀도 & 상태 시뮬레이터", True, BLACK)
    screen.blit(title, (20, 20))
    
    guide_txt = font.render("[Space]: 비커에 넣기 | [C]: 비커 비우기 | [↑/↓]: 개수(몰수) 조절", True, DARK_GRAY)
    screen.blit(guide_txt, (20, 55))

    # 현재 선택 정보
    sel_data = ELEMENTS_DATA[sim.selected_idx]
    state_map = {"S": "고체(Solid)", "L": "액체(Liquid)", "G": "기체(Gas)"}
    info_str = f"선택됨: {sel_data[0]}번 {sel_data[2]} ({sel_data[1]}) | 원자량: {sel_data[3]} | 상태: {state_map[sel_data[4]]} | 투입개수: {sim.qty}"
    info_txt = font.render(info_str, True, (0, 80, 160))
    screen.blit(info_txt, (BEAKER_X, BEAKER_Y - 30))

    # 원소 주기율표 리스트 패널
    pygame.draw.rect(screen, WHITE, (LIST_X, LIST_Y, LIST_W, LIST_H))
    pygame.draw.rect(screen, GRAY, (LIST_X, LIST_Y, LIST_W, LIST_H), 2)
    
    # 주기율표 원소 항목 출력 (스크롤 적용)
    visible_count = 16
    for i in range(visible_count):
        idx = i + sim.scroll_offset
        if idx >= len(ELEMENTS_DATA):
            break
        
        e = ELEMENTS_DATA[idx]
        item_y = LIST_Y + i * 30
        
        # 선택된 원소 하이라이트
        if idx == sim.selected_idx:
            pygame.draw.rect(screen, (220, 235, 255), (LIST_X + 2, item_y, LIST_W - 4, 28))
            
        # 원소 색상 아이콘
        pygame.draw.rect(screen, e[5], (LIST_X + 10, item_y + 5, 18, 18))
        pygame.draw.rect(screen, BLACK, (LIST_X + 10, item_y + 5, 18, 18), 1)

        # 텍스트 정보
        e_info = f"{e[0]:3d}. {e[1]:3s} {e[2]:8s} | {e[3]:6.2f}g/mol | 상태: {e[4]}"
        txt_surf = font.render(e_info, True, BLACK)
        screen.blit(txt_surf, (LIST_X + 35, item_y + 5))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
