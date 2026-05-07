import pygame
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 854,480
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
        self.board = [[]]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill("white")
    pygame.display.flip()
    clock.tick(240)