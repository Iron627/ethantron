import copy
import random
import time
from dataclasses import dataclass
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
SEARCH_TIME_LIMIT_SECONDS = 10
USE_BOARD_STATE = object()
USE_DEFAULT_SEARCH_OPTION = object()
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2
TT_MAX_ENTRIES = 500000
KILLER_MOVE_PRIMARY_BONUS = 1000
KILLER_MOVE_SECONDARY_BONUS = 900
NULL_MOVE_REDUCTION = 2
NULL_MOVE_MIN_DEPTH = NULL_MOVE_REDUCTION + 1
PASSED_PAWN_BASE_BONUS = 20
PASSED_PAWN_ADVANCE_BONUS = 8
DOUBLED_PAWN_PENALTY = 18
ISOLATED_PAWN_PENALTY = 12
ROOK_OPEN_FILE_BONUS = 25
ROOK_SEMI_OPEN_FILE_BONUS = 12
ROOK_SEVENTH_RANK_BONUS = 20
KING_MISSING_SHIELD_PENALTY = 35
KING_OPEN_FILE_PENALTY = 18
KING_SEMI_OPEN_FILE_PENALTY = 9


@dataclass(frozen=True)
class SearchOptions:
    max_depth: int = AI_DEPTH
    max_time: float | None = SEARCH_TIME_LIMIT_SECONDS


def normalize_search_options(
    search_options=None,
    depth=USE_DEFAULT_SEARCH_OPTION,
    time_limit=USE_DEFAULT_SEARCH_OPTION,
):
    if isinstance(search_options, SearchOptions):
        max_depth = search_options.max_depth
        max_time = search_options.max_time
    elif search_options is None:
        max_depth = AI_DEPTH
        max_time = SEARCH_TIME_LIMIT_SECONDS
    else:
        max_depth = search_options
        if depth is not USE_DEFAULT_SEARCH_OPTION and time_limit is USE_DEFAULT_SEARCH_OPTION:
            max_time = depth
            depth = USE_DEFAULT_SEARCH_OPTION
        else:
            max_time = SEARCH_TIME_LIMIT_SECONDS

    if depth is not USE_DEFAULT_SEARCH_OPTION:
        max_depth = depth
    if time_limit is not USE_DEFAULT_SEARCH_OPTION:
        max_time = time_limit

    return SearchOptions(max(1, int(max_depth)), max_time)

_zobrist_rng = random.Random(0)
ZOBRIST_PIECE = [
    [[_zobrist_rng.getrandbits(64) for _ in range(8)] for _ in range(8)]
    for _ in range(13)
]
ZOBRIST_BLACK_TO_MOVE = _zobrist_rng.getrandbits(64)
ZOBRIST_CASTLING = [_zobrist_rng.getrandbits(64) for _ in range(16)]
ZOBRIST_EN_PASSANT_FILE = [_zobrist_rng.getrandbits(64) for _ in range(8)]



OPENING_BOOK = {
    # After 1. e4: choose e5, Sicilian, French, or Caro-Kann
    (
        "rnbqkbnr"
        "pppppppp"
        "........"
        "........"
        "....P..."
        "........"
        "PPPP.PPP"
        "RNBQKBNR",
        True,
    ): [
        (((1, 4), (3, 4)), 40),  # ...e5
        (((1, 2), (3, 2)), 30),  # ...c5 Sicilian
        (((1, 4), (2, 4)), 15),  # ...e6 French
        (((1, 2), (2, 2)), 15),  # ...c6 Caro-Kann
    ],

    # Italian Game: 1. e4 e5 2. Nf3 Nc6 3. Bc4
    (
        "r.bqkbnr"
        "pppp.ppp"
        "..n....."
        "....p..."
        "..B.P..."
        ".....N.."
        "PPPP.PPP"
        "RNBQK..R",
        True,
    ): [
        (((0, 5), (3, 2)), 70),  # ...Bc5
        (((0, 6), (2, 5)), 30),  # ...Nf6
    ],

    # Sicilian: 1. e4 c5 2. Nf3
    (
        "rnbqkbnr"
        "pp.ppppp"
        "........"
        "..p....."
        "....P..."
        ".....N.."
        "PPPP.PPP"
        "RNBQKB.R",
        True,
    ): [
        (((1, 3), (2, 3)), 45),  # ...d6
        (((0, 1), (2, 2)), 35),  # ...Nc6
        (((1, 4), (2, 4)), 20),  # ...e6
    ],

    # French: 1. e4 e6 2. d4
    (
        "rnbqkbnr"
        "pppp.ppp"
        "....p..."
        "........"
        "...PP..."
        "........"
        "PPP..PPP"
        "RNBQKBNR",
        True,
    ): [
        (((1, 3), (3, 3)), 100),  # ...d5
    ],

    # Caro-Kann: 1. e4 c6 2. d4
    (
        "rnbqkbnr"
        "pp.ppppp"
        "..p....."
        "........"
        "...PP..."
        "........"
        "PPP..PPP"
        "RNBQKBNR",
        True,
    ): [
        (((1, 3), (3, 3)), 100),  # ...d5
    ],
    # After 1. d4
    (
        "rnbqkbnr"
        "pppppppp"
        "........"
        "........"
        "...P...."
        "........"
        "PPP.PPPP"
        "RNBQKBNR",
        True,
    ): [
        (((1, 3), (3, 3)), 70),  # ...d5
        (((0, 6), (2, 5)), 30),  # ...Nf6
    ],
    # Queen's Gambit: 1. d4 d5 2. c4
    (
        "rnbqkbnr"
        "ppp.pppp"
        "........"
        "...p...."
        "..PP...."
        "........"
        "PP..PPPP"
        "RNBQKBNR",
        True,
    ): [
        (((1, 4), (2, 4)), 50),  # ...e6
        (((1, 2), (2, 2)), 30),  # ...c6
        (((3, 3), (4, 2)), 20),  # ...dxc4
    ],
    # =========================================
    # LONDON SYSTEM
    # 1.d4 d5 2.Bf4
    # =========================================

    (
        "rnbqkbnr"
        "ppp.pppp"
        "........"
        "...p...."
        "...P.B.."
        "........"
        "PPP.PPPP"
        "RN.QKBNR",
        True,
    ): [
        (((0, 6), (2, 5)), 60),  # ...Nf6
        (((1, 2), (3, 2)), 40),  # ...c5
    ],
    # =========================================
    # LONDON MAINLINE
    # 1.d4 d5 2.Bf4 Nf6 3.e3
    # =========================================

    (
        "rnbqkb.r"
        "ppp.pppp"
        ".....n.."
        "...p...."
        "...P.B.."
        "....P..."
        "PPP..PPP"
        "RN.QKBNR",
        True,
    ): [
        (((1, 4), (2, 4)), 60),  # ...e6
        (((1, 2), (3, 2)), 40),  # ...c5
    ],
}

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
        self.killer_moves = {}
        self.history_moves = {}
        self.search_deadline = None

    def is_square_attacked(self, board, row, col, attacker_color):
        if attacker_color == 'black':
            pawn_piece = 7
            knight_piece = 8
            bishop_piece = 9
            rook_piece = 10
            queen_piece = 11
            enemy_king_piece = 12
            pawn_row = row - 1
        else:
            pawn_piece = 1
            knight_piece = 2
            bishop_piece = 3
            rook_piece = 4
            queen_piece = 5
            enemy_king_piece = 6
            pawn_row = row + 1

        if 0 <= pawn_row < 8:
            for col_offset in (-1, 1):
                pawn_col = col + col_offset
                if 0 <= pawn_col < 8 and board[pawn_row][pawn_col] == pawn_piece:
                    return True

        knight_offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        for row_offset, col_offset in knight_offsets:
            target_row = row + row_offset
            target_col = col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == knight_piece:
                    return True

        king_offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for row_offset, col_offset in king_offsets:
            target_row = row + row_offset
            target_col = col + col_offset
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if board[target_row][target_col] == enemy_king_piece:
                    return True

        diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for row_dir, col_dir in diagonal_directions:
            target_row = row + row_dir
            target_col = col + col_dir
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
            target_row = row + row_dir
            target_col = col + col_dir
            while 0 <= target_row < 8 and 0 <= target_col < 8:
                piece = board[target_row][target_col]
                if piece != 0:
                    if piece in (rook_piece, queen_piece):
                        return True
                    break
                target_row += row_dir
                target_col += col_dir

        return False

    def is_in_check(self, color, board):
        king_piece = 6 if color == 'white' else 12
        king_square = self.find_king(board, king_piece)
        if king_square is None:
            return False

        attacker_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(board, king_square[0], king_square[1], attacker_color)

    def get_piece(self, i,board):
        return board[i[0]][i[1]]
    def eval(self, board=None):
        if board is None:
            board = self.board

        score = 0
        eval_table = EVAL_TABLE
        white_bishops = 0
        black_bishops = 0
        white_pawn_files = [0 for _ in range(8)]
        black_pawn_files = [0 for _ in range(8)]
        white_pawns = []
        black_pawns = []
        white_rooks = []
        black_rooks = []
        white_king_square = None
        black_king_square = None
        for row_no in range(8):
            row = board[row_no]
            for col_no in range(8):
                piece = row[col_no]
                score += eval_table[row[col_no]][row_no][col_no]
                if piece == 1:
                    white_pawn_files[col_no] += 1
                    white_pawns.append((row_no, col_no))
                elif piece == 7:
                    black_pawn_files[col_no] += 1
                    black_pawns.append((row_no, col_no))
                elif piece == 3:
                    white_bishops += 1
                elif piece == 9:
                    black_bishops += 1
                elif piece == 4:
                    white_rooks.append((row_no, col_no))
                elif piece == 10:
                    black_rooks.append((row_no, col_no))
                elif piece == 6:
                    white_king_square = (row_no, col_no)
                elif piece == 12:
                    black_king_square = (row_no, col_no)
        if white_bishops >= 2:
            score -= 30
        if black_bishops >= 2:
            score += 30
        score += self.evaluate_position_features(
            board,
            white_pawn_files,
            black_pawn_files,
            white_pawns,
            black_pawns,
            white_rooks,
            black_rooks,
            white_king_square,
            black_king_square,
        )
        return score

    def evaluate_position_features(
        self,
        board,
        white_pawn_files,
        black_pawn_files,
        white_pawns,
        black_pawns,
        white_rooks,
        black_rooks,
        white_king_square,
        black_king_square,
    ):
        score = 0
        score -= self.evaluate_pawn_features(
            white_pawns,
            white_pawn_files,
            black_pawns,
            True,
        )
        score += self.evaluate_pawn_features(
            black_pawns,
            black_pawn_files,
            white_pawns,
            False,
        )
        score -= self.evaluate_rook_activity(white_rooks, white_pawn_files, black_pawn_files, True)
        score += self.evaluate_rook_activity(black_rooks, black_pawn_files, white_pawn_files, False)
        score += self.king_safety_penalty_from_features(
            board,
            white_king_square,
            'white',
            white_pawn_files,
            black_pawn_files,
        )
        score -= self.king_safety_penalty_from_features(
            board,
            black_king_square,
            'black',
            black_pawn_files,
            white_pawn_files,
        )
        return score

    def evaluate_pawn_features(self, pawns, friendly_files, enemy_pawns, white):
        score = 0
        for file_no, pawn_count in enumerate(friendly_files):
            if pawn_count > 1:
                score -= DOUBLED_PAWN_PENALTY * (pawn_count - 1)
            if pawn_count > 0:
                has_left_neighbor = file_no > 0 and friendly_files[file_no - 1] > 0
                has_right_neighbor = file_no < 7 and friendly_files[file_no + 1] > 0
                if not has_left_neighbor and not has_right_neighbor:
                    score -= ISOLATED_PAWN_PENALTY * pawn_count

        for row, col in pawns:
            passed = True
            for enemy_row, enemy_col in enemy_pawns:
                if abs(enemy_col - col) > 1:
                    continue
                if white and enemy_row < row:
                    passed = False
                    break
                if not white and enemy_row > row:
                    passed = False
                    break
            if passed:
                advancement = 6 - row if white else row - 1
                score += PASSED_PAWN_BASE_BONUS + max(0, advancement) * PASSED_PAWN_ADVANCE_BONUS
        return score

    def evaluate_rook_activity(self, rooks, friendly_pawn_files, enemy_pawn_files, white):
        score = 0
        seventh_rank = 1 if white else 6
        for row, col in rooks:
            if friendly_pawn_files[col] == 0:
                if enemy_pawn_files[col] == 0:
                    score += ROOK_OPEN_FILE_BONUS
                else:
                    score += ROOK_SEMI_OPEN_FILE_BONUS
            if row == seventh_rank:
                score += ROOK_SEVENTH_RANK_BONUS
        return score

    def king_safety_penalty_from_features(
        self,
        board,
        king_square,
        color,
        friendly_pawn_files,
        enemy_pawn_files,
    ):
        if king_square is None:
            return 0

        king_row, king_col = king_square
        attacker_color = 'black' if color == 'white' else 'white'
        penalty = 120 if self.is_square_attacked(board, king_row, king_col, attacker_color) else 0
        friendly_pawn = 1 if color == 'white' else 7
        forward = -1 if color == 'white' else 1
        shield_row = king_row + forward

        for col in range(max(0, king_col - 1), min(8, king_col + 2)):
            if not (0 <= shield_row < 8 and board[shield_row][col] == friendly_pawn):
                penalty += KING_MISSING_SHIELD_PENALTY
            if friendly_pawn_files[col] == 0:
                if enemy_pawn_files[col] == 0:
                    penalty += KING_OPEN_FILE_PENALTY
                else:
                    penalty += KING_SEMI_OPEN_FILE_PENALTY

        return penalty

    def evaluate_king_safety(self, board):
        white_penalty = self.king_safety_penalty(board, 'white')
        black_penalty = self.king_safety_penalty(board, 'black')
        return white_penalty - black_penalty

    def king_safety_penalty(self, board, color):
        king_piece = 6 if color == 'white' else 12
        king_square = self.find_king(board, king_piece)
        if king_square is None:
            return 0

        king_row, king_col = king_square
        penalty = 120 if self.is_in_check(color, board) else 0

        friendly_pawn = 1 if color == 'white' else 7
        forward = -1 if color == 'white' else 1
        for col in range(max(0, king_col - 1), min(8, king_col + 2)):
            shield_row = king_row + forward
            if 0 <= shield_row < 8 and board[shield_row][col] == friendly_pawn:
                continue
            penalty += 35

        return penalty

    def find_king(self, board, target_piece):
        for row_no, row in enumerate(board):
            for col_no, piece in enumerate(row):
                if piece == target_piece:
                    return row_no, col_no
        return None

    def get_all_moves(self, board, black_turn, en_passant_target=USE_BOARD_STATE, castling_rights=None):
        moves = []
        king_square = self.find_king(board, 12 if black_turn else 6)
        for row_no, row in enumerate(board):
            for col_no, piece in enumerate(row):
                if black_turn and 7 <= piece <= 12:
                    start = (row_no, col_no)
                elif not black_turn and 1 <= piece <= 6:
                    start = (row_no, col_no)
                else:
                    continue

                for end in self.get_legal_moves(
                    start,
                    board,
                    True,
                    en_passant_target,
                    castling_rights,
                    king_square,
                ):
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

    def make_temporary_move_for_check(self, board, start, end, en_passant_target):
        moving_piece = board[start[0]][start[1]]
        captured_piece = board[end[0]][end[1]]
        en_passant_capture_square = None
        en_passant_captured_piece = 0
        castle_rook_move = None

        if (
            moving_piece in (1, 7)
            and en_passant_target == end
            and start[1] != end[1]
            and captured_piece == 0
        ):
            en_passant_capture_square = (start[0], end[1])
            en_passant_captured_piece = board[start[0]][end[1]]
            board[start[0]][end[1]] = 0

        if moving_piece in (6, 12) and abs(end[1] - start[1]) == 2:
            row = start[0]
            if end[1] == 6:
                castle_rook_move = ((row, 7), (row, 5), board[row][7])
                board[row][5] = board[row][7]
                board[row][7] = 0
            elif end[1] == 2:
                castle_rook_move = ((row, 0), (row, 3), board[row][0])
                board[row][3] = board[row][0]
                board[row][0] = 0

        board[end[0]][end[1]] = promote_piece_if_needed(moving_piece, end[0])
        board[start[0]][start[1]] = 0

        return (
            start,
            end,
            moving_piece,
            captured_piece,
            en_passant_capture_square,
            en_passant_captured_piece,
            castle_rook_move,
        )

    def unmake_temporary_move_for_check(self, board, undo):
        (
            start,
            end,
            moving_piece,
            captured_piece,
            en_passant_capture_square,
            en_passant_captured_piece,
            castle_rook_move,
        ) = undo

        board[start[0]][start[1]] = moving_piece
        board[end[0]][end[1]] = captured_piece

        if en_passant_capture_square is not None:
            board[en_passant_capture_square[0]][en_passant_capture_square[1]] = en_passant_captured_piece

        if castle_rook_move is not None:
            rook_start, rook_end, rook_piece = castle_rook_move
            board[rook_start[0]][rook_start[1]] = rook_piece
            board[rook_end[0]][rook_end[1]] = 0

    def minimax(
        self,
        board,
        depth,
        alpha,
        beta,
        maximizing,
        en_passant_target=USE_BOARD_STATE,
        castling_rights=None,
        ply=0,
        allow_null_move=True,
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

        color = 'black' if maximizing else 'white'
        in_check = self.is_in_check(color, board)
        if depth == 0 and in_check:
            depth = 1

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

        if self.can_try_null_move(board, maximizing, depth, in_check, allow_null_move):
            null_depth = depth - 1 - NULL_MOVE_REDUCTION
            if maximizing:
                null_score = self.minimax(
                    board,
                    null_depth,
                    beta - 1,
                    beta,
                    False,
                    None,
                    castling_rights,
                    ply + 1,
                    False,
                )
                if null_score >= beta and not self.is_mating_score(null_score):
                    return null_score
            else:
                null_score = self.minimax(
                    board,
                    null_depth,
                    alpha,
                    alpha + 1,
                    True,
                    None,
                    castling_rights,
                    ply + 1,
                    False,
                )
                if null_score <= alpha and not self.is_mating_score(null_score):
                    return null_score

        moves = self.get_all_moves(board, maximizing, en_passant_target, castling_rights)
        if not moves:
            if in_check:
                return -MATE_SCORE if maximizing else MATE_SCORE
            return 0

        moves.sort(
            key=lambda move: self.order_move_score(board, move, depth, ply, en_passant_target),
            reverse=True,
        )
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
                    ply + 1,
                )
                if score > best:
                    best = score
                    best_move = move
                alpha = max(alpha, best)
                if beta <= alpha:
                    self.record_cutoff_move(board, move, depth, ply, en_passant_target)
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
                ply + 1,
            )
            if score < best:
                best = score
                best_move = move
            beta = min(beta, best)
            if beta <= alpha:
                self.record_cutoff_move(board, move, depth, ply, en_passant_target)
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

    def is_quiet_move(self, board, move, en_passant_target=None):
        return not self.is_tactical_move(board, move, en_passant_target)

    def has_non_pawn_material(self, board, black_turn):
        material_pieces = range(8, 12) if black_turn else range(2, 6)
        for row in board:
            for piece in row:
                if piece in material_pieces:
                    return True
        return False

    def can_try_null_move(self, board, maximizing, depth, in_check, allow_null_move):
        return (
            allow_null_move
            and depth >= NULL_MOVE_MIN_DEPTH
            and not in_check
            and self.has_non_pawn_material(board, maximizing)
        )

    def is_mating_score(self, score):
        return abs(score) >= MATE_SCORE

    def history_move_key(self, board, move):
        start, end, _ = normalize_move(move)
        moving_piece = board[start[0]][start[1]]
        return moving_piece, start, end

    def record_cutoff_move(self, board, move, depth, ply, en_passant_target=None):
        if not self.is_quiet_move(board, move, en_passant_target):
            return

        killers = self.killer_moves.setdefault(ply, [])
        if move in killers:
            killers.remove(move)
        killers.insert(0, move)
        del killers[2:]

        history_key = self.history_move_key(board, move)
        self.history_moves[history_key] = self.history_moves.get(history_key, 0) + depth * depth

    def order_move_score(self, board, move, depth, ply, en_passant_target=None):
        score = self.score_move(board, move, en_passant_target)
        if not self.is_quiet_move(board, move, en_passant_target):
            return score

        killers = self.killer_moves.get(ply, ())
        if killers and move == killers[0]:
            score += KILLER_MOVE_PRIMARY_BONUS
        elif len(killers) > 1 and move == killers[1]:
            score += KILLER_MOVE_SECONDARY_BONUS

        score += self.history_moves.get(self.history_move_key(board, move), 0)
        return score

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


    def board_to_book_key(self):
        piece_map = {
            0: '.',
            1: 'P',
            2: 'N',
            3: 'B',
            4: 'R',
            5: 'Q',
            6: 'K',
            7: 'p',
            8: 'n',
            9: 'b',
            10: 'r',
            11: 'q',
            12: 'k',
        }
        chars = []
        for row in self.board:
            for piece in row:
                chars.append(piece_map[piece])
        return "".join(chars), True

    def get_book_move(self):
        entries = OPENING_BOOK.get(self.board_to_book_key())
        if entries is None:
            return None

        legal_moves = self.get_all_moves(self.board, True, self.en_passant_target, self.castling_rights)
        legal_entries = [(move, weight) for move, weight in entries if move in legal_moves]
        if not legal_entries:
            return None

        total_weight = sum(weight for _, weight in legal_entries)
        choice = random.randint(1, total_weight)
        current = 0
        for move, weight in legal_entries:
            current += weight
            if choice <= current:
                return move
        return legal_entries[-1][0]

    def get_best_move(
        self,
        search_options=None,
        depth=USE_DEFAULT_SEARCH_OPTION,
        time_limit=USE_DEFAULT_SEARCH_OPTION,
    ):
        search_options = normalize_search_options(search_options, depth, time_limit)
        book_move = self.get_book_move()
        if book_move is not None:
            return book_move

        moves = self.get_all_moves(self.board, True, self.en_passant_target, self.castling_rights)
        if not moves:
            return None

        best_move = moves[0]
        self.search_deadline = (
            time.monotonic() + search_options.max_time
            if search_options.max_time is not None
            else None
        )
        try:
            for current_depth in range(1, search_options.max_depth + 1):
                if self.search_deadline is not None and time.monotonic() >= self.search_deadline:
                    raise TimeoutError

                moves.sort(
                    key=lambda move: self.order_move_score(
                        self.board,
                        move,
                        current_depth,
                        0,
                        self.en_passant_target,
                    ),
                    reverse=True,
                )
                if best_move in moves:
                    moves.remove(best_move)
                    moves.insert(0, best_move)

                iteration_best_move = None
                iteration_best_score = float('-inf')
                for move in moves:
                    if self.search_deadline is not None and time.monotonic() >= self.search_deadline:
                        raise TimeoutError

                    board_after_move, en_passant_after_move, castling_after_move = self.apply_move_to_copy(
                        self.board,
                        move,
                        self.en_passant_target,
                        self.castling_rights,
                    )
                    score = self.minimax(
                        board_after_move,
                        current_depth - 1,
                        float('-inf'),
                        float('inf'),
                        False,
                        en_passant_after_move,
                        castling_after_move,
                        1,
                    )
                    if score > iteration_best_score:
                        iteration_best_score = score
                        iteration_best_move = move

                if iteration_best_move is not None:
                    best_move = iteration_best_move
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
        king_square=None,
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
            attacker_color = 'black' if color == 'white' else 'white'
            king_piece = 6 if color == 'white' else 12
            if piece == king_piece:
                king_square = cell
            elif king_square is None:
                king_square = self.find_king(board, king_piece)
            filtered_moves = []
            for move in legal_moves:
                target_piece = board[move[0]][move[1]]
                if target_piece in (6, 12):
                    continue

                undo = self.make_temporary_move_for_check(board, cell, move, en_passant_target)
                try:
                    checked_square = move if piece == king_piece else king_square
                    if checked_square is None or not self.is_square_attacked(
                        board,
                        checked_square[0],
                        checked_square[1],
                        attacker_color,
                    ):
                        filtered_moves.append(move)
                finally:
                    self.unmake_temporary_move_for_check(board, undo)
            legal_moves = filtered_moves

        return legal_moves
            
def calculate_ai_move(board_state, en_passant_target, castling_rights, search_options=None):
    worker_board = Board(None)
    worker_board.board = [row[:] for row in board_state]
    worker_board.en_passant_target = en_passant_target
    worker_board.castling_rights = copy.deepcopy(castling_rights)
    return worker_board.get_best_move(search_options)
