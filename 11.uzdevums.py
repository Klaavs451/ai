"""Pārbauda Tic-Tac-Toe botu un tā atbilstību spēles prasībām."""

from __future__ import annotations

from collections.abc import Callable
import importlib.util
import sys
import tkinter as tk
import time
from pathlib import Path
from tkinter import messagebox, ttk
from types import ModuleType

BOARD_SIZE = 15
EMPTY = "_"
CELL_SIZE = 40
BOARD_MARGIN = 32
BOARD_PIXELS = BOARD_MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)
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


class TicTacToeGUI:
    def __init__(self, root: tk.Tk, bot: ModuleType) -> None:
        self.root = root
        self.bot = bot
        self.board = make_board()
        self.phase = "start"
        self.human_color: str | None = None
        self.bot_color: str | None = None
        self.current_symbol = "X"
        self.opening_index = 0
        self.status = tk.StringVar(value="Izvēlies, kurš sāks. Uzvar pieci pēc kārtas.")

        root.title("Pieci pēc kārtas — spēle pret botu")
        root.minsize(1000, 700)
        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            main,
            width=BOARD_PIXELS,
            height=BOARD_PIXELS,
            background="#e5c27b",
            highlightthickness=0,
        )
        self.canvas.pack(side="left", padx=(0, 18))
        self.canvas.bind("<Button-1>", self._on_board_click)

        panel = ttk.Frame(main, width=320)
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)
        ttk.Label(
            panel,
            text=f"Pieci pēc kārtas\nPretinieks: {self.bot.BOT_NAME}",
            font=("Segoe UI", 16, "bold"),
            justify="left",
        ).pack(anchor="w", pady=(8, 14))
        ttk.Label(
            panel,
            textvariable=self.status,
            wraplength=300,
            justify="left",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 14))
        legend = ttk.Frame(panel)
        legend.pack(anchor="w", pady=(0, 12))
        ttk.Label(
            legend, text="X", foreground="#174f8a", font=("Segoe UI", 12, "bold")
        ).pack(side="left")
        ttk.Label(legend, text=" — zilais").pack(side="left")
        ttk.Label(
            legend, text="O", foreground="#a32d2d", font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(12, 0))
        ttk.Label(legend, text=" — sarkanais").pack(side="left")

        self.start_frame = ttk.LabelFrame(panel, text="Jauna spēle", padding=10)
        self.start_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(
            self.start_frame,
            text="Es sāku: lieku 2 X un 1 O",
            command=self.start_human_first,
        ).pack(fill="x", pady=3)
        ttk.Button(
            self.start_frame,
            text="Bots sāk: izvēlos X/O vai pievienoju figūras",
            command=self.start_bot_first,
        ).pack(fill="x", pady=3)

        self.action_frame = ttk.LabelFrame(panel, text="Swap2 izvēle", padding=10)
        self.action_frame.pack(fill="x", pady=(0, 10))
        ttk.Button(panel, text="Sākt no jauna", command=self.reset).pack(
            fill="x", pady=(4, 10)
        )
        ttk.Label(
            panel,
            text=(
                "Spēle ir 15 x 15 (nevis 3 x 3). Mērķis: salikt 5 vienādus "
                "simbolus horizontāli, vertikāli vai pa diagonāli.\n\n"
                "Klikšķini uz brīva līniju krustpunkta. Cipari augšā ir "
                "kolonnas, kreisajā pusē — rindas (0–14)."
            ),
            wraplength=300,
            justify="left",
        ).pack(anchor="w")
        self._clear_actions()
        self._render_board()

    def _render_board(self) -> None:
        self.canvas.delete("all")
        first = BOARD_MARGIN
        last = first + CELL_SIZE * (BOARD_SIZE - 1)
        for index in range(BOARD_SIZE):
            position = first + index * CELL_SIZE
            self.canvas.create_line(first, position, last, position, fill="#493b28")
            self.canvas.create_line(position, first, position, last, fill="#493b28")
            self.canvas.create_text(
                position, first - 17, text=str(index), fill="#30291f"
            )
            self.canvas.create_text(
                first - 17, position, text=str(index), fill="#30291f"
            )

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                symbol = self.board[row][col]
                if symbol == EMPTY:
                    continue
                x = first + col * CELL_SIZE
                y = first + row * CELL_SIZE
                if symbol == "X":
                    radius = 12
                    self.canvas.create_line(
                        x - radius,
                        y - radius,
                        x + radius,
                        y + radius,
                        fill="#174f8a",
                        width=4,
                    )
                    self.canvas.create_line(
                        x - radius,
                        y + radius,
                        x + radius,
                        y - radius,
                        fill="#174f8a",
                        width=4,
                    )
                else:
                    radius = 13
                    self.canvas.create_oval(
                        x - radius,
                        y - radius,
                        x + radius,
                        y + radius,
                        outline="#a32d2d",
                        width=4,
                    )

    def _show_actions(
        self, actions: list[tuple[str, Callable[[], None]]]
    ) -> None:
        for child in self.action_frame.winfo_children():
            child.destroy()
        if not actions:
            self.action_frame.pack_forget()
            return
        self.action_frame.pack(fill="x", pady=(0, 10))
        for label, callback in actions:
            ttk.Button(
                self.action_frame,
                text=label,
                command=callback,
            ).pack(fill="x", pady=3)

    def _clear_actions(self) -> None:
        self._show_actions([])

    def _put(self, row: int, col: int, symbol: str) -> None:
        place_stone(self.board, row, col, symbol)
        self._render_board()

    def _cell_from_click(self, event: tk.Event) -> tuple[int, int] | None:
        col = round((event.x - BOARD_MARGIN) / CELL_SIZE)
        row = round((event.y - BOARD_MARGIN) / CELL_SIZE)
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None
        x = BOARD_MARGIN + col * CELL_SIZE
        y = BOARD_MARGIN + row * CELL_SIZE
        if abs(event.x - x) > CELL_SIZE // 2 or abs(event.y - y) > CELL_SIZE // 2:
            return None
        return row, col

    def _on_board_click(self, event: tk.Event) -> None:
        cell = self._cell_from_click(event)
        if cell is None:
            return
        row, col = cell
        if self.board[row][col] != EMPTY:
            self.status.set("Šī rūtiņa jau ir aizņemta.")
            return

        if self.phase == "human_propose":
            symbol = ("X", "X", "O")[self.opening_index]
            self._put(row, col, symbol)
            self.opening_index += 1
            if self.opening_index == 3:
                self._after_human_proposal()
            else:
                next_symbol = ("X", "X", "O")[self.opening_index]
                self.status.set(
                    f"Sākuma figūra {self.opening_index + 1}/3: "
                    f"klikšķini, lai novietotu {next_symbol}."
                )
            return

        if self.phase == "human_place_two":
            symbol = ("X", "O")[self.opening_index]
            self._put(row, col, symbol)
            self.opening_index += 1
            if self.opening_index == 2:
                self._after_human_place_two()
            else:
                self.status.set("Papildu figūra 2/2: klikšķini, lai novietotu O.")
            return

        if self.phase == "play" and self.current_symbol == self.human_color:
            self._put(row, col, self.current_symbol)
            self._finish_move(row, col, self.current_symbol)

    def start_human_first(self) -> None:
        self.reset(keep_start_buttons=False)
        self.phase = "human_propose"
        self.status.set("Sākuma figūra 1/3: klikšķini, lai novietotu pirmo X.")
        self.start_frame.pack_forget()

    def start_bot_first(self) -> None:
        self.reset(keep_start_buttons=False)
        opening = self.bot.swap2_propose(self.board)
        apply_bot_opening(self.board, opening, 3)
        if sum(symbol == "X" for _, _, symbol in opening) != 2 or sum(
            symbol == "O" for _, _, symbol in opening
        ) != 1:
            raise ValueError("Bot opening must contain two X stones and one O stone")
        self._render_board()
        self.phase = "human_take_action"
        self.status.set(
            "Bots nolika 2 X un 1 O. Izvēlies X/O vai pievieno vēl X un O."
        )
        self.start_frame.pack_forget()
        self._show_actions(
            [
                ("Ņemt X (tu spēlē X)", lambda: self._take_color("X")),
                ("Ņemt O (tu spēlē O)", lambda: self._take_color("O")),
                ("Pievienot vēl X un O", self._start_human_place_two),
            ]
        )

    def _after_human_proposal(self) -> None:
        response = self.bot.swap2_respond(self.board)
        action = response.get("action")
        if action in ("TAKE_X", "TAKE_O"):
            self._begin_game("O" if action[-1] == "X" else "X", "O")
            return
        if action != "PLACE_TWO":
            raise ValueError(f"Invalid bot Swap2 action: {action!r}")

        moves = response["moves"]
        if {symbol for _, _, symbol in moves} != {"X", "O"}:
            raise ValueError("PLACE_TWO must contain one X and one O")
        apply_bot_opening(self.board, moves, 2)
        self._render_board()
        self.phase = "human_choose_color"
        self.status.set("Bots pievienoja X un O. Izvēlies savu krāsu; bots dabūs otru.")
        self._show_actions(
            [
                ("Turpināt ar X", lambda: self._choose_human_color("X")),
                ("Turpināt ar O", lambda: self._choose_human_color("O")),
            ]
        )

    def _start_human_place_two(self) -> None:
        self.phase = "human_place_two"
        self.opening_index = 0
        self._clear_actions()
        self.status.set("Papildu figūra 1/2: klikšķini, lai novietotu X.")

    def _after_human_place_two(self) -> None:
        bot_color = self.bot.swap2_final_choice(self.board)
        if bot_color not in ("X", "O"):
            raise ValueError(f"Invalid bot color: {bot_color!r}")
        self._begin_game("O" if bot_color == "X" else "X", "X")

    def _take_color(self, color: str) -> None:
        self._begin_game(color, "O")

    def _choose_human_color(self, color: str) -> None:
        self._begin_game(color, "X")

    def _begin_game(self, human_color: str, next_symbol: str) -> None:
        self.human_color = human_color
        self.bot_color = "O" if human_color == "X" else "X"
        self.current_symbol = next_symbol
        self.phase = "play"
        self._clear_actions()
        self._advance_turn()

    def _advance_turn(self) -> None:
        if self.phase != "play":
            return
        if self.current_symbol == self.human_color:
            self.status.set(
                f"Tu: {self.human_color}; bots: {self.bot_color}. "
                f"Tavs {self.current_symbol} gājiens — klikšķini uz brīva krustpunkta."
            )
        else:
            self.status.set(
                f"Tu: {self.human_color}; bots: {self.bot_color}. "
                f"Bots domā ({self.current_symbol})..."
            )
            self.root.after(100, self._bot_move)

    def _bot_move(self) -> None:
        if self.phase != "play" or self.current_symbol == self.human_color:
            return
        move = self.bot.get_move(self.board, self.current_symbol)
        if (
            not isinstance(move, tuple)
            or len(move) != 2
            or not all(isinstance(value, int) for value in move)
        ):
            raise ValueError(f"Bot returned an invalid move: {move!r}")
        row, col = move
        self._put(row, col, self.current_symbol)
        self._finish_move(row, col, self.current_symbol)

    def _finish_move(self, row: int, col: int, symbol: str) -> None:
        if winner_after(self.board, row, col, symbol):
            self.phase = "game_over"
            result = "Tu uzvarēji!" if symbol == self.human_color else "Bots uzvarēja."
            self.status.set(result)
            messagebox.showinfo("Spēle beigusies", result, parent=self.root)
            return
        if all(cell != EMPTY for line in self.board for cell in line):
            self.phase = "game_over"
            self.status.set("Neizšķirts.")
            messagebox.showinfo("Spēle beigusies", "Neizšķirts.", parent=self.root)
            return
        self.current_symbol = "O" if symbol == "X" else "X"
        self._advance_turn()

    def reset(self, keep_start_buttons: bool = True) -> None:
        self.board = make_board()
        self.phase = "start"
        self.human_color = None
        self.bot_color = None
        self.current_symbol = "X"
        self.opening_index = 0
        self._clear_actions()
        if keep_start_buttons:
            self.start_frame.pack(fill="x", pady=(0, 10))
        self.status.set("Izvēlies, kurš sāks. Uzvar pieci pēc kārtas.")
        self._render_board()


def main() -> None:
    bot = load_bot()
    if "--test" in sys.argv:
        test_opening_and_legal_moves(bot)
        test_win_and_block(bot)
        test_swap2(bot)
        elapsed = test_time_limit(bot)
        print(f"All checks passed. Move time: {elapsed:.3f}s / 1.000s.")
        return
    if "--console" in sys.argv:
        play_game(bot)
        return
    root = tk.Tk()
    TicTacToeGUI(root, bot)
    root.mainloop()


if __name__ == "__main__":
    main()
