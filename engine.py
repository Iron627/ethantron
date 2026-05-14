import copy
import random
import time
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
MATE_SCORE = 1000000
QUIESCENCE_DEPTH = 4
SEARCH_TIME_LIMIT_SECONDS = 15
USE_BOARD_STATE = object()
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2
TT_MAX_ENTRIES = 500000
KING_ATTACK_WEIGHTS = {1: 6, 2: 14, 3: 14, 4: 20, 5: 32, 6: 0}

_zobrist_rng = random.Random(0)
ZOBRIST_PIECE = [
    [[_zobrist_rng.getrandbits(64) for _ in range(8)] for _ in range(8)]
    for _ in range(13)
]
ZOBRIST_BLACK_TO_MOVE = _zobrist_rng.getrandbits(64)
ZOBRIST_CASTLING = [_zobrist_rng.getrandbits(64) for _ in range(16)]
ZOBRIST_EN_PASSANT_FILE = [_zobrist_rng.getrandbits(64) for _ in range(8)]


def castling_rights_to_index(castling_rights):
    idx = 0
    if castling_rights['white']['king_side']:
        idx |= 1
    if castling_rights['white']['queen_side']:
        idx |= 2
    if castling_rights['black']['king_side']:
        idx |= 4
    if castling_rights['black']['queen_side']:
        idx |= 8
    return idx


def hash_position(board, black_to_move, en_passant_target, castling_rights):
    h = 0
    for row_no in range(8):
        for col_no in range(8):
            piece = board[row_no][col_no]
            if piece != 0:
                h ^= ZOBRIST_PIECE[piece][row_no][col_no]

    if black_to_move:
        h ^= ZOBRIST_BLACK_TO_MOVE

    h ^= ZOBRIST_CASTLING[castling_rights_to_index(castling_rights)]

    if en_passant_target is not None:
        h ^= ZOBRIST_EN_PASSANT_FILE[en_passant_target[1]]

    return h


def get_material_value(piece):
    if piece > 6:
        piece -= 6
    return material_values[piece]

def promote_piece_if_needed(piece, row, promotion_choice="queen"):
    white_promotions = {"queen": 5, "knight": 2}
    black_promotions = {"queen": 11, "knight": 8}
    if promotion_choice not in white_promotions:
        promotion_choice = "queen"

    if piece == 1 and row == 0:
        return white_promotions[promotion_choice]
    if piece == 7 and row == 7:
        return black_promotions[promotion_choice]
    return piece

def normalize_move(move):
    if len(move) == 2:
        start, end = move
        return start, end, None
    start, end, promotion_choice = move
    return start, end, promotion_choice

def get_promotion_choices(piece, row):
    if (piece == 1 and row == 0) or (piece == 7 and row == 7):
        return ("queen", "knight")
    return (None,)

def copy_castling_rights(castling_rights):
    return {
        'white': {
            'king_side': castling_rights['white']['king_side'],
            'queen_side': castling_rights['white']['queen_side'],
        },
        'black': {
            'king_side': castling_rights['black']['king_side'],
            'queen_side': castling_rights['black']['queen_side'],
        },
    }

EVAL_TABLE = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(13)]
for piece in range(1, 13):
    base_piece = piece - 6 if piece > 6 else piece
    for row in range(8):
        for col in range(8):
            pst_row = 7 - row if piece > 6 else row
            value = material_values[base_piece] + piece_square_tables[base_piece][pst_row][col]
            EVAL_TABLE[piece][row][col] = value if piece > 6 else -value

class Board:
    def __init__(self, screen=None):
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
        self.pending_promotion = None
        self.turn = False
        self.en_passant_target = None
        self.castling_rights = {
            'white': {'king_side': True, 'queen_side': True},
            'black': {'king_side': True, 'queen_side': True},
        }
        self.result_text = None
        self.tt = {}
        self.qtt = {}
        self.search_deadline = None
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
        score += self.evaluate_king_safety(board)
        return score

    def evaluate_king_safety(self, board):
        white_penalty = self.king_safety_penalty(board, 'white')
        black_penalty = self.king_safety_penalty(board, 'black')
        return white_penalty - black_penalty

    def king_safety_penalty(self, board, color):
        king_piece = 6 if color == 'white' else 12
        king_square = self.find_piece(board, king_piece)
        if king_square is None:
            return 0

        king_row, king_col = king_square
        attacked_by_black = color == 'white'
        penalty = 40 if self.is_in_check(color, board) else 0

        for row in range(max(0, king_row - 1), min(8, king_row + 2)):
            for col in range(max(0, king_col - 1), min(8, king_col + 2)):
                penalty += self.attack_pressure_on_square(board, row, col, attacked_by_black)

        friendly_pawn = 1 if color == 'white' else 7
        forward = -1 if color == 'white' else 1
        for col in range(max(0, king_col - 1), min(8, king_col + 2)):
            shield_row = king_row + forward
            backup_row = king_row + (2 * forward)
            if 0 <= shield_row < 8 and board[shield_row][col] == friendly_pawn:
                continue
            if 0 <= backup_row < 8 and board[backup_row][col] == friendly_pawn:
                penalty += 6
            else:
                penalty += 12

            has_friendly_pawn_on_file = any(row[col] == friendly_pawn for row in board)
            has_any_pawn_on_file = any(row[col] in (1, 7) for row in board)
            if not has_friendly_pawn_on_file:
                penalty += 8
            if not has_any_pawn_on_file:
                penalty += 6

        attacking_material = self.non_pawn_material(board, attacked_by_black)
        phase = min(100, max(25, attacking_material * 100 // 2400))
        return penalty * phase // 100

    def find_piece(self, board, target_piece):
        for row_no, row in enumerate(board):
            for col_no, piece in enumerate(row):
                if piece == target_piece:
                    return row_no, col_no
        return None

    def non_pawn_material(self, board, black_pieces):
        total = 0
        for row in board:
            for piece in row:
                if black_pieces and 8 <= piece <= 11:
                    total += get_material_value(piece)
                elif not black_pieces and 2 <= piece <= 5:
                    total += get_material_value(piece)
        return total

    def attack_pressure_on_square(self, board, row, col, attacked_by_black):
        pawn_piece = 7 if attacked_by_black else 1
        knight_piece = 8 if attacked_by_black else 2
        bishop_piece = 9 if attacked_by_black else 3
        rook_piece = 10 if attacked_by_black else 4
        queen_piece = 11 if attacked_by_black else 5
        king_piece = 12 if attacked_by_black else 6
        pressure = 0

        pawn_source_row = row - 1 if attacked_by_black else row + 1
        if 0 <= pawn_source_row < 8:
            for pawn_col in (col - 1, col + 1):
                if 0 <= pawn_col < 8 and board[pawn_source_row][pawn_col] == pawn_piece:
                    pressure += KING_ATTACK_WEIGHTS[1]

        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for row_offset, col_offset in knight_offsets:
            target_row = row + row_offset
            target_col = col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == knight_piece:
                    pressure += KING_ATTACK_WEIGHTS[2]

        diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for row_dir, col_dir in diagonal_directions:
            target_row = row + row_dir
            target_col = col + col_dir
            while 0 <= target_row < 8 and 0 <= target_col < 8:
                piece = board[target_row][target_col]
                if piece != 0:
                    if piece in (bishop_piece, queen_piece):
                        pressure += KING_ATTACK_WEIGHTS[3 if piece == bishop_piece else 5]
                    break
                target_row += row_dir
                target_col += col_dir

        straight_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for row_dir, col_dir in straight_directions:
            target_row = row + row_dir
            target_col = col + col_dir
            while 0 <= target_row < 8 and 0 <= target_col < 8:
                piece = board[target_row][target_col]
                if piece != 0:
                    if piece in (rook_piece, queen_piece):
                        pressure += KING_ATTACK_WEIGHTS[4 if piece == rook_piece else 5]
                    break
                target_row += row_dir
                target_col += col_dir

        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for row_offset, col_offset in king_offsets:
            target_row = row + row_offset
            target_col = col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == king_piece:
                    pressure += KING_ATTACK_WEIGHTS[6]

        return pressure

    def get_all_moves(self, board, black_turn, en_passant_target=USE_BOARD_STATE, castling_rights=None):
        moves = []
        for row_no, row in enumerate(board):
            for col_no, piece in enumerate(row):
                if black_turn and 7 <= piece <= 12:
                    start = (row_no, col_no)
                elif not black_turn and 1 <= piece <= 6:
                    start = (row_no, col_no)
                else:
                    continue

                for end in self.get_legal_moves(start, board, True, en_passant_target, castling_rights):
                    for promotion_choice in get_promotion_choices(piece, end[0]):
                        if promotion_choice is None:
                            moves.append((start, end))
                        else:
                            moves.append((start, end, promotion_choice))
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

    def apply_move_to_copy(
        self,
        board,
        move,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
    ):
        start, end, promotion_choice = normalize_move(move)
        if en_passant_target is USE_BOARD_STATE:
            en_passant_target = self.en_passant_target
        new_castling_rights = copy_castling_rights(
            self.castling_rights if castling_rights is None else castling_rights
        )
        new_board = [row[:] for row in board]
        moving_piece = new_board[start[0]][start[1]]
        captured_piece = new_board[end[0]][end[1]]

        is_en_passant_capture = (
            moving_piece in (1, 7)
            and en_passant_target == end
            and start[1] != end[1]
            and new_board[end[0]][end[1]] == 0
        )
        if is_en_passant_capture:
            captured_piece = new_board[start[0]][end[1]]
            new_board[start[0]][end[1]] = 0

        if moving_piece in (6, 12) and abs(end[1] - start[1]) == 2:
            row = start[0]
            if end[1] == 6:
                new_board[row][5] = new_board[row][7]
                new_board[row][7] = 0
            elif end[1] == 2:
                new_board[row][3] = new_board[row][0]
                new_board[row][0] = 0
        new_board[end[0]][end[1]] = promote_piece_if_needed(
            moving_piece,
            end[0],
            promotion_choice or "queen",
        )
        new_board[start[0]][start[1]] = 0

        self.update_castling_rights_for(
            new_castling_rights,
            start,
            end,
            moving_piece,
            captured_piece,
        )

        if moving_piece in (1, 7) and abs(end[0] - start[0]) == 2:
            new_en_passant_target = ((start[0] + end[0]) // 2, start[1])
        else:
            new_en_passant_target = None

        return new_board, new_en_passant_target, new_castling_rights

    def move_on_copy(
        self,
        board,
        move,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
    ):
        new_board, _, _ = self.apply_move_to_copy(
            board,
            move,
            en_passant_target,
            castling_rights,
        )
        return new_board

    def minimax(
        self,
        board,
        depth,
        alpha,
        beta,
        maximizing,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
    ):
        if self.search_deadline is not None and time.monotonic() >= self.search_deadline:
            raise TimeoutError

        if en_passant_target is USE_BOARD_STATE:
            en_passant_target = self.en_passant_target
        if castling_rights is None:
            castling_rights = self.castling_rights

        position_key = hash_position(board, maximizing, en_passant_target, castling_rights)
        tt_entry = self.tt.get(position_key)
        if tt_entry is not None and tt_entry[0] >= depth:
            _, tt_flag, tt_score, _ = tt_entry
            if tt_flag == TT_EXACT:
                return tt_score
            if tt_flag == TT_LOWERBOUND:
                alpha = max(alpha, tt_score)
            elif tt_flag == TT_UPPERBOUND:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

        original_alpha = alpha
        original_beta = beta

        if depth == 0:
            return self.quiescence(
                board,
                alpha,
                beta,
                maximizing,
                en_passant_target,
                castling_rights,
                QUIESCENCE_DEPTH,
            )

        moves = self.get_all_moves(board, maximizing, en_passant_target, castling_rights)
        if not moves:
            color = 'black' if maximizing else 'white'
            if self.is_in_check(color, board):
                return -MATE_SCORE if maximizing else MATE_SCORE
            return 0

        moves.sort(key=lambda move: self.score_move(board, move, en_passant_target), reverse=True)
        if tt_entry is not None and tt_entry[3] in moves:
            tt_move = tt_entry[3]
            moves.remove(tt_move)
            moves.insert(0, tt_move)

        if maximizing:
            best = float('-inf')
            best_move = None
            for move in moves:
                next_board, next_en_passant, next_castling = self.apply_move_to_copy(
                    board,
                    move,
                    en_passant_target,
                    castling_rights,
                )
                score = self.minimax(
                    next_board,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    next_en_passant,
                    next_castling,
                )
                if score > best:
                    best = score
                    best_move = move
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            if len(self.tt) >= TT_MAX_ENTRIES:
                self.tt.clear()
            if best <= original_alpha:
                tt_flag = TT_UPPERBOUND
            elif best >= original_beta:
                tt_flag = TT_LOWERBOUND
            else:
                tt_flag = TT_EXACT
            self.tt[position_key] = (depth, tt_flag, best, best_move)
            return best

        best = float('inf')
        best_move = None
        for move in moves:
            next_board, next_en_passant, next_castling = self.apply_move_to_copy(
                board,
                move,
                en_passant_target,
                castling_rights,
            )
            score = self.minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                True,
                next_en_passant,
                next_castling,
            )
            if score < best:
                best = score
                best_move = move
            beta = min(beta, best)
            if beta <= alpha:
                break
        if len(self.tt) >= TT_MAX_ENTRIES:
            self.tt.clear()
        if best <= original_alpha:
            tt_flag = TT_UPPERBOUND
        elif best >= original_beta:
            tt_flag = TT_LOWERBOUND
        else:
            tt_flag = TT_EXACT
        self.tt[position_key] = (depth, tt_flag, best, best_move)
        return best

    def quiescence(
        self,
        board,
        alpha,
        beta,
        maximizing,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
        depth=QUIESCENCE_DEPTH,
    ):
        if self.search_deadline is not None and time.monotonic() >= self.search_deadline:
            raise TimeoutError

        if en_passant_target is USE_BOARD_STATE:
            en_passant_target = self.en_passant_target
        if castling_rights is None:
            castling_rights = self.castling_rights

        position_key = hash_position(board, maximizing, en_passant_target, castling_rights)
        original_alpha = alpha
        original_beta = beta
        tt_entry = self.qtt.get(position_key)
        if tt_entry is not None and tt_entry[0] >= depth:
            _, tt_flag, tt_score = tt_entry
            if tt_flag == TT_EXACT:
                return tt_score
            if tt_flag == TT_LOWERBOUND:
                alpha = max(alpha, tt_score)
            elif tt_flag == TT_UPPERBOUND:
                beta = min(beta, tt_score)
            if alpha >= beta:
                return tt_score

        def store_quiescence_score(score):
            if len(self.qtt) >= TT_MAX_ENTRIES:
                self.qtt.clear()
            if score <= original_alpha:
                tt_flag = TT_UPPERBOUND
            elif score >= original_beta:
                tt_flag = TT_LOWERBOUND
            else:
                tt_flag = TT_EXACT
            self.qtt[position_key] = (depth, tt_flag, score)
            return score

        color = 'black' if maximizing else 'white'
        in_check = self.is_in_check(color, board)

        if depth <= 0:
            if in_check:
                moves = self.get_all_moves(board, maximizing, en_passant_target, castling_rights)
                if not moves:
                    return store_quiescence_score(-MATE_SCORE if maximizing else MATE_SCORE)
            return store_quiescence_score(self.eval(board))

        if in_check:
            moves = self.get_all_moves(board, maximizing, en_passant_target, castling_rights)
            if not moves:
                return store_quiescence_score(-MATE_SCORE if maximizing else MATE_SCORE)
        else:
            stand_pat = self.eval(board)
            if maximizing:
                if stand_pat >= beta:
                    return store_quiescence_score(stand_pat)
                alpha = max(alpha, stand_pat)
            else:
                if stand_pat <= alpha:
                    return store_quiescence_score(stand_pat)
                beta = min(beta, stand_pat)

            moves = [
                move for move in self.get_all_moves(board, maximizing, en_passant_target, castling_rights)
                if self.is_tactical_move(board, move, en_passant_target)
            ]
            if not moves:
                return store_quiescence_score(stand_pat)

        moves.sort(key=lambda move: self.score_move(board, move, en_passant_target), reverse=True)

        if maximizing:
            best = float('-inf') if in_check else stand_pat
            for move in moves:
                next_board, next_en_passant, next_castling = self.apply_move_to_copy(
                    board,
                    move,
                    en_passant_target,
                    castling_rights,
                )
                score = self.quiescence(
                    next_board,
                    alpha,
                    beta,
                    False,
                    next_en_passant,
                    next_castling,
                    depth - 1,
                )
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return store_quiescence_score(best)

        best = float('inf') if in_check else stand_pat
        for move in moves:
            next_board, next_en_passant, next_castling = self.apply_move_to_copy(
                board,
                move,
                en_passant_target,
                castling_rights,
            )
            score = self.quiescence(
                next_board,
                alpha,
                beta,
                True,
                next_en_passant,
                next_castling,
                depth - 1,
            )
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return store_quiescence_score(best)

    def is_tactical_move(self, board, move, en_passant_target=None):
        start, end, promotion_choice = normalize_move(move)
        moving_piece = board[start[0]][start[1]]
        captured_piece = board[end[0]][end[1]]

        return (
            captured_piece != 0
            or promotion_choice is not None
            or (
                moving_piece in (1, 7)
                and en_passant_target == end
                and start[1] != end[1]
            )
        )

    def score_move(self, board, move, en_passant_target=None):
        start, end, promotion_choice = normalize_move(move)
        moving_piece = board[start[0]][start[1]]
        captured_piece = board[end[0]][end[1]]
        score = 0

        if (
            moving_piece in (1, 7)
            and en_passant_target == end
            and start[1] != end[1]
            and captured_piece == 0
        ):
            captured_piece = 7 if moving_piece == 1 else 1

        if captured_piece != 0:
            score += 10 * get_material_value(captured_piece)
            score -= get_material_value(moving_piece)

        if promotion_choice == "queen":
            score += get_material_value(5)
        elif promotion_choice == "knight":
            score += get_material_value(2)

        if end in ((3, 3), (3, 4), (4, 3), (4, 4)):
            score += 10
        
        return score

    def get_best_move(self, depth=AI_DEPTH, time_limit=SEARCH_TIME_LIMIT_SECONDS):
        best_move = None
        best_score = float('-inf')
        moves = self.get_all_moves(self.board, True, self.en_passant_target, self.castling_rights)
        moves.sort(key=lambda move: self.score_move(self.board, move, self.en_passant_target), reverse=True)

        self.search_deadline = time.monotonic() + time_limit if time_limit is not None else None
        try:
            for move in moves:
                if self.search_deadline is not None and time.monotonic() >= self.search_deadline:
                    break

                board_after_move, en_passant_after_move, castling_after_move = self.apply_move_to_copy(
                    self.board,
                    move,
                    self.en_passant_target,
                    self.castling_rights,
                )
                score = self.minimax(
                    board_after_move,
                    depth - 1,
                    float('-inf'),
                    float('inf'),
                    False,
                    en_passant_after_move,
                    castling_after_move,
                )
                if score > best_score:
                    best_score = score
                    best_move = move
        except TimeoutError:
            pass
        finally:
            self.search_deadline = None

        return best_move

    def is_promotion_move(self, start, end):
        moving_piece = self.get_piece(start, self.board)
        return (moving_piece == 1 and end[0] == 0) or (moving_piece == 7 and end[0] == 7)

    def move_piece(self,i,f,promotion_choice="queen"):
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

        self.board[f[0]][f[1]] = promote_piece_if_needed(moving_piece, f[0], promotion_choice)
        self.board[i[0]][i[1]] = 0

        self.update_castling_rights(i, f, moving_piece, captured_piece)

        if moving_piece in (1, 7) and abs(f[0] - i[0]) == 2:
            self.en_passant_target = ((i[0] + f[0]) // 2, i[1])
        else:
            self.en_passant_target = None

    def update_castling_rights(self, start, end, moving_piece, captured_piece):
        self.update_castling_rights_for(
            self.castling_rights,
            start,
            end,
            moving_piece,
            captured_piece,
        )

    def update_castling_rights_for(self, castling_rights, start, end, moving_piece, captured_piece):
        if moving_piece == 6:
            castling_rights['white']['king_side'] = False
            castling_rights['white']['queen_side'] = False
        elif moving_piece == 12:
            castling_rights['black']['king_side'] = False
            castling_rights['black']['queen_side'] = False
        elif moving_piece == 4:
            if start == (7, 0):
                castling_rights['white']['queen_side'] = False
            elif start == (7, 7):
                castling_rights['white']['king_side'] = False
        elif moving_piece == 10:
            if start == (0, 0):
                castling_rights['black']['queen_side'] = False
            elif start == (0, 7):
                castling_rights['black']['king_side'] = False

        if captured_piece == 4:
            if end == (7, 0):
                castling_rights['white']['queen_side'] = False
            elif end == (7, 7):
                castling_rights['white']['king_side'] = False
        elif captured_piece == 10:
            if end == (0, 0):
                castling_rights['black']['queen_side'] = False
            elif end == (0, 7):
                castling_rights['black']['king_side'] = False

    def can_castle(self, color, side, board, castling_rights=None):
        castling_rights = self.castling_rights if castling_rights is None else castling_rights
        row = 7 if color == 'white' else 0
        king_piece = 6 if color == 'white' else 12
        rook_piece = 4 if color == 'white' else 10

        if not castling_rights[color][side]:
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
    def get_legal_moves(
        self,
        cell,
        board,
        validate_check=True,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
    ):
        if en_passant_target is USE_BOARD_STATE:
            en_passant_target = self.en_passant_target
        castling_rights = self.castling_rights if castling_rights is None else castling_rights
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
                    if en_passant_target == (capture_row, capture_col):
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
                if self.can_castle(color, 'king_side', board, castling_rights):
                    legal_moves.append((cell[0], 6))
                if self.can_castle(color, 'queen_side', board, castling_rights):
                    legal_moves.append((cell[0], 2))
        if validate_check:
            color = 'white' if piece <= 6 else 'black'
            filtered_moves = []
            for move in legal_moves:
                target_piece = board[move[0]][move[1]]
                if target_piece in (6, 12):
                    continue

                temp_board = self.move_on_copy(
                    board,
                    (cell, move),
                    en_passant_target,
                    castling_rights,
                )
                if not self.is_in_check(color, temp_board):
                    filtered_moves.append(move)
            legal_moves = filtered_moves

        return legal_moves
            
def calculate_ai_move(board_state, en_passant_target, castling_rights):
    worker_board = Board(None)
    worker_board.board = [row[:] for row in board_state]
    worker_board.en_passant_target = en_passant_target
    worker_board.castling_rights = copy.deepcopy(castling_rights)
    return worker_board.get_best_move()
