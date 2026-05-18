from engine import AI_DEPTH, Board


PIECE_TO_INT = {
    "P": 1,
    "N": 2,
    "B": 3,
    "R": 4,
    "Q": 5,
    "K": 6,
    "p": 7,
    "n": 8,
    "b": 9,
    "r": 10,
    "q": 11,
    "k": 12,
}

PROMO_CHAR_TO_NAME = {
    "q": "queen",
    "r": "rook",
    "b": "bishop",
    "n": "knight",
}

PROMO_NAME_TO_CHAR = {
    "queen": "q",
    "rook": "r",
    "bishop": "b",
    "knight": "n",
}


class UCIEngine:
    def __init__(self):
        self.board = Board()

    def out(self, text):
        print(text, flush=True)

    def reset(self):
        self.board = Board()

    def square_to_rc(self, square):
        col = ord(square[0]) - ord("a")
        row = 8 - int(square[1])
        return row, col

    def rc_to_square(self, rc):
        row, col = rc
        return chr(ord("a") + col) + str(8 - row)

    def uci_to_move(self, move_text):
        start = self.square_to_rc(move_text[:2])
        end = self.square_to_rc(move_text[2:4])
        if len(move_text) >= 5:
            promo = PROMO_CHAR_TO_NAME.get(move_text[4].lower(), "queen")
            return start, end, promo
        return start, end

    def move_to_uci(self, move):
        if move is None:
            return "0000"
        text = self.rc_to_square(move[0]) + self.rc_to_square(move[1])
        if len(move) >= 3 and move[2] is not None:
            text += PROMO_NAME_TO_CHAR.get(move[2], "q")
        return text

    def apply_uci_move(self, move_text):
        move = self.uci_to_move(move_text)
        start = move[0]
        end = move[1]
        promo = move[2] if len(move) >= 3 else "queen"

        legal_moves = self.board.get_all_moves(
            self.board.board,
            self.board.turn,
            self.board.en_passant_target,
            self.board.castling_rights,
        )

        if move in legal_moves:
            self.board.move_piece(start, end, promo)
            return

        for legal in legal_moves:
            if legal[0] == start and legal[1] == end:
                legal_promo = legal[2] if len(legal) >= 3 else promo
                self.board.move_piece(start, end, legal_promo)
                return

    def set_fen(self, fen):
        parts = fen.strip().split()
        if len(parts) < 4:
            return

        placement = parts[0]
        active_color = parts[1]
        castling = parts[2]
        ep_square = parts[3]

        rows = []
        for rank in placement.split("/"):
            row = []
            for char in rank:
                if char.isdigit():
                    row.extend([0] * int(char))
                else:
                    row.append(PIECE_TO_INT[char])
            if len(row) != 8:
                return
            rows.append(row)

        if len(rows) != 8:
            return

        self.board = Board()
        self.board.board = rows
        self.board.turn = active_color == "b"
        self.board.castling_rights = {
            "white": {
                "king_side": "K" in castling,
                "queen_side": "Q" in castling,
            },
            "black": {
                "king_side": "k" in castling,
                "queen_side": "q" in castling,
            },
        }
        self.board.en_passant_target = None if ep_square == "-" else self.square_to_rc(ep_square)
        self.board.result_text = None
        self.board.tt = {}
        self.board.qtt = {}
        self.board.killer_moves = {}
        self.board.history_moves = {}

    def handle_position(self, tokens):
        if len(tokens) < 2:
            return

        if tokens[1] == "startpos":
            self.reset()
            if "moves" in tokens:
                move_index = tokens.index("moves")
                for move_text in tokens[move_index + 1:]:
                    self.apply_uci_move(move_text)
            return

        if tokens[1] == "fen":
            if "moves" in tokens:
                move_index = tokens.index("moves")
                fen_tokens = tokens[2:move_index]
                move_tokens = tokens[move_index + 1:]
            else:
                fen_tokens = tokens[2:]
                move_tokens = []
            self.set_fen(" ".join(fen_tokens))
            for move_text in move_tokens:
                self.apply_uci_move(move_text)

    def parse_go(self, tokens):
        options = {}
        i = 1
        while i < len(tokens):
            key = tokens[i]
            if key in {"wtime", "btime", "winc", "binc"} and i + 1 < len(tokens):
                try:
                    options[key] = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
                continue
            i += 1
        return options

    def choose_time_limit(self, options):
        white_to_move = not self.board.turn
        remaining = options.get("wtime" if white_to_move else "btime")
        increment = options.get("winc" if white_to_move else "binc", 0)
        if remaining is None:
            return 10.0
        return max(0.05, min((remaining / 30.0 + increment * 0.75) / 1000.0, 10.0))

    def handle_go(self, tokens):
        options = self.parse_go(tokens)
        time_limit = self.choose_time_limit(options)
        def emit_info(depth, score_cp, best_move, nodes, time_ms, nps):
            pv = self.move_to_uci(best_move)
            self.out(
                f"info depth {depth} seldepth {depth} time {time_ms} nodes {nodes} nps {nps} score cp {score_cp} pv {pv}"
            )

        best_move = self.board.get_best_move(depth=AI_DEPTH, time_limit=time_limit, info_callback=emit_info)
        best_move_uci = self.move_to_uci(best_move)
        self.out(f"bestmove {best_move_uci}")

    def loop(self):
        while True:
            try:
                line = input()
            except EOFError:
                break
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            command = tokens[0]

            if command == "quit":
                break
            if command == "uci":
                self.out("id name ethantron")
                self.out("id author ethan")
                self.out("uciok")
                continue
            if command == "isready":
                self.out("readyok")
                continue
            if command == "ucinewgame":
                self.reset()
                continue
            if command == "position":
                self.handle_position(tokens)
                continue
            if command == "go":
                self.handle_go(tokens)
                continue
            if command == "stop":
                continue


def main():
    UCIEngine().loop()


if __name__ == "__main__":
    main()
