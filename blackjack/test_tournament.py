import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from .tournament import (
    BlackjackTournament,
    BotPlayer,
    audit_public_history,
    hand_value,
    is_natural,
    make_shoe,
)


class PublicAuditTests(unittest.TestCase):
    def test_public_history_audit_checks_validity_and_rank_balance(self):
        complete_shoe = [
            f"{rank}{suit}"
            for _ in range(4)
            for suit in "HDCS"
            for rank in "23456789TJQKA"
        ]
        biased_sample = [
            f"2{suit}"
            for _ in range(4)
            for suit in "HDCS"
        ] + [
            f"{rank}{suit}"
            for rank in "3456789TJQKA"
            for suit in "HDC"
        ]

        self.assertTrue(
            audit_public_history(complete_shoe, 4).startswith("OK:")
        )
        self.assertTrue(
            audit_public_history(biased_sample, 4).startswith("CHECK:")
        )
        self.assertTrue(
            audit_public_history(["2H"] * 5, 4).startswith("ALERT:")
        )
        with self.assertRaises(ValueError):
            audit_public_history([], 0)

    def test_leaderboard_uses_survival_to_break_chip_ties(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        first_out = BotPlayer("FirstOut", None, 100)
        survivor = BotPlayer("Survivor", None, 100)
        first_out.eliminated_at = 3
        app.bots = [first_out, survivor]
        app.round_number = 6

        self.assertEqual(
            [bot.name for bot in app._ranked_bots()],
            ["Survivor", "FirstOut"],
        )

    def test_last_standing_option_finishes_when_only_one_bot_survives(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        app.bots = [
            BotPlayer("LastBot", None, 100),
            BotPlayer("EliminatedBot", None, 0),
        ]
        app.settings = {"rounds": 1000}
        app.round_number = 20
        app.last_standing_var = SimpleNamespace(get=lambda: True)

        self.assertTrue(app._tournament_complete())

        app.last_standing_var = SimpleNamespace(get=lambda: False)
        self.assertFalse(app._tournament_complete())


class HandValueTests(unittest.TestCase):
    def test_face_cards_and_t_are_worth_ten(self):
        self.assertEqual(hand_value(["TH", "JD"]), 20)

    def test_ace_changes_to_one_when_hand_would_bust(self):
        self.assertEqual(hand_value(["AH", "9D", "5C"]), 15)

    def test_multiple_aces_are_adjusted_individually(self):
        self.assertEqual(hand_value(["AS", "AD", "9H"]), 21)

    def test_split_twenty_one_is_not_a_natural(self):
        hand = ["AH", "KD"]
        self.assertTrue(is_natural(hand))
        self.assertFalse(is_natural(hand, was_split=True))

    def test_shoe_has_four_cards_of_each_rank_per_deck(self):
        shoe = make_shoe(2)
        self.assertEqual(len(shoe), 104)
        self.assertEqual(shoe.count("TH"), 2)


class RoundTests(unittest.TestCase):
    class Button:
        def configure(self, **kwargs):
            pass

    class Variable:
        def get(self):
            return True

    class Scheduler:
        def __init__(self):
            self.callbacks = []

        def after(self, _delay, callback):
            self.callbacks.append(callback)
            return str(len(self.callbacks))

        def update_idletasks(self):
            pass

    def run_round(self, draw_order, decide_action, place_bet=None, bankroll=100):
        from .tournament import BlackjackTournament

        app = BlackjackTournament.__new__(BlackjackTournament)
        bot_module = SimpleNamespace(
            place_bet=place_bet or (lambda bankroll, history, decks_remaining: 10),
            decide_action=decide_action,
        )
        app.bots = [BotPlayer("TestBot", bot_module, bankroll)]
        app.round_number = 0
        app.settings = {
            "rounds": 2,
            "decks": 1,
            "cut_percent": 75,
            "step_ms": 0,
        }
        filler = ["2S", "3S", "4S", "5S", "7S", "9S", "JS", "QS"]
        app.shoe = filler + list(reversed(draw_order))
        app.history = []
        app.dealer_hand = []
        app.dealer_hole_hidden = False
        app.phase = "ready"
        app.auto_running = False
        app.animation_after_id = None
        app.bot_action_iterator = None
        app.fast_batch_active = False
        app.auto_dealer_var = self.Variable()
        app.hit_button = self.Button()
        app.stand_button = self.Button()
        app._log = lambda line: None
        app._set_status = lambda text: None
        app._refresh_scoreboard = lambda: None
        app._draw_table = lambda: None
        app.play_next_round()
        return app.bots[0], app

    def test_gui_round_advances_bot_and_dealer_actions_as_scheduled_steps(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        bot_module = SimpleNamespace(
            place_bet=lambda bankroll, history, decks_remaining: 10,
            decide_action=lambda hand, upcard, history, can_double, can_split: "STAND",
        )
        app.bots = [BotPlayer("TestBot", bot_module, 100)]
        app.round_number = 0
        app.settings = {
            "rounds": 2,
            "decks": 1,
            "cut_percent": 75,
            "step_ms": 0,
        }
        app.shoe = ["2S", "3S", "4S", "5S", "7S", "9S", "JS", "QS"] + list(
            reversed(["TH", "6H", "8D", "TD", "2C"])
        )
        app.history = []
        app.dealer_hand = []
        app.dealer_hole_hidden = False
        app.phase = "ready"
        app.auto_running = False
        app.auto_dealer_var = self.Variable()
        app.hit_button = self.Button()
        app.stand_button = self.Button()
        app.root = self.Scheduler()
        app.animation_after_id = None
        app.bot_action_iterator = None
        app.fast_batch_active = False
        app._log = lambda line: None
        app._set_status = lambda text: None
        app._refresh_scoreboard = lambda: None
        app._draw_table = lambda: None

        app.play_next_round()

        self.assertEqual(app.phase, "players")
        self.assertEqual(len(app.root.callbacks), 1)
        while app.root.callbacks:
            app.root.callbacks.pop(0)()

        self.assertEqual(app.phase, "round_done")
        self.assertEqual(app.bots[0].bankroll, 100)

    def test_fast_mode_runs_1000_rounds_without_per_action_ui_refresh(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        bot_module = SimpleNamespace(
            place_bet=lambda bankroll, history, decks_remaining: 10,
            decide_action=lambda hand, upcard, history, can_double, can_split: "STAND",
        )
        app.bots = [BotPlayer("TestBot", bot_module, 1000000000)]
        app.round_number = 0
        app.settings = {
            "rounds": 1000,
            "decks": 1,
            "cut_percent": 75,
            "step_ms": 150,
            "batch_size": 1000,
        }
        app.shoe = make_shoe(1)
        app.history = []
        app.dealer_hand = []
        app.dealer_hole_hidden = False
        app.phase = "ready"
        app.auto_running = True
        app.after_id = None
        app.animation_after_id = None
        app.bot_action_iterator = None
        app.fast_batch_active = False
        app.shuffle_count = 0
        app.early_shuffle_count = 0
        app.dealer_rule_violations = 0
        app.fast_mode_var = self.Variable()
        app.auto_dealer_var = self.Variable()
        app.auto_button = self.Button()
        app.hit_button = self.Button()
        app.stand_button = self.Button()
        app.root = self.Scheduler()
        app._log = lambda line: None
        app._set_status = lambda text: None
        app._refresh_scoreboard = Mock()
        app._refresh_audit_status = Mock()
        app._draw_table = Mock()
        app._refresh_log = Mock()

        app._run_fast_batch()

        self.assertEqual(app.round_number, 1000)
        self.assertEqual(app.phase, "finished")
        self.assertEqual(app._draw_table.call_count, 1)
        self.assertEqual(app._refresh_scoreboard.call_count, 1)
        self.assertEqual(len(app.root.callbacks), 0)

    def test_fast_mode_stops_when_one_bot_is_left(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        bot_module = SimpleNamespace(
            place_bet=lambda bankroll, history, decks_remaining: 10,
            decide_action=lambda hand, upcard, history, can_double, can_split: "STAND",
        )
        app.bots = [
            BotPlayer("Winner", bot_module, 10),
            BotPlayer("Eliminated", bot_module, 10),
        ]
        app.round_number = 0
        app.settings = {
            "rounds": 1000,
            "decks": 1,
            "cut_percent": 75,
            "step_ms": 150,
            "batch_size": 1000,
        }
        draw_order = ["TH", "2H", "6H", "TD", "3H", "TH", "2C"]
        app.shoe = ["4S", "5S", "7S", "8S", "9S", "JS", "QS", "KS"] + list(
            reversed(draw_order)
        )
        app.history = []
        app.dealer_hand = []
        app.dealer_hole_hidden = False
        app.phase = "ready"
        app.auto_running = True
        app.after_id = None
        app.animation_after_id = None
        app.bot_action_iterator = None
        app.fast_batch_active = False
        app.shuffle_count = 0
        app.early_shuffle_count = 0
        app.dealer_rule_violations = 0
        app.fast_mode_var = self.Variable()
        app.last_standing_var = self.Variable()
        app.auto_dealer_var = self.Variable()
        app.auto_button = self.Button()
        app.hit_button = self.Button()
        app.stand_button = self.Button()
        app.root = self.Scheduler()
        app._log = lambda line: None
        app._set_status = lambda text: None
        app._refresh_scoreboard = Mock()
        app._refresh_audit_status = Mock()
        app._draw_table = Mock()
        app._refresh_log = Mock()

        app._run_fast_batch()

        self.assertEqual(app.round_number, 1)
        self.assertEqual(app.phase, "finished")
        self.assertIsNone(app.bots[0].eliminated_at)
        self.assertEqual(app.bots[1].eliminated_at, 1)
        self.assertEqual(len(app.root.callbacks), 0)

    def test_manual_dealer_stand_below_seventeen_is_audited(self):
        app = BlackjackTournament.__new__(BlackjackTournament)
        app.phase = "dealer"
        app.dealer_hand = ["6H", "TD"]
        app.dealer_rule_violations = 0
        app._log = lambda line: None
        app._refresh_audit_status = lambda: None
        settled = []
        app._settle_round = lambda: settled.append(True)

        app.dealer_stand()

        self.assertEqual(app.dealer_rule_violations, 1)
        self.assertEqual(settled, [True])

    def test_push_returns_the_original_bet(self):
        bot, app = self.run_round(
            ["TH", "6H", "8D", "TD", "2C"],
            lambda hand, upcard, history, can_double, can_split: "STAND",
        )
        self.assertEqual(bot.bankroll, 100)
        self.assertEqual(app.phase, "round_done")
        self.assertEqual(app.dealer_hand, ["6H", "TD", "2C"])

    def test_split_creates_and_plays_both_hands(self):
        def split_then_stand(hand, upcard, history, can_double, can_split):
            if can_split:
                return "SPLIT"
            return "STAND"

        bot, _ = self.run_round(
            ["8H", "6H", "8D", "TD", "3C", "4C", "2H"],
            split_then_stand,
        )
        self.assertEqual(len(bot.hands), 2)
        self.assertEqual([hand["cards"] for hand in bot.hands], [["8H", "3C"], ["8D", "4C"]])
        self.assertEqual(bot.bankroll, 80)

    def test_ten_and_face_card_can_be_split_by_value(self):
        can_split_values = []

        def stand(hand, upcard, history, can_double, can_split):
            can_split_values.append(can_split)
            return "STAND"

        bot, _ = self.run_round(["TH", "6H", "KD", "TD", "2C"], stand)
        self.assertTrue(can_split_values[0])
        self.assertEqual(bot.bankroll, 110)

    def test_natural_blackjack_pays_three_to_two(self):
        bot, _ = self.run_round(
            ["TH", "6H", "AH", "TD", "2C"],
            lambda hand, upcard, history, can_double, can_split: "STAND",
        )
        self.assertEqual(bot.bankroll, 115)

    def test_bets_are_clamped_to_the_rule_limits(self):
        draw_order = ["TH", "TD", "7D", "8S", "2C"]
        stand = lambda hand, upcard, history, can_double, can_split: "STAND"
        cases = ((1000, 1, 10), (1000, 500, 200), (80, 200, 80))
        for bankroll, requested_bet, expected_bet in cases:
            with self.subTest(bankroll=bankroll, requested_bet=requested_bet):
                bot, _ = self.run_round(
                    draw_order,
                    stand,
                    place_bet=lambda current, history, decks: requested_bet,
                    bankroll=bankroll,
                )
                self.assertEqual(bot.hands[0]["bet"], expected_bet)


if __name__ == "__main__":
    unittest.main()
