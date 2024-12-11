data Nat : Set where
  zero : Nat
  suc  : Nat → Nat

one : Nat
one = suc zero

two : Nat
two = suc one

_>_ : Nat → Nat → Set
zero > n = ⊥
suc m > zero = ⊤
suc m > suc n = m > n

one_gt_zero : one > zero
one_gt_zero = λ () → ()