"""Klavs's Blackjack bot and card-counting strategy."""

from collections import Counter
from collections.abc import Iterable
from math import sqrt
from typing import NamedTuple

BOT_NAME = "klavs_bot"

_SUITS = frozenset({"H", "D", "C", "S"})
_RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 11,
}


def card_value(card: str) -> int:
    """Return a card's Blackjack value, counting an ace as 11."""
    if not isinstance(card, str) or len(card) not in (2, 3):
        raise ValueError(f"Invalid card: {card!r}")

    rank, suit = card[:-1], card[-1]
    if rank not in _RANK_VALUES or suit not in _SUITS:
        raise ValueError(f"Invalid card: {card!r}")
    return _RANK_VALUES[rank]


def hand_value(cards: Iterable[str]) -> int:
    """Return the best hand total not exceeding 21, or the bust total."""
    total = 0
    aces = 0
    for card in cards:
        total += card_value(card)
        if card[:-1] == "A":
            aces += 1

    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


class BetInsight(NamedTuple):
    amount: int
    running_count: int
    true_count: float
    reason: str


class DecisionInsight(NamedTuple):
    action: str
    running_count: int
    true_count: float
    reason: str


def _hi_lo_value(card: str) -> int:
    rank = card[:-1]
    if rank in {"2", "3", "4", "5", "6"}:
        return 1
    if rank in {"T", "J", "Q", "K", "A"}:
        return -1
    return 0


def running_count(history: Iterable[str]) -> int:
    """Return the Hi-Lo running count for the publicly seen cards."""
    return sum(_hi_lo_value(card) for card in history)


def audit_public_shoe(history: list[str]) -> str:
    """Flag impossible cards or extreme rank-frequency deviations in a shoe."""
    for card in history:
        if (
            not isinstance(card, str)
            or len(card) not in (2, 3)
            or card[:-1] not in _RANK_VALUES
            or card[-1] not in _SUITS
        ):
            return f"ALERT: invalid card in public history: {card!r}."

    if len(history) > 208:
        return "ALERT: public history exceeds one four-deck shoe."

    card_counts = Counter(history)
    repeated_card = next(
        ((card, count) for card, count in card_counts.items() if count > 4),
        None,
    )
    if repeated_card:
        card, count = repeated_card
        return f"ALERT: {card} appeared {count} times; a four-deck shoe has 4."

    seen = len(history)
    if seen < 52:
        return f"COLLECTING: {seen}/52 public cards seen."

    if seen == 208:
        return "OK: complete four-deck shoe composition."

    probability = 1 / 13
    expected = seen * probability
    variance = (
        seen
        * probability
        * (1 - probability)
        * (208 - seen)
        / 207
    )
    standard_deviation = sqrt(variance)
    rank_counts = Counter(card[:-1] for card in history)
    rank, z_score = max(
        (
            (rank, abs(rank_counts[rank] - expected) / standard_deviation)
            for rank in _RANK_VALUES
        ),
        key=lambda item: item[1],
    )
    if z_score >= 4.0:
        return (
            f"CHECK: {rank} frequency is unusual "
            f"({rank_counts[rank]} vs {expected:.1f} expected, "
            f"{z_score:.1f}σ); this is not proof of manipulation."
        )
    return f"OK: {seen} public cards; no extreme rank imbalance."


def is_early_shuffle(cards_remaining: int) -> bool:
    """Return whether a four-deck shoe was shuffled before 75% was dealt."""
    if not 0 <= cards_remaining <= 208:
        return True
    return 208 - cards_remaining < 156


def estimate_true_count(
    history: Iterable[str],
    decks_remaining: float | None = None,
) -> float:
    """Estimate Hi-Lo true count; action callbacks do not supply deck count."""
    seen_cards = list(history)
    if decks_remaining is None:
        decks_remaining = max(0.25, 4.0 - len(seen_cards) / 52.0)
    else:
        decks_remaining = max(0.25, decks_remaining)
    return running_count(seen_cards) / decks_remaining


def analyze_bet(
    bankroll: int,
    history: list[str],
    decks_remaining: float,
) -> BetInsight:
    running = running_count(history)
    true = estimate_true_count(history, decks_remaining)
    bankroll_limit = max(10, min(200, (bankroll // 100) * 10))
    if true < 0.5:
        units = 1
    elif true < 1.0:
        units = 2
    elif true < 1.5:
        units = 3
    elif true < 2.0:
        units = 5
    elif true < 2.5:
        units = 7
    elif true < 3.0:
        units = 10
    elif true < 4.0:
        units = 15
    else:
        units = 20
    shoe_audit = audit_public_shoe(history)
    if shoe_audit.startswith(("CHECK:", "ALERT:")):
        units = 1
    amount = min(bankroll_limit, units * 10)
    reason = (
        f"Hi-Lo running count {running:+d}, true count {true:+.1f}; "
        f"betting {amount} chips ({amount // 10} units, "
        f"bankroll cap {bankroll_limit})."
    )
    if shoe_audit.startswith(("CHECK:", "ALERT:")):
        reason += f" Public shoe audit: {shoe_audit} Bet reduced to minimum."
    return BetInsight(amount, running, true, reason)


def place_bet(
    bankroll: int,
    history: list[str],
    decks_remaining: float,
) -> int:
    """Choose a 10–200 chip wager, increasing it when the count is favorable."""
    return analyze_bet(bankroll, history, decks_remaining).amount


def _hand_score(cards: list[str]) -> tuple[int, bool]:
    total = sum(card_value(card) for card in cards)
    aces = sum(card[:-1] == "A" for card in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, aces > 0


def _pair_action(pair_value: int, dealer_value: int) -> str | None:
    if pair_value in (8, 11):
        return "SPLIT"
    if pair_value == 9 and (
        2 <= dealer_value <= 6 or dealer_value in (8, 9)
    ):
        return "SPLIT"
    if pair_value == 7 and 2 <= dealer_value <= 7:
        return "SPLIT"
    if pair_value == 6 and 2 <= dealer_value <= 6:
        return "SPLIT"
    if pair_value == 4 and dealer_value in (5, 6):
        return "SPLIT"
    if pair_value in (2, 3) and 2 <= dealer_value <= 7:
        return "SPLIT"
    return None


def analyze_decision(
    hand: list[str],
    dealer_upcard: str,
    history: list[str],
    can_double: bool,
    can_split: bool,
) -> DecisionInsight:
    if not hand:
        raise ValueError("The hand must contain at least one card.")

    running = running_count(history)
    true = estimate_true_count(history)
    dealer_value = card_value(dealer_upcard)
    total, soft = _hand_score(hand)
    count_note = f"Hi-Lo count {running:+d} / true {true:+.1f}."
    shoe_audit = audit_public_shoe(history)
    suspicious_shoe = shoe_audit.startswith(("CHECK:", "ALERT:"))

    if total >= 21:
        return DecisionInsight("STAND", running, true, f"Total is {total}. {count_note}")

    if (
        not suspicious_shoe
        and can_split
        and len(hand) == 2
        and card_value(hand[0]) == card_value(hand[1])
    ):
        split_action = _pair_action(card_value(hand[0]), dealer_value)
        if split_action == "SPLIT":
            return DecisionInsight(
                "SPLIT",
                running,
                true,
                f"Pair value {card_value(hand[0])} follows pair-splitting strategy. "
                f"{count_note}",
            )

    if can_double and not suspicious_shoe:
        if not soft and (
            (total == 9 and 3 <= dealer_value <= 6)
            or (total == 10 and 2 <= dealer_value <= 9)
            or (total == 11 and dealer_value != 11)
        ):
            return DecisionInsight(
                "DOUBLE",
                running,
                true,
                f"Hard {total} is a favorable double against dealer {dealer_value}. "
                f"{count_note}",
            )
        if soft and (
            (total in (13, 14) and dealer_value in (5, 6))
            or (total in (15, 16) and 4 <= dealer_value <= 6)
            or (total == 17 and 3 <= dealer_value <= 6)
            or (total == 18 and 2 <= dealer_value <= 6)
        ):
            return DecisionInsight(
                "DOUBLE",
                running,
                true,
                f"Soft {total} is a favorable double against dealer {dealer_value}. "
                f"{count_note}",
            )

    if not soft:
        if not suspicious_shoe and total == 16 and dealer_value == 10 and true >= 0:
            return DecisionInsight(
                "STAND", running, true,
                f"Hi-Lo deviation: stand on hard 16 vs T at true count {true:+.1f}.",
            )
        if not suspicious_shoe and total == 15 and dealer_value == 10 and true >= 4:
            return DecisionInsight(
                "STAND", running, true,
                f"Hi-Lo deviation: stand on hard 15 vs T at true count {true:+.1f}.",
            )
        if not suspicious_shoe and total == 12 and dealer_value == 3 and true >= 2:
            return DecisionInsight(
                "STAND", running, true,
                f"Hi-Lo deviation: stand on hard 12 vs 3 at true count {true:+.1f}.",
            )
        if not suspicious_shoe and total == 12 and dealer_value == 2 and true >= 3:
            return DecisionInsight(
                "STAND", running, true,
                f"Hi-Lo deviation: stand on hard 12 vs 2 at true count {true:+.1f}.",
            )
        if total <= 11:
            action = "HIT"
        elif total == 12:
            action = "STAND" if 4 <= dealer_value <= 6 else "HIT"
        elif total <= 16:
            action = "STAND" if 2 <= dealer_value <= 6 else "HIT"
        else:
            action = "STAND"
    elif total <= 17:
        action = "HIT"
    elif total == 18:
        action = "STAND" if dealer_value in (2, 7, 8) else "HIT"
    else:
        action = "STAND"

    hand_type = "Soft" if soft else "Hard"
    reason = (
        f"{hand_type} {total} vs dealer {dealer_value}: basic strategy says "
        f"{action.lower()}. {count_note}"
    )
    if suspicious_shoe:
        reason += f" Public shoe audit: {shoe_audit} Using conservative action."
    return DecisionInsight(action, running, true, reason)


def decide_action(
    hand: list[str],
    dealer_upcard: str,
    history: list[str],
    can_double: bool,
    can_split: bool,
) -> str:
    """Return one of the official tournament actions."""
    return analyze_decision(
        hand, dealer_upcard, history, can_double, can_split
    ).action


if __name__ == "__main__":
    assert card_value("AS") == 11
    assert card_value("TH") == 10
    assert hand_value(["AS", "7D"]) == 18
    assert hand_value(["AS", "AH", "9C"]) == 21
    assert running_count(["2H", "6D", "9C", "TS", "AH"]) == 0
    assert decide_action(["8S", "8D"], "6C", [], False, True) == "SPLIT"
    assert decide_action(["5S", "6D"], "9C", [], True, False) == "DOUBLE"
