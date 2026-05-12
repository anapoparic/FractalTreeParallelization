# Paralelizacija generisanja fraktalnog stabla

**Autor:** Ana Poparić, SV 74/2021
**Predmet:** Napredne tehnike programiranja

---

## Tema

Tema teze je istraživanje efikasnosti paralelizacije rekurzivnih algoritama na primeru generisanja binarnog fraktalnog stabla. Centralno pitanje je: **kako tip problema, jezik i model paralelizma utiču na ubrzanje koje paralelizacija može da pruži?**

---

## Proširenje problema

Osnovna varijanta problema je generisanje **simetričnog** binarnog fraktalnog stabla — rekurzivne strukture gde svaka grana rađa dve podgrane jednakih proporcija.

Proširenje uvodi **asimetrično** stablo: leva i desna grana imaju različite faktore skaliranja i različite uglove grananja. Ovo je bliže realnim prirodnim strukturama i unosi tehničku komplikaciju — podstabla više nisu jednakih veličina, što direktno utiče na raspodelu posla između procesora (load imbalance).

---

## Implementacija

Problem je implementiran u dva jezika s fundamentalno različitim modelima paralelizma:

- **Python** — `multiprocessing.Pool`: svaki radni proces je poseban OS proces sa zasebnim Python interpretatorom; komunikacija ide kroz serijalizaciju (pickle)
- **Rust** — `rayon`: niti unutar jednog procesa dele memoriju; dinamički work-stealing scheduler raspodeljuje zadatke

Ova razlika u modelima paralelizma je jedan od ključnih faktora koji se istražuju.

---

## Rezultati i analiza

Detaljna merenja, tabele, teorijska analiza (Amdahlov i Gustafsonov zakon) i zaključci nalaze se u:

**[report.md](report.md)**
