module temp_proof where

open import Data.Nat
open import Data.Nat.Properties

two : ℕ
two = 1 + 1

proof : two ≡ 2
proof = refl