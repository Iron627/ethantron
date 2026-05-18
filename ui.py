import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import time

import pygame
from engine import *
from engine import Board as EngineBoard

pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 1024,1024
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
running = True
font = pygame.font.Font(None, 96)
WHITE = "#c2c2c2"
BLACK = "#2a4537"
HIGHLIGHT = (255, 210, 84,50)
SELECTED_HIGHLIGHT = (80, 170, 255, 90)
ai_executor = ThreadPoolExecutor(max_workers=1)
ai_future = None
AI_SEARCH_OPTIONS = SearchOptions(
    max_depth=AI_DEPTH,
    max_time=SEARCH_TIME_LIMIT_SECONDS,
)
piece_imgs = {}


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


for piece in range(1,13):
    piece_imgs[piece] = pygame.transform.scale(pygame.image.load(resource_path(f'assets/{piece}.png')).convert_alpha(), (100,100))


def get_mouse_cell():
    x, y = pygame.mouse.get_pos()
    cell_width = SCREEN_WIDTH // 8
    cell_height = SCREEN_HEIGHT // 8
    cell = (y // cell_height, x // cell_width)
    return cell


class Board(EngineBoard):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        cell_width = SCREEN_WIDTH // 8
        cell_height = SCREEN_HEIGHT // 8
        self.hover_highlight = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
        self.hover_highlight.fill(HIGHLIGHT)
        self.selected_highlight = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
        self.selected_highlight.fill(SELECTED_HIGHLIGHT)
        self.move_marker = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
        pygame.draw.circle(
            self.move_marker,
            (120, 120, 120, 140),
            (cell_width // 2, cell_height // 2),
            min(cell_width, cell_height) // 10
        )

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
            self.screen.blit(self.hover_highlight, (col_no * cell_width, row_no * cell_height))
        
        for row_no, row in enumerate(self.board):
            for col_no, _ in enumerate(row):
                piece = self.get_piece((row_no, col_no), self.board)
                if piece == 0:
                    continue
                screen.blit(piece_imgs[piece],((col_no * cell_width) + 10, (row_no * cell_height) + 10))
        if self.selected is not None:
            row_no = self.selected[0]
            col_no = self.selected[1]
            self.screen.blit(self.selected_highlight, (col_no * cell_width, row_no * cell_height))
            for move_row, move_col in self.selected_legal_moves:
                self.screen.blit(self.move_marker, (move_col * cell_width, move_row * cell_height))
        if self.result_text is not None:
            text = font.render(self.result_text, True, "white")
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            pygame.draw.rect(self.screen, "black", text_rect.inflate(40, 30))
            self.screen.blit(text, text_rect)
        elif self.pending_promotion is not None:
            text = font.render("Q: Queen  N: Knight", True, "white")
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            pygame.draw.rect(self.screen, "black", text_rect.inflate(40, 30))
            self.screen.blit(text, text_rect)


def main():
    global running, ai_future

    game_board = Board(screen)
    picked = False
    picked_cell = None

    while running:
        mouse_cell = get_mouse_cell()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_board.pending_promotion is not None:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_n):
                    promotion_choice = "queen" if event.key == pygame.K_q else "knight"
                    start, end = game_board.pending_promotion
                    game_board.move_piece(start, end, promotion_choice=promotion_choice)
                    picked = False
                    picked_cell = None
                    game_board.pending_promotion = None
                    game_board.selected = None
                    game_board.selected_legal_moves = []
                    game_board.turn = not game_board.turn
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and game_board.result_text is None:
                if not game_board.turn:
                    clicked_piece = game_board.get_piece(mouse_cell, game_board.board)
                    if not picked and 0 < clicked_piece < 7:
                        picked = True
                        picked_cell = mouse_cell
                        game_board.selected = picked_cell
                        game_board.selected_legal_moves = game_board.get_legal_moves(picked_cell, game_board.board)
                    elif picked:
                        legal_moves = game_board.selected_legal_moves
                        if clicked_piece == 0 and mouse_cell not in legal_moves:
                            picked = False
                            game_board.selected = None
                            game_board.selected_legal_moves = []
                            picked_cell = None
                        elif mouse_cell not in legal_moves:
                            picked = False
                            game_board.selected = None
                            game_board.selected_legal_moves = []
                            picked_cell = None
                        elif mouse_cell != picked_cell and mouse_cell in legal_moves:
                            picked = False
                            if game_board.is_promotion_move(picked_cell, mouse_cell):
                                game_board.pending_promotion = (picked_cell, mouse_cell)
                            else:
                                game_board.move_piece(picked_cell, mouse_cell)
                                game_board.selected = None
                                game_board.selected_legal_moves = []
                                game_board.turn = not game_board.turn

        if game_board.turn and game_board.result_text is None:
            if ai_future is None:
                if not game_board.check_game_over(True):
                    timer = time.perf_counter()
                    board_snapshot = [row[:] for row in game_board.board]
                    en_passant_snapshot = game_board.en_passant_target
                    castling_snapshot = copy.deepcopy(game_board.castling_rights)
                    ai_future = ai_executor.submit(
                        calculate_ai_move,
                        board_snapshot,
                        en_passant_snapshot,
                        castling_snapshot,
                        AI_SEARCH_OPTIONS,
                    )
            elif ai_future.done():
                move = ai_future.result()
                ai_future = None
                if move is not None:
                    start, end, promotion_choice = normalize_move(move)
                    game_board.move_piece(start, end, promotion_choice or "queen")
                    game_board.turn = not game_board.turn
                    game_board.check_game_over(False)
                    timer = time.perf_counter() - timer
                    print(f"AI move calculated in {timer:.2f} seconds")

        if mouse_cell:
            game_board.hovered = mouse_cell
        game_board.draw()
        pygame.display.flip()

    ai_executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
