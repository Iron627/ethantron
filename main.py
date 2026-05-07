import pygame
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 1024,1024
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
running = True
clock = pygame.time.Clock()
WHITE = "#c2c2c2"
BLACK = "#2a4537"
HIGHLIGHT = (255, 210, 84,50)
# Piece Map: 0: empty space, 1: Pawn, 2: Knight, 3: Bishop, 4: Rook, 5: Queen, 6: King
#            7: Black Pawn, 8: Black Knight, 9: Black Bishop, 10: Black Rook, 11: Black Queen, 12: Black King
material_values = {0:0,1:1,2:3,3:3,4:5,5:9,6:0}
piece_imgs = {}
for piece in range(1,13):
    piece_imgs[piece] = pygame.transform.scale(pygame.image.load(f'assets/{piece}.png').convert_alpha(), (100,100))
def get_material_value(piece):
    if piece > 6:
        piece -= 6
    return material_values[piece]

def get_mouse_cell():
    x, y = pygame.mouse.get_pos()
    cell_width = SCREEN_WIDTH // 8
    cell_height = SCREEN_HEIGHT // 8
    cell = (y // cell_height, x // cell_width)
    return cell


class Board:
    def __init__(self,screen):
        self.screen = screen
        self.board = [
            [10, 8, 9, 11, 12, 9, 8, 10],
            [7, 7, 7, 7, 7, 7, 7, 7],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [4, 2, 3, 5, 6, 3, 2, 4],
        ]
        self.hovered = None
    def draw(self):
        cell_width = SCREEN_WIDTH // 8
        cell_height = SCREEN_HEIGHT // 8
        for row_no, row in enumerate(self.board):
            for col_no, _ in enumerate(row):
                color = WHITE if (row_no + col_no) % 2 == 0 else BLACK
                rect = (col_no * cell_width, row_no * cell_height, cell_width, cell_height)
                pygame.draw.rect(self.screen, color, rect)
        if self.hovered is not None:
            row_no = self.hovered[0]
            col_no = self.hovered[1]
            highlight = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            highlight.fill(HIGHLIGHT)
            self.screen.blit(highlight, (col_no * cell_width, row_no * cell_height))
        for row_no, row in enumerate(self.board):
            for col_no, piece in enumerate(row):
                if piece == 0:
                    continue
                screen.blit(piece_imgs[piece],((col_no * cell_width) + 10, (row_no * cell_height) + 10))

    def eval(self):
        score = 0
        for row in self.board:
            for piece in row:
                if 1 <= piece <= 6:
                    score -= get_material_value(piece)
                elif piece != 0 and piece > 6:
                    score += get_material_value(piece)
        return score



game_board = Board(screen)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    if get_mouse_cell():
        game_board.hovered = get_mouse_cell()
    game_board.draw()
    pygame.display.flip()
    clock.tick(240)
