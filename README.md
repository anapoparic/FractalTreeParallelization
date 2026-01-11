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
- Rezultati se grupišu po dubini (iteracijama) i čuvaju u JSON format

**Paralelna verzija:**

- **Biblioteka:** `multiprocessing.Pool`
- **Strategija**: Sekvencijalno generisanje prvih parallel_depth nivoa, zatim paralelna obrada podstabala
- **Optimizacija**: Auto-kalkulacija optimalnog parallel_depth parametra na osnovu veličine problema i broja CPU jezgara
- Svaki worker proces nezavisno generiše kompletno podstablo koristeći isti rekurzivni algoritam
- Rezultati iz svih procesa se čuvaju u JSON format
- **Broj nivoa paralelizacije:** ograničen, jer bi dublja paralelizacija dovela do overhead-a

### Rust implementacija

**Sekvencijalna verzija:**

- Rekurzivna funkcija koja generiše grane i čuva ih u `Vec<Branch>` strukturi.
- Svaka grana se reprezentuje kao struct sa poljima (x1, y1, x2, y2, depth).
- Koristi trigonometriju za izračunavanje krajnjih pozicija i depth-first pristup generisanju

**Paralelna verzija:**

- **Biblioteka:** [std::thread](https://doc.rust-lang.org/std/thread/) - manuelna kontrola thread-ova
- **Strategija:** Identična Python strategiji - sekvencijalno generisanje prvih parallel_depth nivoa, zatim paralelna obrada podstabala.
- Optimizacija: Auto-kalkulacija optimalnog parallel_depth parametra na osnovu veličine problema i broja dostupnih thread-ova.
- Svaki thread nezavisno generiše kompletno podstablo, rezultati se agregiraju kroz `Arc<Mutex<Vec<Branch>>>`

### Vizualizacija

Vizualizacija će biti urađena sa bibliotekom [Plotters](https://github.com/plotters-rs/plotters). Algoritam generiše listu grana gde svaka grana sadrži koordinate početne i krajnje tačke (x1, y1, x2, y2) i dubinu u stablu. Finalna vizualizacija prikazuje kompletno fraktalno stablo crtanjem linija između tačaka svake grane i biće eksportovana u PNG format.

### Merenje performansi

Performanse će biti merene kroz sledeće eksperimente:

**Metrika:**

- **Vreme izvršavanja** - ukupno vreme potrebno za generisanje kompletnog fraktalnog stabla (od početka rekurzije do kraja)
- **Speedup** - odnos vremena sekvencijalne i paralelne verzije u istom jeziku

1. **Poređenje Python verzija:** Merenje razlike između Python sekvencijalne i paralelne implementacije
2. **Poređenje Rust verzija:** Merenje razlike između Rust sekvencijalne i paralelne implementacije

**Varijabilni parametri:**

- Različite dubine stabla (broj nivoa rekurzije)
- Različiti uglovi grananja
- Različiti faktori smanjenja dužine grana

Cilj je pokazati u kojim scenarijima paralelizacija daje najviše koristi i koje su razlike između process-based (Python) i thread-based (Rust) paralelizacije.

**Testna platforma:**

- Procesor: Intel(R) Core(TM) i5-1035G1 CPU @ 1.00GHz 1.19 GHz
- Python verzija: 3.11
- Rust verzija: 1.91

## Reference

- [std::thread](https://doc.rust-lang.org/std/thread/)
- [Arc](https://doc.rust-lang.org/std/sync/struct.Arc.html)
- [Mutex](https://doc.rust-lang.org/std/sync/struct.Mutex.html)
- [Plotters - Rust plotting library](https://github.com/plotters-rs/plotters)
- [Python multiprocessing documentation](https://docs.python.org/3/library/multiprocessing.html)

---

**Ana Poparić SV 74/2021**
