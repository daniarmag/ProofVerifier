data ℕ : Set where
  zero : ℕ
  suc  : ℕ → ℕ

_+_ : ℕ → ℕ → ℕ
zero + n = n
suc m + n = suc (m + n)

cong : ∀ {A B : Set} {x y : A} (f : A → B) → x ≡ y → f x ≡ f y
cong f refl = refl

comm+ : ∀ (a b : ℕ) → a + b ≡ b + a
comm+ zero n = refl
comm+ (suc m) n = cong suc (comm+ m n)