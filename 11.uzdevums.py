"""Pārbauda Tic-Tac-Toe botu un tā atbilstību spēles prasībām."""

from __future__ import annotations

import importlib.util
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


def main() -> None:
    bot = load_bot()
    test_opening_and_legal_moves(bot)
    test_win_and_block(bot)
    test_swap2(bot)
    elapsed = test_time_limit(bot)
    print(f"All checks passed. Move time: {elapsed:.3f}s / 1.000s.")


if __name__ == "__main__":
    main()
