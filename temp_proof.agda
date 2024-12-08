data Nat : Set where
  zero : Nat
  suc  : Nat → Nat

one : Nat
one = suc zero

two : Nat
two = suc one

add : Nat → Nat → Nat
add zero      m = m
add (suc n) m = suc (add n m)

onePlusOneIsTwo : add one one ≡ two
onePlusOneIsTwo = begin
  add one one
  ≡⟨ refl ⟩
  add (suc zero) one
  ≡⟨ refl ⟩
  suc (add zero one)
  ≡⟨ refl ⟩
  suc one
  ≡⟨ refl ⟩
  two
  ∎