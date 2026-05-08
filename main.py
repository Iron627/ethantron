import pygame
import copy
from concurrent.futures import ThreadPoolExecutor
import time
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 1024,1024
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
running = True
font = pygame.font.Font(None, 96)
WHITE = "#c2c2c2"
BLACK = "#2a4537"
HIGHLIGHT = (255, 210, 84,50)
SELECTED_HIGHLIGHT = (80, 170, 255, 90)
# Piece Map: 0: empty space, 1: Pawn, 2: Knight, 3: Bishop, 4: Rook, 5: Queen, 6: King
#            7: Black Pawn, 8: Black Knight, 9: Black Bishop, 10: Black Rook, 11: Black Queen, 12: Black King
material_values = {0: 0, 1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}
piece_square_tables = {1: [[0, 0, 0, 0, 0, 0, 0, 0],
     [50, 50, 50, 50, 50, 50, 50, 50],
     [10, 10, 20, 30, 30, 20, 10, 10],
     [5, 5, 10, 25, 25, 10, 5, 5],
     [0, 0, 0, 20, 20, 0, 0, 0],
     [5, -5, -10, 0, 0, -10, -5, 5],
     [5, 10, 10, -20, -20, 10, 10, 5],
     [0, 0, 0, 0, 0, 0, 0, 0]],
 2: [[-50, -40, -30, -30, -30, -30, -40, -50],
     [-40, -20, 0, 5, 5, 0, -20, -40],
     [-30, 5, 10, 15, 15, 10, 5, -30],
     [-30, 0, 15, 20, 20, 15, 0, -30],
     [-30, 5, 15, 20, 20, 15, 5, -30],
     [-30, 0, 10, 15, 15, 10, 0, -30],
     [-40, -20, 0, 0, 0, 0, -20, -40],
     [-50, -40, -30, -30, -30, -30, -40, -50]],
 3: [[-20, -10, -10, -10, -10, -10, -10, -20],
     [-10, 5, 0, 0, 0, 0, 5, -10],
     [-10, 10, 10, 10, 10, 10, 10, -10],
     [-10, 0, 10, 10, 10, 10, 0, -10],
     [-10, 5, 5, 10, 10, 5, 5, -10],
     [-10, 0, 5, 10, 10, 5, 0, -10],
     [-10, 0, 0, 0, 0, 0, 0, -10],
     [-20, -10, -10, -10, -10, -10, -10, -20]],
 4: [[0, 0, 0, 5, 5, 0, 0, 0],
     [-5, 0, 0, 0, 0, 0, 0, -5],
     [-5, 0, 0, 0, 0, 0, 0, -5],
     [-5, 0, 0, 0, 0, 0, 0, -5],
     [-5, 0, 0, 0, 0, 0, 0, -5],
     [-5, 0, 0, 0, 0, 0, 0, -5],
     [5, 10, 10, 10, 10, 10, 10, 5],
     [0, 0, 0, 0, 0, 0, 0, 0]],
 5: [[-20, -10, -10, -5, -5, -10, -10, -20],
     [-10, 0, 0, 0, 0, 0, 0, -10],
     [-10, 0, 5, 5, 5, 5, 0, -10],
     [-5, 0, 5, 5, 5, 5, 0, -5],
     [0, 0, 5, 5, 5, 5, 0, -5],
     [-10, 5, 5, 5, 5, 5, 0, -10],
     [-10, 0, 5, 0, 0, 0, 0, -10],
     [-20, -10, -10, -5, -5, -10, -10, -20]],
 6: [[-30, -40, -40, -50, -50, -40, -40, -30],
     [-30, -40, -40, -50, -50, -40, -40, -30],
     [-30, -40, -40, -50, -50, -40, -40, -30],
     [-30, -40, -40, -50, -50, -40, -40, -30],
     [-20, -30, -30, -40, -40, -30, -30, -20],
     [-10, -20, -20, -20, -20, -20, -20, -10],
     [20, 20, 0, 0, 0, 0, 20, 20],
     [20, 30, 10, 0, 0, 10, 30, 20]]}
AI_DEPTH = 4
ai_executor = ThreadPoolExecutor(max_workers=1)
ai_future = None
piece_imgs = {}
for piece in range(1,13):
    piece_imgs[piece] = pygame.transform.scale(pygame.image.load(f'assets/{piece}.png').convert_alpha(), (100,100))
def get_material_value(piece):
    if piece > 6:
        piece -= 6
    return material_values[piece]

def get_piece_square_value(piece, row, col):
    base_piece = piece - 6 if piece > 6 else piece
    table_row = 7 - row if piece > 6 else row
    return piece_square_tables[base_piece][table_row][col]
EVAL_TABLE = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(13)]
for piece in range(1, 13):
    base_piece = piece - 6 if piece > 6 else piece
    for row in range(8):
        for col in range(8):
            pst_row = 7 - row if piece > 6 else row
            value = material_values[base_piece] + piece_square_tables[base_piece][pst_row][col]
            EVAL_TABLE[piece][row][col] = value if piece > 6 else -value

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
        self.selected = None
        self.selected_legal_moves = []
        self.turn = False
        self.en_passant_target = None
        self.castling_rights = {
            'white': {'king_side': True, 'queen_side': True},
            'black': {'king_side': True, 'queen_side': True},
        }
        self.result_text = None
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
    def is_in_check(self, color, board):
        king_piece = 6 if color == 'white' else 12
        king_row = None
        king_col = None
        for row_no in range(8):
            for col_no in range(8):
                if board[row_no][col_no] == king_piece:
                    king_row = row_no
                    king_col = col_no
                    break
            if king_row is not None:
                break

        if king_row is None:
            return False

        if color == 'white':
            pawn_piece = 7
            knight_piece = 8
            bishop_piece = 9
            rook_piece = 10
            queen_piece = 11
            enemy_king_piece = 12
            pawn_row = king_row - 1
        else:
            pawn_piece = 1
            knight_piece = 2
            bishop_piece = 3
            rook_piece = 4
            queen_piece = 5
            enemy_king_piece = 6
            pawn_row = king_row + 1

        if 0 <= pawn_row < 8:
            for col_offset in (-1, 1):
                pawn_col = king_col + col_offset
                if 0 <= pawn_col < 8 and board[pawn_row][pawn_col] == pawn_piece:
                    return True

        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for row_offset, col_offset in knight_offsets:
            target_row = king_row + row_offset
            target_col = king_col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == knight_piece:
                    return True

        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for row_offset, col_offset in king_offsets:
            target_row = king_row + row_offset
            target_col = king_col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == enemy_king_piece:
                    return True

        diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for row_dir, col_dir in diagonal_directions:
            target_row = king_row + row_dir
            target_col = king_col + col_dir
            while 0 <= target_row < 8 and 0 <= target_col < 8:
                piece = board[target_row][target_col]
                if piece != 0:
                    if piece in (bishop_piece, queen_piece):
                        return True
                    break
                target_row += row_dir
                target_col += col_dir

        straight_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for row_dir, col_dir in straight_directions:
            target_row = king_row + row_dir
            target_col = king_col + col_dir
            while 0 <= target_row < 8 and 0 <= target_col < 8:
                piece = board[target_row][target_col]
                if piece != 0:
                    if piece in (rook_piece, queen_piece):
                        return True
                    break
                target_row += row_dir
                target_col += col_dir

        return False
    def get_piece(self, i,board):
        return board[i[0]][i[1]]
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

    def eval(self, board=None):
        if board is None:
            board = self.board

        score = 0
        eval_table = EVAL_TABLE
        white_bishops = 0
        black_bishops = 0
        for row_no in range(8):
            row = board[row_no]
            for col_no in range(8):
                piece = row[col_no]
                score += eval_table[row[col_no]][row_no][col_no]
                if piece == 3:
                    white_bishops += 1
                elif piece == 9:
                    black_bishops += 1
        if white_bishops >= 2:
            score -= 30
        if black_bishops >= 2:
            score += 30
        return score

    def get_all_moves(self, board, black_turn):
        moves = []
        for row_no, row in enumerate(board):
            for col_no, piece in enumerate(row):
                if black_turn and 7 <= piece <= 12:
                    start = (row_no, col_no)
                elif not black_turn and 1 <= piece <= 6:
                    start = (row_no, col_no)
                else:
                    continue

                for end in self.get_legal_moves(start, board):
                    moves.append((start, end))
        return moves

    def check_game_over(self, black_turn):
        if self.get_all_moves(self.board, black_turn):
            return False

        color = 'black' if black_turn else 'white'
        if self.is_in_check(color, self.board):
            self.result_text = 'White wins' if black_turn else 'Black wins'
        else:
            self.result_text = 'Stalemate'
        return True

    def move_on_copy(self, board, move):
        start, end = move
        new_board = [row[:] for row in board]
        moving_piece = new_board[start[0]][start[1]]
        if moving_piece in (6, 12) and abs(end[1] - start[1]) == 2:
            row = start[0]
            if end[1] == 6:
                new_board[row][5] = new_board[row][7]
                new_board[row][7] = 0
            elif end[1] == 2:
                new_board[row][3] = new_board[row][0]
                new_board[row][0] = 0
        new_board[end[0]][end[1]] = moving_piece
        new_board[start[0]][start[1]] = 0
        return new_board

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.eval(board)

        moves = self.get_all_moves(board, maximizing)
        if not moves:
            return self.eval(board)

        moves.sort(key=lambda move: self.score_move(board, move), reverse=True)

        if maximizing:
            best = float('-inf')
            for move in moves:
                score = self.minimax(self.move_on_copy(board, move), depth - 1, alpha, beta, False)
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best

        best = float('inf')
        for move in moves:
            score = self.minimax(self.move_on_copy(board, move), depth - 1, alpha, beta, True)
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

    def score_move(self, board, move):
        start, end = move
        moving_piece = board[start[0]][start[1]]
        captured_piece = board[end[0]][end[1]]
        score = 0

        if captured_piece != 0:
            score += 10 * get_material_value(captured_piece)
            score -= get_material_value(moving_piece)

        if end in ((3, 3), (3, 4), (4, 3), (4, 4)):
            score += 10
        
        return score

    def get_best_move(self, depth=AI_DEPTH):
        best_move = None
        best_score = float('-inf')
        moves = self.get_all_moves(self.board, True)
        moves.sort(key=lambda move: self.score_move(self.board, move), reverse=True)

        for move in moves:
            board_after_move = self.move_on_copy(self.board, move)
            score = self.minimax(board_after_move, depth - 1, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def ai_move(self):
        move = self.get_best_move()
        if move is not None:
            self.move_piece(move[0], move[1])
            self.turn = not self.turn

    def move_piece(self,i,f):
        moving_piece = self.get_piece(i, self.board)
        captured_piece = self.get_piece(f, self.board)

        is_en_passant_capture = (
            moving_piece in (1, 7)
            and self.en_passant_target == f
            and i[1] != f[1]
            and self.board[f[0]][f[1]] == 0
        )

        if is_en_passant_capture:
            self.board[i[0]][f[1]] = 0

        if moving_piece in (6, 12) and abs(f[1] - i[1]) == 2:
            row = i[0]
            if f[1] == 6:
                self.board[row][5] = self.board[row][7]
                self.board[row][7] = 0
            elif f[1] == 2:
                self.board[row][3] = self.board[row][0]
                self.board[row][0] = 0

        self.board[f[0]][f[1]] = moving_piece
        self.board[i[0]][i[1]] = 0

        self.update_castling_rights(i, f, moving_piece, captured_piece)

        if moving_piece in (1, 7) and abs(f[0] - i[0]) == 2:
            self.en_passant_target = ((i[0] + f[0]) // 2, i[1])
        else:
            self.en_passant_target = None

    def update_castling_rights(self, start, end, moving_piece, captured_piece):
        if moving_piece == 6:
            self.castling_rights['white']['king_side'] = False
            self.castling_rights['white']['queen_side'] = False
        elif moving_piece == 12:
            self.castling_rights['black']['king_side'] = False
            self.castling_rights['black']['queen_side'] = False
        elif moving_piece == 4:
            if start == (7, 0):
                self.castling_rights['white']['queen_side'] = False
            elif start == (7, 7):
                self.castling_rights['white']['king_side'] = False
        elif moving_piece == 10:
            if start == (0, 0):
                self.castling_rights['black']['queen_side'] = False
            elif start == (0, 7):
                self.castling_rights['black']['king_side'] = False

        if captured_piece == 4:
            if end == (7, 0):
                self.castling_rights['white']['queen_side'] = False
            elif end == (7, 7):
                self.castling_rights['white']['king_side'] = False
        elif captured_piece == 10:
            if end == (0, 0):
                self.castling_rights['black']['queen_side'] = False
            elif end == (0, 7):
                self.castling_rights['black']['king_side'] = False

    def can_castle(self, color, side, board):
        row = 7 if color == 'white' else 0
        king_piece = 6 if color == 'white' else 12
        rook_piece = 4 if color == 'white' else 10

        if not self.castling_rights[color][side]:
            return False
        if board[row][4] != king_piece:
            return False
        if self.is_in_check(color, board):
            return False

        if side == 'king_side':
            rook_col = 7
            empty_cols = (5, 6)
            king_path_cols = (5, 6)
        else:
            rook_col = 0
            empty_cols = (1, 2, 3)
            king_path_cols = (3, 2)

        if board[row][rook_col] != rook_piece:
            return False
        for col in empty_cols:
            if board[row][col] != 0:
                return False
        for col in king_path_cols:
            temp_board = [board_row[:] for board_row in board]
            temp_board[row][4] = 0
            temp_board[row][col] = king_piece
            if self.is_in_check(color, temp_board):
                return False

        return True
    def get_legal_moves(self,cell,board,validate_check=True):
        legal_moves = []
        piece = self.get_piece(cell, board)
        if piece == 2 or piece == 8:
            knight_offsets = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            is_white_piece = 1 <= piece <= 6
            for row_offset, col_offset in knight_offsets:
                target_row = cell[0] + row_offset
                target_col = cell[1] + col_offset
                if not (0 <= target_row < 8 and 0 <= target_col < 8):
                    continue

                target_piece = board[target_row][target_col]
                if target_piece == 0:
                    legal_moves.append((target_row, target_col))
                    continue

                if is_white_piece and target_piece > 6:
                    legal_moves.append((target_row, target_col))
                elif not is_white_piece and 1 <= target_piece <= 6:
                    legal_moves.append((target_row, target_col))
        if piece == 1 or piece == 7:
            direction = -1 if piece == 1 else 1
            start_row = 6 if piece == 1 else 1
            is_white_piece = 1 <= piece <= 6

            one_step_row = cell[0] + direction
            if 0 <= one_step_row < 8 and board[one_step_row][cell[1]] == 0:
                legal_moves.append((one_step_row, cell[1]))

                two_step_row = cell[0] + (2 * direction)
                if cell[0] == start_row and 0 <= two_step_row < 8 and board[two_step_row][cell[1]] == 0:
                    legal_moves.append((two_step_row, cell[1]))

            for col_offset in (-1, 1):
                capture_row = cell[0] + direction
                capture_col = cell[1] + col_offset
                if not (0 <= capture_row < 8 and 0 <= capture_col < 8):
                    continue

                target_piece = board[capture_row][capture_col]
                if target_piece == 0:
                    if self.en_passant_target == (capture_row, capture_col):
                        legal_moves.append((capture_row, capture_col))
                    continue

                if is_white_piece and target_piece > 6:
                    legal_moves.append((capture_row, capture_col))
                elif not is_white_piece and 1 <= target_piece <= 6:
                    legal_moves.append((capture_row, capture_col))
        if piece == 4 or piece == 10:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            is_white_piece = 1 <= piece <= 6
            for row_dir, col_dir in directions:
                for step in range(1, 8):
                    target_row = cell[0] + row_dir * step
                    target_col = cell[1] + col_dir * step
                    if not (0 <= target_row < 8 and 0 <= target_col < 8):
                        break

                    target_piece = board[target_row][target_col]
                    if target_piece == 0:
                        legal_moves.append((target_row, target_col))
                    else:
                        if is_white_piece and target_piece > 6:
                            legal_moves.append((target_row, target_col))
                        elif not is_white_piece and 1 <= target_piece <= 6:
                            legal_moves.append((target_row, target_col))
                        break
        if piece == 3 or piece == 9:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            is_white_piece = 1 <= piece <= 6
            for row_dir, col_dir in directions:
                for step in range(1, 8):
                    target_row = cell[0] + row_dir * step
                    target_col = cell[1] + col_dir * step
                    if not (0 <= target_row < 8 and 0 <= target_col < 8):
                        break

                    target_piece = board[target_row][target_col]
                    if target_piece == 0:
                        legal_moves.append((target_row, target_col))
                    else:
                        if is_white_piece and target_piece > 6:
                            legal_moves.append((target_row, target_col))
                        elif not is_white_piece and 1 <= target_piece <= 6:
                            legal_moves.append((target_row, target_col))
                        break
        if piece == 5 or piece == 11:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            is_white_piece = 1 <= piece <= 6
            for row_dir, col_dir in directions:
                for step in range(1, 8):
                    target_row = cell[0] + row_dir * step
                    target_col = cell[1] + col_dir * step
                    if not (0 <= target_row < 8 and 0 <= target_col < 8):
                        break

                    target_piece = board[target_row][target_col]
                    if target_piece == 0:
                        legal_moves.append((target_row, target_col))
                    else:
                        if is_white_piece and target_piece > 6:
                            legal_moves.append((target_row, target_col))
                        elif not is_white_piece and 1 <= target_piece <= 6:
                            legal_moves.append((target_row, target_col))
                        break
        if piece == 6 or piece == 12:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            is_white_piece = 1 <= piece <= 6
            for row_dir, col_dir in directions:
                target_row = cell[0] + row_dir
                target_col = cell[1] + col_dir
                if not (0 <= target_row < 8 and 0 <= target_col < 8):
                    continue

                target_piece = board[target_row][target_col]
                if target_piece == 0:
                    legal_moves.append((target_row, target_col))
                else:
                    if is_white_piece and target_piece > 6:
                        legal_moves.append((target_row, target_col))
                    elif not is_white_piece and 1 <= target_piece <= 6:
                        legal_moves.append((target_row, target_col))
            if validate_check and cell == ((7, 4) if is_white_piece else (0, 4)):
                color = 'white' if is_white_piece else 'black'
                if self.can_castle(color, 'king_side', board):
                    legal_moves.append((cell[0], 6))
                if self.can_castle(color, 'queen_side', board):
                    legal_moves.append((cell[0], 2))
        if validate_check:
            color = 'white' if piece <= 6 else 'black'
            filtered_moves = []
            for move in legal_moves:
                target_piece = board[move[0]][move[1]]
                if target_piece in (6, 12):
                    continue

                temp_board = self.move_on_copy(board, (cell, move))
                if not self.is_in_check(color, temp_board):
                    filtered_moves.append(move)
            legal_moves = filtered_moves

        return legal_moves
            
game_board = Board(screen)

def calculate_ai_move(board_state, en_passant_target, castling_rights):
    worker_board = Board(None)
    worker_board.board = [row[:] for row in board_state]
    worker_board.en_passant_target = en_passant_target
    worker_board.castling_rights = copy.deepcopy(castling_rights)
    return worker_board.get_best_move()

picked = False
while running:
    mouse_cell = get_mouse_cell()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
                )
        elif ai_future.done():
            move = ai_future.result()
            ai_future = None
            if move is not None:
                game_board.move_piece(move[0], move[1])
                game_board.turn = not game_board.turn
                game_board.check_game_over(False)
                timer = time.perf_counter() - timer
                print(f"AI move calculated in {timer:.2f} seconds")

    if mouse_cell:
        game_board.hovered = mouse_cell
    game_board.draw()
    pygame.display.flip()
ai_executor.shutdown(wait=False)
