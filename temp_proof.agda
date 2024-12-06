module OnePlusOneEqualsTwo where

-- Define natural numbers
data Nat : Set where
  zero : Nat
  suc  : Nat → Nat

-- Define the addition operation
_+_ : Nat → Nat → Nat
zero + n       = n
(suc m) + n    = suc (m + n)

-- Define the number 1 and 2
one : Nat
one = suc zero

two : Nat
two = suc one

-- Prove that 1 + 1 = 2
onePlusOneEqualsTwo : one + one ≡ two
onePlusOneEqualsTwo = refl