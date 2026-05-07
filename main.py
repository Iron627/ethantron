import pygame
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 1024,1024
screen = pygame.display.set_mode((SCREEN_HEIGHT,SCREEN_WIDTH))
running = True
clock = pygame.time.Clock()

# Piece Map: 0: empty space, 1: Pawn, 2: Knight, 3: Bishop, 4: Rook, 5: Queen, 6: King
#            7: Black Pawn, 8: Black Knight, 9: Black Bishop, 10: Black Rook, 11: Black Queen, 12: Black King
material_values = {0:0,1:1,2:3,3:3,4:5,5:9,6:0}

def get_material_value(piece):
    if piece > 6:
        piece -= 6
    return material_values[piece]

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
    def draw(self):
        cell_width = SCREEN_WIDTH // 8
        cell_height = SCREEN_HEIGHT // 8
        for row_no, row in enumerate(self.board):
            for col_no, _ in enumerate(row):
                color = "white" if (row_no + col_no) % 2 == 0 else "black"
                rect = (row_no * cell_width, col_no * cell_height, cell_width, cell_height)
                pygame.draw.rect(self.screen, color, rect)




game_board = Board(screen)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    game_board.draw()
    pygame.display.flip()
    clock.tick(240)
