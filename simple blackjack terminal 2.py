import random

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['S', 'H', 'D', 'C']  # Spades, Hearts, Diamonds, Clubs


def new_shoe():
    deck = [(r, s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def draw(shoe):
    if len(shoe) < 8:
        shoe.extend(new_shoe())
    return shoe.pop()


def card_str(card):
    return f"{card[0]}{card[1]}"


def hand_str(cards):
    return ' '.join(card_str(c) for c in cards)


def hand_value(cards):
    total = 0
    aces = 0
    for rank, _ in cards:
        if rank == 'A':
            aces += 1
            total += 11
        elif rank in ('J', 'Q', 'K'):
            total += 10
        else:
            total += int(rank)
    soft = aces > 0
    while total > 21 and aces:
        total -= 10
        aces -= 1
        soft = aces > 0
    return total, soft


def rank_group(rank):
    if rank in ('J', 'Q', 'K'):
        return 10
    if rank == 'A':
        return 'A'
    return int(rank)


def advise(cards, dealer_up, can_double, can_split):
    total, soft = hand_value(cards)
    up = rank_group(dealer_up)

    if can_split and len(cards) == 2 and rank_group(cards[0][0]) == rank_group(cards[1][0]):
        p = rank_group(cards[0][0])
        if p == 'A' or p == 8:
            return 'Split'
        if p == 9:
            return 'Stand' if up in (7, 10, 'A') else 'Split'
        if p in (2, 3, 7) and up != 'A' and up <= 7:
            return 'Split'
        if p == 6 and up != 'A' and up <= 6:
            return 'Split'
        if p == 4 and up in (5, 6):
            return 'Split'

    if soft:
        if total >= 19:
            return 'Stand'
        if total == 18:
            if can_double and up in (3, 4, 5, 6):
                return 'Double'
            return 'Stand' if up in (2, 7, 8) else 'Hit'
        if total == 17:
            return 'Double' if can_double and up != 'A' and 3 <= up <= 6 else 'Hit'
        if total in (15, 16):
            return 'Double' if can_double and up != 'A' and 4 <= up <= 6 else 'Hit'
        if total in (13, 14):
            return 'Double' if can_double and up in (5, 6) else 'Hit'
        return 'Hit'

    if total >= 17:
        return 'Stand'
    if total <= 8:
        return 'Hit'
    if total == 9:
        return 'Double' if can_double and up != 'A' and 3 <= up <= 6 else 'Hit'
    if total == 10:
        return 'Double' if can_double and up != 'A' and up <= 9 else 'Hit'
    if total == 11:
        return 'Double' if can_double and up != 'A' else 'Hit'
    return 'Stand' if up != 'A' and up <= 6 else 'Hit'


def ask(prompt, choices):
    while True:
        answer = input(prompt).strip().lower()
        if answer in choices:
            return answer
        print(f"  Please enter one of: {', '.join(choices)}")


def play_hand(cards, bet, dealer_up_card, shoe, is_split_ace=False, allow_split=True):
    """Play a single hand until it's done. Returns (final_cards, final_bet)."""
    if is_split_ace:
        return cards, bet

    while True:
        total, _ = hand_value(cards)
        if total >= 21:
            return cards, bet

        can_double = len(cards) == 2
        can_split = (
            allow_split and len(cards) == 2 and
            rank_group(cards[0][0]) == rank_group(cards[1][0])
        )
        hint = advise(cards, dealer_up_card[0][0], can_double, can_split)

        options = ['h', 's']
        label = "(h)it / (s)tand"
        if can_double:
            options.append('d')
            label += " / (d)ouble"
        if can_split:
            options.append('p')
            label += " / s(p)lit"

        print(f"\nYour hand: {hand_str(cards)}  (total: {total})")
        print(f"Advisor suggests: {hint}")
        choice = ask(f"{label}: ", options)

        if choice == 'h':
            cards.append(draw(shoe))
            print(f"You drew {card_str(cards[-1])}")
        elif choice == 's':
            return cards, bet
        elif choice == 'd':
            bet *= 2
            cards.append(draw(shoe))
            print(f"You doubled down and drew {card_str(cards[-1])}")
            return cards, bet
        elif choice == 'p':
            return 'SPLIT', bet


def play_round(bankroll):
    print("\n" + "=" * 40)
    while True:
        try:
            bet = int(input(f"Bankroll: ${bankroll}. Place your bet: $"))
            if 0 < bet <= bankroll:
                break
        except ValueError:
            pass
        print("  Enter a valid bet within your bankroll.")

    shoe = new_shoe()
    player_hands = [{'cards': [draw(shoe), draw(shoe)], 'bet': bet}]
    dealer_cards = [draw(shoe), draw(shoe)]

    print(f"\nDealer shows: {card_str(dealer_cards[0])} [hidden]")

    p_total, _ = hand_value(player_hands[0]['cards'])
    d_total, _ = hand_value(dealer_cards)
    if p_total == 21:
        print(f"Your hand: {hand_str(player_hands[0]['cards'])} -- Blackjack!")
        if d_total == 21:
            print(f"Dealer also has blackjack: {hand_str(dealer_cards)}. Push.")
            return bankroll
        print(f"Dealer's hand: {hand_str(dealer_cards)} (total {d_total})")
        winnings = int(bet * 1.5)
        print(f"You win ${winnings}!")
        return bankroll + winnings

    # Play out all hands (handles one level of splitting)
    i = 0
    while i < len(player_hands):
        h = player_hands[i]
        result, new_bet = play_hand(
            h['cards'], h['bet'], dealer_cards, shoe,
            is_split_ace=h.get('is_split_ace', False),
            allow_split=len(player_hands) < 4
        )
        if result == 'SPLIT':
            c1, c2 = h['cards'][0], h['cards'][1]
            is_ace = c1[0] == 'A'
            h['cards'] = [c1, draw(shoe)]
            h['is_split_ace'] = is_ace
            new_hand = {'cards': [c2, draw(shoe)], 'bet': h['bet'], 'is_split_ace': is_ace}
            player_hands.insert(i + 1, new_hand)
            print(f"Split into two hands.")
            continue  # replay this hand (now resolved unless it's a split ace)
        else:
            h['cards'], h['bet'] = result, new_bet
            i += 1

    print(f"\nDealer reveals: {hand_str(dealer_cards)} (total {hand_value(dealer_cards)[0]})")
    any_alive = any(hand_value(h['cards'])[0] <= 21 for h in player_hands)
    if any_alive:
        while hand_value(dealer_cards)[0] < 17:
            dealer_cards.append(draw(shoe))
            print(f"Dealer draws {card_str(dealer_cards[-1])} -> {hand_str(dealer_cards)}")
    d_total, _ = hand_value(dealer_cards)

    for idx, h in enumerate(player_hands, 1):
        p_total, _ = hand_value(h['cards'])
        tag = f"Hand {idx}" if len(player_hands) > 1 else "Your hand"
        print(f"\n{tag}: {hand_str(h['cards'])} (total {p_total}), bet ${h['bet']}")
        if p_total > 21:
            print("Busted -- you lose.")
            bankroll -= h['bet']
        elif d_total > 21 or p_total > d_total:
            print("You win!")
            bankroll += h['bet']
        elif p_total == d_total:
            print("Push.")
        else:
            print("Dealer wins.")
            bankroll -= h['bet']

    return bankroll


def main():
    print("Welcome to the table. You start with $1000.")
    bankroll = 1000
    while bankroll > 0:
        bankroll = play_round(bankroll)
        if bankroll <= 0:
            print("\nYou're out of chips. Game over.")
            break
        again = ask("\nPlay another hand? (y/n): ", ['y', 'n'])
        if again == 'n':
            break
    print(f"\nFinal bankroll: ${bankroll}. Thanks for playing!")


if __name__ == "__main__":
    main()
