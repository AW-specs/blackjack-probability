"""
Simple Blackjack Basic-Strategy Advisor
----------------------------------------
Tells you whether to HIT, STAND, or SPLIT based on your hand
and the dealer's up-card. Not a full "double down" strategy,
just hit/stand/split logic using standard basic strategy rules.
"""

def hand_value(cards):
    """Return (total, is_soft) for a list of card values (2-10, 'A')."""
    total = 0
    aces = 0
    for c in cards:
        if c == 'A':
            aces += 1
            total += 11
        else:
            total += c
    # Downgrade aces from 11 to 1 if busting
    is_soft = aces > 0
    while total > 21 and aces:
        total -= 10
        aces -= 1
        is_soft = aces > 0
    return total, is_soft


def can_split(cards):
    return len(cards) == 2 and cards[0] == cards[1]


def advise(cards, dealer_up):
    total, soft = hand_value(cards)

    # --- Pairs (splitting) ---
    if can_split(cards):
        pair = cards[0]
        if pair == 'A' or pair == 8:
            return "SPLIT"
        if pair == 9:
            return "SPLIT" if dealer_up not in (7, 10, 'A') else "STAND"
        if pair in (2, 3, 7) and dealer_up in range(2, 8):
            return "SPLIT"
        if pair == 6 and dealer_up in range(2, 7):
            return "SPLIT"
        if pair == 4 and dealer_up in (5, 6):
            return "SPLIT"
        if pair in (5, 10):
            pass  # never split 5s or 10s, fall through to normal logic

    # --- Soft totals (has an Ace counted as 11) ---
    if soft:
        if total >= 19:
            return "STAND"
        if total == 18:
            return "STAND" if dealer_up in (2, 7, 8) else "HIT"
        return "HIT"  # soft 17 or less

    # --- Hard totals ---
    if total >= 17:
        return "STAND"
    if total <= 11:
        return "HIT"
    if 12 <= total <= 16:
        # Stand if dealer shows weak card (2-6), else hit
        return "STAND" if dealer_up in range(2, 7) else "HIT"

    return "HIT"


if __name__ == "__main__":
    print("Enter card values as 2-10 or 'A' (Ace).")
    raw = input("Your cards (comma separated, e.g. 8,8 or A,6): ")
    cards = [int(c) if c.strip() != 'A' else 'A' for c in raw.split(',')]

    dealer_raw = input("Dealer's up-card: ").strip()
    dealer_up = int(dealer_raw) if dealer_raw != 'A' else 'A'

    decision = advise(cards, dealer_up)
    total, soft = hand_value(cards)
    kind = "soft" if soft else "hard"
    print(f"\nYour hand: {cards} ({kind} {total}) vs dealer {dealer_up}")
    print(f"Decision: {decision}")
