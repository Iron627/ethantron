import importlib.util
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import requests
import chess
import chess.pgn

API_URL = "https://chess-api.com/v1"


def load_engine_module():
    engine_path = os.path.join(os.path.dirname(__file__), "main.py")
    spec = importlib.util.spec_from_file_location("engine_module", engine_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def engine_move_to_uci(move):
    start, end = move[:2]
    uci = chess.square_name(chess.square(start[1], 7 - start[0]))
    uci += chess.square_name(chess.square(end[1], 7 - end[0]))

    if len(move) == 3:
        uci += "q" if move[2] == "queen" else "n"

    return uci


def apply_uci_move(engine_board, move_uci):
    start = chess.parse_square(move_uci[:2])
    end = chess.parse_square(move_uci[2:4])

    start_cell = (7 - chess.square_rank(start), chess.square_file(start))
    end_cell = (7 - chess.square_rank(end), chess.square_file(end))

    promotion = "queen"
    if len(move_uci) == 5 and move_uci[4] == "n":
        promotion = "knight"

    engine_board.move_piece(start_cell, end_cell, promotion)


def api_safe_fen(board):
    parts = board.fen().split()
    parts[3] = "-"
    return " ".join(parts)


def get_stockfish_move(board):
    fen = api_safe_fen(board)

    response = requests.post(
        API_URL,
        json={
            "fen": fen,
            "variants": 1,
            "depth": 12,
            "maxThinkingTime": 100,
        },
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    data = response.json()

    if data.get("type") == "error":
        raise RuntimeError(f"API rejected FEN:\n{fen}\n\nResponse:\n{data}")

    move = data.get("move") or data.get("lan")

    if not move:
        raise RuntimeError(f"No move in API response:\n{data}")

    return move


def main():
    pygame.display.init()

    engine_module = load_engine_module()
    engine_board = engine_module.Board(None)
    chess_board = chess.Board()

    game = chess.pgn.Game()
    game.headers["Event"] = "Stockfish API vs My Engine"
    game.headers["White"] = "Stockfish API"
    game.headers["Black"] = "My Engine"
    game.headers["Result"] = "*"

    node = game

    ply = 1

    while not chess_board.is_game_over():
        print("\n" + "=" * 50)
        print(f"Ply {ply}")
        print(chess_board)
        print("FEN:", chess_board.fen())
        print("=" * 50)

        if chess_board.turn == chess.WHITE:
            print("Stockfish API thinking...")
            move_uci = get_stockfish_move(chess_board)
            print("Stockfish plays:", move_uci)
        else:
            print("Your engine thinking...")
            best_move = engine_board.get_best_move()

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