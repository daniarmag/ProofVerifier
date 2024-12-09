data Nat : Set where
  zero : Nat
  suc  : Nat → Nat

plus : Nat → Nat → Nat
plus zero     n = n
plus (suc m) n = suc (plus m n)

plus-comm : (a b : Nat) → plus a b ≡ plus b a
plus-comm zero     b = refl
plus-comm (suc a) b = begin
  plus (suc a) b
  ≡⟨⟩
  suc (plus a b)
  ≡⟨ plus-comm a b ⟩
  suc (plus b a)
  ≡⟨⟩
  plus b (suc a)
  ≡⟨⟩
  refl