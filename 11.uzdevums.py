"""Pārbauda Tic-Tac-Toe botu un tā atbilstību spēles prasībām."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType

BOARD_SIZE = 15
EMPTY = "_"
BOT_RELATIVE_PATH = Path(
    "tic-tac-toe",
    "studenti",
    "klavs_barons-kaupa",
    "bot.py",
)


def load_bot() -> ModuleType:
    """Atrod un ielādē bota moduli no projekta mapes."""
    project_dir = Path(__file__).resolve().parent
    candidates = (project_dir / BOT_RELATIVE_PATH, project_dir / "ai" / BOT_RELATIVE_PATH)
    bot_path = next((path for path in candidates if path.is_file()), None)
    if bot_path is None:
        checked_paths = "\n".join(str(path) for path in candidates)
        raise FileNotFoundError(f"Botu neatradu. Pārbaudītās vietas:\n{checked_paths}")

    spec = importlib.util.spec_from_file_location("student_bot", bot_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Neizdevās ielādēt botu no {bot_path}")

    bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot)
    return bot


def make_board() -> list[list[str]]:
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def test_opening_and_legal_moves(bot: ModuleType) -> None:
    board = make_board()
    before = [row[:] for row in board]
    move = bot.get_move(board, "X")
    assert move == (7, 7), f"First move should be in the center, got {move}"
    assert board == before, "get_move changed the supplied board"
    assert 0 <= move[0] < BOARD_SIZE and 0 <= move[1] < BOARD_SIZE


def test_win_and_block(bot: ModuleType) -> None:
    board = make_board()
    for col in range(5, 9):
        board[7][col] = "X"
    before = [row[:] for row in board]
    assert bot.get_move(board, "X") in ((7, 4), (7, 9))
    assert board == before, "Winning-move search changed the supplied board"

    board = make_board()
    for col in range(4, 8):
        board[7][col] = "O"
    assert bot.get_move(board, "X") in ((7, 3), (7, 8))


def test_swap2(bot: ModuleType) -> None:
    board = make_board()
    opening = bot.swap2_propose(board)
    assert len(opening) == 3, "Opening must contain exactly three moves"
    assert sum(symbol == "X" for _, _, symbol in opening) == 2
    assert sum(symbol == "O" for _, _, symbol in opening) == 1
    assert len({(row, col) for row, col, _ in opening}) == 3

    for row, col, symbol in opening:
        assert 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE
        assert board[row][col] == EMPTY
        board[row][col] = symbol

    response = bot.swap2_respond(board)
    assert response["action"] in ("TAKE_X", "TAKE_O", "PLACE_TWO")
    if response["action"] == "PLACE_TWO":
        moves = response["moves"]
        assert len(moves) == 2
        assert {symbol for _, _, symbol in moves} == {"X", "O"}
        assert len({(row, col) for row, col, _ in moves}) == 2
        for row, col, _ in moves:
            assert 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE
            assert board[row][col] == EMPTY

    choice_board = make_board()
    for row, col, symbol in opening:
        choice_board[row][col] = symbol
    choice_board[6][7] = "X"
    choice_board[8][7] = "O"
    assert bot.swap2_final_choice(choice_board) in ("X", "O")


def test_time_limit(bot: ModuleType) -> float:
    board = make_board()
    for row in range(0, BOARD_SIZE, 2):
        for col in range(0, BOARD_SIZE, 2):
            board[row][col] = "X" if (row + col) % 4 == 0 else "O"

    start = time.perf_counter()
    move = bot.get_move(board, "X")
    elapsed = time.perf_counter() - start

    assert board[move[0]][move[1]] == EMPTY, "Bot chose an occupied square"
    assert elapsed < 1.0, f"Move took {elapsed:.3f}s (limit is 1.0s)"
    return elapsed


def print_board(board: list[list[str]]) -> None:
    print("    " + " ".join(f"{col:2}" for col in range(BOARD_SIZE)))
    for row_index, row in enumerate(board):
        cells = " ".join("." if cell == EMPTY else cell for cell in row)
        print(f"{row_index:2}  {cells}")


def ask_human_move(
    board: list[list[str]], player: str
) -> tuple[int, int] | None:
    while True:
        answer = input(
            f"Your move as {player} (row col, 0-14; q quits): "
        ).strip().lower()
        if answer in ("q", "quit"):
            return None

        parts = answer.split()
        if len(parts) != 2:
            print("Enter two numbers, for example: 7 8")
            continue
        try:
            row, col = map(int, parts)
        except ValueError:
            print("Coordinates must be whole numbers.")
            continue
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            print("Coordinates must be from 0 to 14.")
            continue
        if board[row][col] != EMPTY:
            print("That square is occupied.")
            continue
        return row, col


def ask_human_color() -> str | None:
    while True:
        answer = input("Choose your color (X or O; q quits): ").strip().upper()
        if answer in ("Q", "QUIT"):
            return None
        if answer in ("X", "O"):
            return answer
        print("Enter X or O.")


def place_stone(
    board: list[list[str]], row: int, col: int, symbol: str
) -> None:
    if symbol not in ("X", "O"):
        raise ValueError(f"Invalid symbol returned by bot: {symbol!r}")
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        raise ValueError(f"Bot returned an out-of-range move: {(row, col)!r}")
    if board[row][col] != EMPTY:
        raise ValueError(f"Bot returned an occupied square: {(row, col)!r}")
    board[row][col] = symbol


def apply_bot_opening(
    board: list[list[str]], moves: list[tuple[int, int, str]], expected: int
) -> None:
    if len(moves) != expected:
        raise ValueError(f"Bot must return exactly {expected} opening moves")
    seen: set[tuple[int, int]] = set()
    for row, col, symbol in moves:
        if (row, col) in seen:
            raise ValueError("Bot returned duplicate opening coordinates")
        place_stone(board, row, col, symbol)
        seen.add((row, col))


def winner_after(
    board: list[list[str]], row: int, col: int, player: str
) -> bool:
    directions = ((1, 0), (0, 1), (1, 1), (1, -1))
    for dr, dc in directions:
        count = 1
        for sign in (-1, 1):
            rr, cc = row + sign * dr, col + sign * dc
            while (
                0 <= rr < BOARD_SIZE
                and 0 <= cc < BOARD_SIZE
                and board[rr][cc] == player
            ):
                count += 1
                rr += sign * dr
                cc += sign * dc
        if count >= 5:
            return True
    return False


def setup_human_first(
    board: list[list[str]], bot: ModuleType
) -> tuple[str, str] | None:
    print("You are Player 1. Place two X stones and one O stone.")
    for symbol in ("X", "X", "O"):
        move = ask_human_move(board, symbol)
        if move is None:
            return None
        place_stone(board, move[0], move[1], symbol)
        print_board(board)

    response = bot.swap2_respond(board)
    action = response.get("action")
    print(f"Bot chose {action}.")
    if action in ("TAKE_X", "TAKE_O"):
        bot_color = action[-1]
        human_color = "O" if bot_color == "X" else "X"
        return human_color, "O"
    if action != "PLACE_TWO":
        raise ValueError(f"Bot returned an invalid Swap2 action: {action!r}")

    apply_bot_opening(board, response["moves"], 2)
    print_board(board)
    human_color = ask_human_color()
    if human_color is None:
        return None
    return human_color, "X"


def setup_bot_first(
    board: list[list[str]], bot: ModuleType
) -> tuple[str, str] | None:
    opening = bot.swap2_propose(board)
    apply_bot_opening(board, opening, 3)
    print("Bot placed its opening stones:")
    print_board(board)

    while True:
        action = input("Choose TAKE_X, TAKE_O, or PLACE_TWO: ").strip().upper()
        if action in ("TAKE_X", "TAKE_O"):
            human_color = action[-1]
            return human_color, "O"
        if action == "PLACE_TWO":
            break
        print("Enter TAKE_X, TAKE_O, or PLACE_TWO.")

    print("Place one X stone and one O stone.")
    for symbol in ("X", "O"):
        move = ask_human_move(board, symbol)
        if move is None:
            return None
        place_stone(board, move[0], move[1], symbol)
        print_board(board)

    bot_color = bot.swap2_final_choice(board)
    if bot_color not in ("X", "O"):
        raise ValueError(f"Bot returned an invalid color: {bot_color!r}")
    human_color = "O" if bot_color == "X" else "X"
    print(f"Bot chose {bot_color}; you play {human_color}.")
    return human_color, "X"


def play_game(bot: ModuleType) -> None:
    board = make_board()
    while True:
        first = input("Who makes the Swap2 opening? 1=you, 2=bot [1]: ").strip()
        if first in ("", "1", "2"):
            break
        print("Enter 1 or 2.")

    setup = (
        setup_human_first(board, bot)
        if first in ("", "1")
        else setup_bot_first(board, bot)
    )
    if setup is None:
        print("Game cancelled.")
        return

    human_color, current_symbol = setup
    bot_color = "O" if human_color == "X" else "X"
    print(f"You play {human_color}; bot plays {bot_color}. Five in a row wins.")

    while True:
        print_board(board)
        if current_symbol == human_color:
            move = ask_human_move(board, current_symbol)
            if move is None:
                print("Game cancelled.")
                return
        else:
            move = bot.get_move(board, current_symbol)
            if (
                not isinstance(move, tuple)
                or len(move) != 2
                or not all(isinstance(value, int) for value in move)
            ):
                raise ValueError(f"Bot returned an invalid move: {move!r}")
            if not (0 <= move[0] < BOARD_SIZE and 0 <= move[1] < BOARD_SIZE):
                raise ValueError(f"Bot returned an out-of-range move: {move!r}")
            if board[move[0]][move[1]] != EMPTY:
                raise ValueError(f"Bot returned an occupied square: {move!r}")
            print(f"Bot plays {move[0]} {move[1]} as {current_symbol}.")

        row, col = move
        place_stone(board, row, col, current_symbol)
        if winner_after(board, row, col, current_symbol):
            print_board(board)
            winner = "You win!" if current_symbol == human_color else "Bot wins."
            print(winner)
            return
        if all(cell != EMPTY for line in board for cell in line):
            print_board(board)
            print("Draw.")
            return
        current_symbol = "O" if current_symbol == "X" else "X"


def main() -> None:
    bot = load_bot()
    if "--test" in sys.argv:
        test_opening_and_legal_moves(bot)
        test_win_and_block(bot)
        test_swap2(bot)
        elapsed = test_time_limit(bot)
        print(f"All checks passed. Move time: {elapsed:.3f}s / 1.000s.")
        return
    play_game(bot)


if __name__ == "__main__":
    main()
