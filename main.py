import pygame
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 854,480
screen = pygame.display.set_mode((SCREEN_HEIGHT,SCREEN_WIDTH))
running = True
clock = pygame.time.Clock()
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