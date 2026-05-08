import pygame
pygame.init()
SCREEN_HEIGHT,SCREEN_WIDTH = 1024,1024
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
running = True
clock = pygame.time.Clock()
font = pygame.font.Font(None, 96)
WHITE = "#c2c2c2"
BLACK = "#2a4537"
HIGHLIGHT = (255, 210, 84,50)
SELECTED_HIGHLIGHT = (80, 170, 255, 90)
# Piece Map: 0: empty space, 1: Pawn, 2: Knight, 3: Bishop, 4: Rook, 5: Queen, 6: King
#            7: Black Pawn, 8: Black Knight, 9: Black Bishop, 10: Black Rook, 11: Black Queen, 12: Black King
material_values = {0:0,1:1,2:3,3:3,4:5,5:9,6:0}
AI_DEPTH = 2
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
        self.selected = None
        self.turn = False
        self.en_passant_target = None
        self.result_text = None
    def is_in_check(self, color, board):
        king_piece = 6 if color == 'white' else 12
        king_pos = None
        for row_no in range(8):
            for col_no in range(8):
                if board[row_no][col_no] == king_piece:
                    king_pos = (row_no, col_no)
                    break
            if king_pos is not None:
                break

        if king_pos is None:
            return False

        is_opponent_piece = (lambda p: 7 <= p <= 12) if color == 'white' else (lambda p: 1 <= p <= 6)
        for row_no in range(8):
            for col_no in range(8):
                piece = board[row_no][col_no]
                if not is_opponent_piece(piece):
                    continue
                if piece in (1, 7):
                    direction = -1 if piece == 1 else 1
                    for col_offset in (-1, 1):
                        if (row_no + direction, col_no + col_offset) == king_pos:
                            return True
                    continue
                legal_moves = self.get_legal_moves((row_no, col_no), board, validate_check=False)
                if king_pos in legal_moves:
                    return True
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
            highlight = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            highlight.fill(HIGHLIGHT)
            self.screen.blit(highlight, (col_no * cell_width, row_no * cell_height))
        
        for row_no, row in enumerate(self.board):
            for col_no, _ in enumerate(row):
                piece = self.get_piece((row_no, col_no), self.board)
                if piece == 0:
                    continue
                screen.blit(piece_imgs[piece],((col_no * cell_width) + 10, (row_no * cell_height) + 10))
        if self.selected is not None:
            row_no = self.selected[0]
            col_no = self.selected[1]
            selected_highlight = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            selected_highlight.fill(SELECTED_HIGHLIGHT)
            self.screen.blit(selected_highlight, (col_no * cell_width, row_no * cell_height))
            legal_moves = self.get_legal_moves(self.selected,self.board)
            for move_row, move_col in legal_moves:
                circle_radius = min(cell_width, cell_height) // 10
                move_marker = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                pygame.draw.circle(
                    move_marker,
                    (120, 120, 120, 140),
                    (cell_width // 2, cell_height // 2),
                    circle_radius
                )
                self.screen.blit(move_marker, (move_col * cell_width, move_row * cell_height))
        if self.result_text is not None:
            text = font.render(self.result_text, True, "white")
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            pygame.draw.rect(self.screen, "black", text_rect.inflate(40, 30))
            self.screen.blit(text, text_rect)

    def eval(self, board=None):
        if board is None:
            board = self.board

        score = 0
        for row in board:
            for piece in row:
                if 1 <= piece <= 6:
                    score -= get_material_value(piece)
                elif piece != 0 and piece > 6:
                    score += get_material_value(piece)
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
        new_board[end[0]][end[1]] = new_board[start[0]][start[1]]
        new_board[start[0]][start[1]] = 0
        return new_board

    def minimax(self, board, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.eval(board)

        moves = self.get_all_moves(board, maximizing)
        if not moves:
            return self.eval(board)

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

    def get_best_move(self, depth=AI_DEPTH):
        best_move = None
        best_score = float('-inf')

        for move in self.get_all_moves(self.board, True):
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

        is_en_passant_capture = (
            moving_piece in (1, 7)
            and self.en_passant_target == f
            and i[1] != f[1]
            and self.board[f[0]][f[1]] == 0
        )

        if is_en_passant_capture:
            self.board[i[0]][f[1]] = 0

        self.board[f[0]][f[1]] = moving_piece
        self.board[i[0]][i[1]] = 0

        if moving_piece in (1, 7) and abs(f[0] - i[0]) == 2:
            self.en_passant_target = ((i[0] + f[0]) // 2, i[1])
        else:
            self.en_passant_target = None
    def get_legal_moves(self,cell,board,validate_check=True):
        self.dummy_board = [row[:] for row in board]
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
        if validate_check:
            for move in legal_moves[:]:
                if board[move[0]][move[1]] == 12 or board[move[0]][move[1]] == 6:
                    legal_moves.remove(move)
        if validate_check:
            for move in legal_moves[:]:
                temp_board = [row[:] for row in board]
                temp_board[move[0]][move[1]] = piece
                temp_board[cell[0]][cell[1]] = 0
                if self.is_in_check('white' if piece <= 6 else 'black', temp_board):
                    legal_moves.remove(move)

        return legal_moves
            
game_board = Board(screen)
picked = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and game_board.result_text is None:
            if not game_board.turn:
                if not picked and 0 < game_board.get_piece(get_mouse_cell(), game_board.board) < 7:
                    picked = True
                    picked_cell = get_mouse_cell()
                    game_board.selected = picked_cell
                elif picked:
                    if game_board.get_piece(get_mouse_cell(), game_board.board) == 0 and get_mouse_cell() not in game_board.get_legal_moves(picked_cell, game_board.board):
                        picked = False
                        game_board.selected = None
                        picked_cell = None
                    elif get_mouse_cell() not in game_board.get_legal_moves(picked_cell, game_board.board):
                        picked = False
                        game_board.selected = None
                        picked_cell = None
                    elif get_mouse_cell() != picked_cell and get_mouse_cell() in game_board.get_legal_moves(picked_cell, game_board.board):
                        picked = False
                        game_board.move_piece(picked_cell,get_mouse_cell())
                        game_board.selected = None
                        game_board.turn = not game_board.turn

    if game_board.turn and game_board.result_text is None:
        if not game_board.check_game_over(True):
            game_board.ai_move()
            game_board.check_game_over(False)

    if get_mouse_cell():
        game_board.hovered = get_mouse_cell()
    game_board.draw()
    pygame.display.flip()
    clock.tick(240)
