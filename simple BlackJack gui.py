import random
import tkinter as tk
from tkinter import messagebox

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['S', 'H', 'D', 'C']  # Spades, Hearts, Diamonds, Clubs


# ---------- Game logic (same rules as the console version) ----------

def new_shoe():
    deck = [(r, s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def card_str(card):
    return f"{card[0]}{card[1]}"


def hand_str(cards, hide_second=False):
    if hide_second and len(cards) > 1:
        return card_str(cards[0]) + " ??"
    return ' '.join(card_str(c) for c in cards)


def hand_value(cards):
    total, aces = 0, 0
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


def advise(cards, dealer_up_rank, can_double, can_split):
    total, soft = hand_value(cards)
    up = rank_group(dealer_up_rank)

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


# ---------- GUI application ----------

class BlackjackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack")
        self.root.geometry("420x480")
        self.root.configure(bg="#0f3d2e")

        self.bankroll = 1000
        self.shoe = new_shoe()
        self.player_hands = []
        self.dealer_cards = []
        self.active_index = 0
        self.phase = "betting"  # betting | player | roundover

        self._build_widgets()
        self._render_betting()

    # ---- widget layout, built once ----
    def _build_widgets(self):
        font_big = ("Georgia", 16, "bold")
        font_med = ("Georgia", 12)

        self.bankroll_lbl = tk.Label(self.root, text="", font=font_big,
                                      bg="#0f3d2e", fg="#c9a227")
        self.bankroll_lbl.pack(pady=(10, 0))

        self.dealer_lbl = tk.Label(self.root, text="Dealer: ", font=font_med,
                                    bg="#0f3d2e", fg="white")
        self.dealer_lbl.pack(pady=(15, 0))

        self.player_lbl = tk.Label(self.root, text="You: ", font=font_med,
                                    bg="#0f3d2e", fg="white")
        self.player_lbl.pack(pady=(15, 0))

        self.advisor_lbl = tk.Label(self.root, text="", font=("Georgia", 11, "italic"),
                                     bg="#0f3d2e", fg="#c9a227")
        self.advisor_lbl.pack(pady=(10, 0))

        self.status_lbl = tk.Label(self.root, text="", font=font_med,
                                    bg="#0f3d2e", fg="white", wraplength=380)
        self.status_lbl.pack(pady=(5, 10))

        # Betting controls
        self.bet_frame = tk.Frame(self.root, bg="#0f3d2e")
        tk.Label(self.bet_frame, text="Bet: $", bg="#0f3d2e", fg="white").pack(side="left")
        self.bet_entry = tk.Entry(self.bet_frame, width=8)
        self.bet_entry.insert(0, "50")
        self.bet_entry.pack(side="left", padx=5)
        self.deal_btn = tk.Button(self.bet_frame, text="Deal", command=self.on_deal,
                                   bg="#c9a227")
        self.deal_btn.pack(side="left", padx=5)
        self.bet_frame.pack(pady=5)

        # Action controls
        self.action_frame = tk.Frame(self.root, bg="#0f3d2e")
        self.hit_btn = tk.Button(self.action_frame, text="Hit", width=8, command=self.on_hit)
        self.stand_btn = tk.Button(self.action_frame, text="Stand", width=8, command=self.on_stand)
        self.double_btn = tk.Button(self.action_frame, text="Double", width=8, command=self.on_double)
        self.split_btn = tk.Button(self.action_frame, text="Split", width=8, command=self.on_split)
        self.hit_btn.grid(row=0, column=0, padx=3)
        self.stand_btn.grid(row=0, column=1, padx=3)
        self.double_btn.grid(row=0, column=2, padx=3)
        self.split_btn.grid(row=0, column=3, padx=3)

        # Next-round control
        self.next_frame = tk.Frame(self.root, bg="#0f3d2e")
        self.next_btn = tk.Button(self.next_frame, text="Next hand", command=self.on_next,
                                   bg="#c9a227")
        self.next_btn.pack()

    # ---- helpers ----
    def draw(self):
        if len(self.shoe) < 8:
            self.shoe.extend(new_shoe())
        return self.shoe.pop()

    def active_hand(self):
        return self.player_hands[self.active_index]

    def _render_betting(self):
        self.phase = "betting"
        self.bankroll_lbl.config(text=f"Bankroll: ${self.bankroll}")
        self.dealer_lbl.config(text="Dealer: ")
        self.player_lbl.config(text="You: ")
        self.advisor_lbl.config(text="")
        self.status_lbl.config(text="Place your bet and click Deal.")
        self.action_frame.pack_forget()
        self.next_frame.pack_forget()
        self.bet_frame.pack(pady=5)

    def _render_table(self, hide_dealer_second=True):
        self.bankroll_lbl.config(text=f"Bankroll: ${self.bankroll}")
        self.dealer_lbl.config(
            text="Dealer: " + hand_str(self.dealer_cards, hide_second=hide_dealer_second)
        )

        lines = []
        for idx, h in enumerate(self.player_hands):
            total, soft = hand_value(h['cards'])
            marker = " <-- your turn" if (self.phase == "player" and idx == self.active_index) else ""
            tag = f"Hand {idx + 1}" if len(self.player_hands) > 1 else "Hand"
            bust = " (bust)" if total > 21 else ""
            result = f" [{h['result']}]" if h.get('result') else ""
            lines.append(f"{tag}: {hand_str(h['cards'])}  = {total}{bust}{result}  bet ${h['bet']}{marker}")
        self.player_lbl.config(text="You:\n" + "\n".join(lines))

    # ---- betting ----
    def on_deal(self):
        try:
            bet = int(self.bet_entry.get())
        except ValueError:
            messagebox.showerror("Invalid bet", "Enter a whole number.")
            return
        if bet <= 0 or bet > self.bankroll:
            messagebox.showerror("Invalid bet", "Bet must be within your bankroll.")
            return

        self.dealer_cards = [self.draw(), self.draw()]
        self.player_hands = [{
            'cards': [self.draw(), self.draw()],
            'bet': bet,
            'is_split_ace': False,
            'can_split_now': True,
            'result': None,
        }]
        self.active_index = 0
        self.phase = "player"

        self.bet_frame.pack_forget()
        self.action_frame.pack(pady=5)
        self.next_frame.pack_forget()

        total, _ = hand_value(self.player_hands[0]['cards'])
        if total == 21:
            self._render_table(hide_dealer_second=False)
            self.player_hands[0]['done'] = True
            self._settle_round()
            return

        self._render_table()
        self._update_action_buttons()
        self._update_advisor()

    # ---- player actions ----
    def _update_action_buttons(self):
        h = self.active_hand()
        total, _ = hand_value(h['cards'])
        can_double = len(h['cards']) == 2 and not h['is_split_ace'] and self.bankroll >= h['bet']
        can_split = (
            h['can_split_now'] and len(h['cards']) == 2 and
            rank_group(h['cards'][0][0]) == rank_group(h['cards'][1][0]) and
            self.bankroll >= h['bet'] and len(self.player_hands) < 4
        )
        self.double_btn.config(state="normal" if can_double else "disabled")
        self.split_btn.config(state="normal" if can_split else "disabled")
        self.hit_btn.config(state="disabled" if total >= 21 else "normal")
        self.stand_btn.config(state="disabled" if total >= 21 else "normal")

    def _update_advisor(self):
        h = self.active_hand()
        can_double = len(h['cards']) == 2 and not h['is_split_ace']
        can_split = h['can_split_now']
        hint = advise(h['cards'], self.dealer_cards[0][0], can_double, can_split)
        self.advisor_lbl.config(text=f"Advisor suggests: {hint}")

    def on_hit(self):
        h = self.active_hand()
        h['cards'].append(self.draw())
        total, _ = hand_value(h['cards'])
        self._render_table()
        if total >= 21:
            self._advance_hand()
        else:
            self._update_action_buttons()
            self._update_advisor()

    def on_stand(self):
        self._advance_hand()

    def on_double(self):
        h = self.active_hand()
        h['bet'] *= 2
        h['cards'].append(self.draw())
        self._render_table()
        self._advance_hand()

    def on_split(self):
        h = self.active_hand()
        is_ace = h['cards'][0][0] == 'A'
        c1, c2 = h['cards'][0], h['cards'][1]
        h['cards'] = [c1, self.draw()]
        h['is_split_ace'] = is_ace
        h['can_split_now'] = False
        new_hand = {
            'cards': [c2, self.draw()],
            'bet': h['bet'],
            'is_split_ace': is_ace,
            'can_split_now': False,
            'result': None,
        }
        self.player_hands.insert(self.active_index + 1, new_hand)
        self._render_table()
        if is_ace:
            self._advance_hand()
        else:
            self._update_action_buttons()
            self._update_advisor()

    def _advance_hand(self):
        self.active_index += 1
        while self.active_index < len(self.player_hands):
            h = self.player_hands[self.active_index]
            if h['is_split_ace']:
                self.active_index += 1
                continue
            break
        if self.active_index >= len(self.player_hands):
            self._dealer_turn()
        else:
            self._render_table()
            self._update_action_buttons()
            self._update_advisor()

    # ---- dealer + settling ----
    def _dealer_turn(self):
        self.phase = "dealer"
        self.action_frame.pack_forget()
        any_alive = any(hand_value(h['cards'])[0] <= 21 for h in self.player_hands)
        if any_alive:
            self._dealer_step()
        else:
            self._settle_round()

    def _dealer_step(self):
        total, _ = hand_value(self.dealer_cards)
        if total < 17:
            self.dealer_cards.append(self.draw())
            self._render_table(hide_dealer_second=False)
            self.root.after(500, self._dealer_step)
        else:
            self._settle_round()

    def _settle_round(self):
        self.phase = "roundover"
        d_total, _ = hand_value(self.dealer_cards)
        for h in self.player_hands:
            if h.get('result'):
                continue
            p_total, _ = hand_value(h['cards'])
            if p_total == 21 and len(h['cards']) == 2 and len(self.player_hands) == 1:
                winnings = int(h['bet'] * 1.5)
                self.bankroll += winnings
                h['result'] = f"Blackjack +${winnings}"
            elif p_total > 21:
                self.bankroll -= h['bet']
                h['result'] = f"Bust -${h['bet']}"
            elif d_total > 21 or p_total > d_total:
                self.bankroll += h['bet']
                h['result'] = f"Win +${h['bet']}"
            elif p_total == d_total:
                h['result'] = "Push"
            else:
                self.bankroll -= h['bet']
                h['result'] = f"Lose -${h['bet']}"

        self._render_table(hide_dealer_second=False)
        self.advisor_lbl.config(text="")
        if self.bankroll <= 0:
            self.status_lbl.config(text="Out of chips! Next hand resets your bankroll to $1000.")
        else:
            self.status_lbl.config(text="Round over.")
        self.action_frame.pack_forget()
        self.next_frame.pack(pady=5)

    def on_next(self):
        if self.bankroll <= 0:
            self.bankroll = 1000
        self._render_betting()


if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackApp(root)
    root.mainloop()
