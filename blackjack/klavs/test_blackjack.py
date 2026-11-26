from __future__ import annotations

import random
import unittest
from unittest.mock import Mock

from app import BlackjackApp
from bot import (
    BOT_NAME,
    analyze_bet,
    analyze_decision,
    card_value,
    decide_action,
    estimate_true_count,
    hand_value,
    place_bet,
    running_count,
)
from game import (
    PlayerHand,
    compare_hands,
    create_shoe,
    dealer_should_hit,
    draw_card,
    is_natural,
    is_pair,
)


class BlackjackBotTests(unittest.TestCase):
    def test_bot_name_matches_assignment_name(self) -> None:
        self.assertEqual(BOT_NAME, "klavs_bot")

    def test_card_format_uses_t_for_ten(self) -> None:
        self.assertEqual(card_value("TH"), 10)
        with self.assertRaises(ValueError):
            card_value("10H")

    def test_hi_lo_count_and_true_count(self) -> None:
        history = ["2H", "6D", "9C", "TS", "AH"]
        self.assertEqual(running_count(history), 0)
        self.assertEqual(estimate_true_count(history, 2.0), 0.0)

        low_cards = [f"{rank}{suit}" for rank in "23456" for suit in "HDCS"]
        self.assertEqual(running_count(low_cards), 20)
        self.assertGreater(estimate_true_count(low_cards), 5.0)

    def test_bet_spread_increases_when_count_is_favorable(self) -> None:
        low_cards = [f"{rank}{suit}" for rank in "23456" for suit in "HDCS"]
        neutral_bet = place_bet(1000, [], 4.0)
        favorable_bet = place_bet(1000, low_cards, 3.6)
        self.assertEqual(neutral_bet, 10)
        self.assertGreater(favorable_bet, neutral_bet)
        self.assertLessEqual(favorable_bet, 200)
        self.assertLessEqual(place_bet(35, low_cards, 3.6), 35)

    def test_aggressive_bet_spread_uses_true_count_thresholds(self) -> None:
        self.assertEqual(place_bet(1000, ["TH", "AS"], 4.0), 10)
        self.assertEqual(place_bet(1000, ["2H", "3H"], 4.0), 30)
        self.assertEqual(place_bet(1000, ["2H", "3H", "4H", "5H"], 4.0), 50)

    def test_pair_splitting_and_double_decisions(self) -> None:
        self.assertEqual(decide_action(["8S", "8D"], "6C", [], False, True), "SPLIT")
        self.assertEqual(decide_action(["5S", "5D"], "6C", [], True, True), "DOUBLE")
        self.assertEqual(decide_action(["5S", "6D"], "9C", [], True, False), "DOUBLE")

    def test_hi_lo_deviation_is_explained(self) -> None:
        low_cards = [f"{rank}{suit}" for rank in "23456" for suit in "HDCS"]
        insight = analyze_bet(1000, low_cards, 3.6)
        self.assertEqual(insight.running_count, 20)
        self.assertIn("true count", insight.reason)

        decision = analyze_decision(["TS", "6D"], "TH", low_cards, False, False)
        self.assertEqual(decision.action, "STAND")
        self.assertIn("Hi-Lo deviation", decision.reason)

    def test_aces_reduce_to_one_when_hand_would_bust(self) -> None:
        self.assertEqual(hand_value(["AS", "AH", "9C"]), 21)
        self.assertEqual(hand_value(["AS", "9H", "5C"]), 15)

    def test_four_deck_shoe_contains_208_cards(self) -> None:
        shoe = create_shoe(random.Random(7))
        self.assertEqual(len(shoe), 208)
        self.assertEqual(len(set(shoe)), 52)
        self.assertTrue(all(shoe.count(card) == 4 for card in set(shoe)))

    def test_draw_removes_one_card_and_empty_shoe_fails(self) -> None:
        shoe = ["AS"]
        self.assertEqual(draw_card(shoe), "AS")
        self.assertEqual(shoe, [])
        with self.assertRaises(RuntimeError):
            draw_card(shoe)

    def test_natural_dealer_rule_and_pair_detection(self) -> None:
        self.assertTrue(is_natural(["AS", "KH"]))
        self.assertFalse(is_natural(["AS", "7H", "3C"]))
        self.assertFalse(dealer_should_hit(["AS", "6H"]))
        self.assertFalse(dealer_should_hit(["TS", "7D"]))
        self.assertTrue(is_pair(["TS", "KH"]))

    def test_hand_comparison_covers_wins_losses_pushes_and_busts(self) -> None:
        self.assertEqual(compare_hands(["TS", "8D"], ["TH", "7C"]), "win")
        self.assertEqual(compare_hands(["TS", "6D"], ["TH", "7C"]), "loss")
        self.assertEqual(compare_hands(["TS", "7D"], ["TH", "7C"]), "push")
        self.assertEqual(compare_hands(["TS", "8D", "5C"], ["TH", "7C"]), "loss")


class BlackjackAppTests(unittest.TestCase):
    def test_splitting_pair_draws_cards_and_schedules_next_bot_turn(self) -> None:
        app = BlackjackApp.__new__(BlackjackApp)
        hand = PlayerHand(["2D", "2H"], 10)
        app.player_hands = [hand]
        app.active_hand_index = 0
        app.bankroll = 990
        app.shoe = ["3C", "4D"]
        app.history = []
        app.last_action = ""
        app.last_reason = ""
        app.current_bet = 0
        app.root = Mock()
        app._set_status = Mock()
        app._record_event = Mock()
        app._refresh_analysis = Mock()
        app._render_table = Mock()
        app._display_card = lambda card: card

        app._split_active_hand(hand)

        self.assertEqual(
            [item.cards for item in app.player_hands],
            [["2D", "4D"], ["2H", "3C"]],
        )
        self.assertEqual(app.history, ["4D", "3C"])
        self.assertEqual(app.bankroll, 980)
        app.root.after.assert_called_once_with(550, app._bot_turn)


if __name__ == "__main__":
    unittest.main()
