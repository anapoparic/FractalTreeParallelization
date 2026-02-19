# Paralelizacija algoritma za generisanje fraktalnog stabla

**Predmet:** Napredne tehnike programiranja

**Ocena** za koju se radi projektni zadatak: 10

<p align="center"><img width=50% src="Fractal-Tree.jpg"></p>

## Opis problema

**Binarno fraktalno stablo** je rekurzivna struktura definisana simetričnim binarnim grananjem. Stablo počinje sa deblom određene dužine koje se deli na dve grane, od kojih svaka ima dužinu `r × parent_length` i zaklapa određeni ugao sa roditeljskom granom. Svaka od ovih grana se dalje deli na još dve grane manje dužine, i tako rekurzivno dok dužina grane ne postane manja od zadatog praga.

Generisanje fraktalnog stabla je računski intenzivan proces, posebno za velika stabla sa mnogo nivoa rekurzije. Međutim, ovaj problem ima mogućnost **paralelizacije** - svaka grana može nezavisno da generiše svoje podstablo, što omogućava podelu posla između više procesnih jezgara.

## Cilj projekta

Cilj projekta je:

1. **Implementirati algoritam** za generisanje binarnog fraktalnog stabla
2. **Paralelizovati algoritam** korišćenjem modernih tehnika paralelnog programiranja
3. **Uporediti performanse** sekvencijalne i paralelne verzije
4. **Implementirati rešenje u dva jezika**: Python i Rust
5. **Vizualizovati** generisano fraktalno stablo

## Metode i tehnologije

### Python implementacija

**Sekvencijalna verzija:**

- Rekurzivna funkcija koja generiše grane stabla depth-first pristupom
- Svaka grana se reprezentuje kao tuple (x1, y1, x2, y2, depth)
- Algoritam koristi trigonometriju za izračunavanje krajnjih pozicija grana
- Rezultati se grupišu po dubini (iteracijama) i čuvaju u JSON formatu

**Paralelna verzija:**

- **Biblioteka:** `multiprocessing.Pool`
- **Strategija**: Sekvencijalno generisanje prvih `split_depth` nivoa, zatim paralelna obrada podstabala kroz pool worker procese
- **Optimizacija**: Auto-kalkulacija optimalnog `split_depth` parametra na osnovu broja CPU jezgara
- Svaki worker proces nezavisno generiše kompletno podstablo koristeći isti rekurzivni algoritam
- Rezultati iz svih procesa se kombinuju kroz `numpy.concatenate` za efikasnu IPC serijalizaciju

### Rust implementacija

**Sekvencijalna verzija:**

- Rekurzivna funkcija koja generiše grane i čuva ih u `Vec<Branch>` strukturi
- Svaka grana se reprezentuje kao struct sa poljima (x1, y1, x2, y2, depth)
- Koristi trigonometriju za izračunavanje krajnjih pozicija i depth-first pristup generisanju
- Kapacitet vektora se unapred rezerviše koristeći `count_branches` funkciju (nula realokacija)

**Paralelna verzija:**

- **Biblioteka:** [Rayon](https://github.com/rayon-rs/rayon) - data parallelism biblioteka
- **Strategija:** Identična Python strategiji - sekvencijalno generisanje prvih `split_depth` nivoa, zatim paralelna obrada podstabala
- **Optimizacija**: Auto-kalkulacija optimalnog `split_depth` parametra na osnovu broja dostupnih threadova
- Svaki task nezavisno generiše kompletno podstablo sa pre-alokovanim `Vec<Branch>`; rezultati se čuvaju kao `Vec<Vec<Branch>>` bez potrebe za spajanjem

### Vizualizacija

Vizualizacija fraktalnog stabla urađena je Python `turtle` bibliotekom (`tree-visualization.py`). Grafovi performansi generišu se iz CSV rezultata eksperimenata.

### Merenje performansi

Eksperimenti se pokreću kroz `scripts/run_all.py` koji za svaku konfiguraciju izvršava više ponavljanja i čuva rezultate u CSV format.

**Metrika:**

- **Vreme izvršavanja** - ukupno vreme potrebno za generisanje kompletnog fraktalnog stabla (od početka rekurzije do kraja)
- **Speedup** - odnos vremena sekvencijalne i paralelne verzije u istom jeziku

**Tipovi skaliranja:**

1. **Strong scaling** - isti problem, povećava se broj jezgara (1, 2, 4, 8)
2. **Weak scaling** - problem raste proporcionalno sa brojem jezgara

Cilj je pokazati u kojim scenarijima paralelizacija daje najviše koristi i koje su razlike između process-based (Python) i thread-based (Rust) paralelizacije.

**Testna platforma:**

- Procesor: Intel(R) Core(TM) i5-1035G1 CPU @ 1.00GHz 1.19 GHz
- Python verzija: 3.11
- Rust verzija: 1.91

## Reference

- [Rayon - data parallelism library for Rust](https://github.com/rayon-rs/rayon)
- [Python multiprocessing documentation](https://docs.python.org/3/library/multiprocessing.html)
- [Python turtle graphics](https://docs.python.org/3/library/turtle.html)

---

**Ana Poparić SV 74/2021**
