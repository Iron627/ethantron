import importlib.util
import os
import random
import time
import platform
import chess
import chess.engine
import chess.pgn

STOCKFISH_PATH = "stockfish" if platform.system() == "Linux" else "stockfish.exe"
STOCKFISH_TIME = 1.0
STOCKFISH_MULTIPV = 3
RANDOM_CP_MARGIN = 10

time_last_turn = 0.0


def load_engine_module():
    engine_path = os.path.join(os.path.dirname(__file__), "engine.py")
    spec = importlib.util.spec_from_file_location("engine_module", engine_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def engine_move_to_uci(move):
    start, end = move[:2]
    uci = chess.square_name(chess.square(start[1], 7 - start[0]))
    uci += chess.square_name(chess.square(end[1], 7 - end[0]))

    if len(move) == 3:
        promo_map = {
            "queen": "q",
            "rook": "r",
            "bishop": "b",
            "knight": "n",
        }
        uci += promo_map.get(move[2], "q")

    return uci


def apply_uci_move(engine_board, move_uci):
    start = chess.parse_square(move_uci[:2])
    end = chess.parse_square(move_uci[2:4])

    start_cell = (7 - chess.square_rank(start), chess.square_file(start))
    end_cell = (7 - chess.square_rank(end), chess.square_file(end))

    promo_map = {
        "q": "queen",
        "r": "rook",
        "b": "bishop",
        "n": "knight",
    }

    promotion = None
    if len(move_uci) == 5:
        promotion = promo_map[move_uci[4]]

    engine_board.move_piece(start_cell, end_cell, promotion)


def score_to_cp(score):
    cp = score.relative.score(mate_score=100000)
    return cp if cp is not None else 0


def get_stockfish_move(sf_engine, board):
    info = sf_engine.analyse(
        board,
        chess.engine.Limit(time=STOCKFISH_TIME),
        multipv=STOCKFISH_MULTIPV,
    )

    best_cp = score_to_cp(info[0]["score"])
    candidates = []

    for line in info:
        if "pv" not in line or not line["pv"]:
            continue

        line_cp = score_to_cp(line["score"])

        if line_cp >= best_cp - RANDOM_CP_MARGIN:
            candidates.append(line["pv"][0])

    if not candidates:
        candidates = [info[0]["pv"][0]]

    return random.choice(candidates).uci()


def main():
    global time_last_turn

    engine_module = load_engine_module()
    engine_board = engine_module.Board(None)
    chess_board = chess.Board()

    sf_engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    sf_engine.configure({
        "Threads": 8,
        "Hash": 1024,
        "Skill Level": 20,
        "UCI_LimitStrength": False,
    })

    game = chess.pgn.Game()
    game.headers["Event"] = "Local Stockfish vs My Engine"
    game.headers["White"] = "Local Stockfish"
    game.headers["Black"] = "My Engine"
    game.headers["Result"] = "*"

    node = game
    ply = 1

    try:
        while not chess_board.is_game_over():
            print("\n" + "=" * 50)
            print(f"Ply {ply}")
            print(chess_board)
            print("FEN:", chess_board.fen())
            print("=" * 50)

            if chess_board.turn == chess.WHITE:
                print("Stockfish thinking...")
                move_uci = get_stockfish_move(sf_engine, chess_board)
                print("Stockfish plays:", move_uci)

            else:
                print(f"Your engine thinking... It took {time_last_turn:.2f} seconds last turn.")
                start = time.perf_counter()

                best_move = engine_board.get_best_move()

                time_last_turn = time.perf_counter() - start

                if best_move is None:
                    print("Engine has no legal move.")
                    break

                move_uci = engine_move_to_uci(best_move)
                print("Engine plays:", move_uci)

            move = chess.Move.from_uci(move_uci)

            if move not in chess_board.legal_moves:
                print("Illegal move:", move_uci)
                print("Current FEN:", chess_board.fen())
                break

            node = node.add_variation(move)

            chess_board.push(move)
            apply_uci_move(engine_board, move_uci)

            ply += 1

    finally:
        sf_engine.quit()

    result = chess_board.result()
    game.headers["Result"] = result

    print("\nFINAL POSITION")
    print(chess_board)
    print(chess_board.fen())
    print("RESULT:", result)

    print("\nPGN:")
    print(game)


if __name__ == "__main__":
    main()