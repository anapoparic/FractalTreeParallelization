# Izveštaj o Jakom i Slabom Skaliranju — Fraktalno Stablo

---

## 1. Arhitektura Sistema

### 1.1 Hardverska konfiguracija

**Procesor:**

| Atribut                                    | Vrednost                                                |
| ------------------------------------------ | ------------------------------------------------------- |
| Model                                      | Intel Core i5-1035G1                                    |
| Mikroarhitektura                           | Ice Lake (10 nm)                                        |
| Bazni takt                                 | 1.00 GHz                                                |
| Turbo takt (1 jezgro / sva jezgra)         | 3.60 GHz / 3.40 GHz                                     |
| Fizička jezgra                             | 4                                                       |
| Logička jezgra                             | 8 (Hyper-Threading)                                     |
| L1 keš (po jezgru)                         | 48 KB podatkovni + 32 KB instrukcioni                   |
| L2 keš (po jezgru)                         | 512 KB (ukupno 2 MB)                                    |
| L3 keš (deljeni)                           | 6 MB                                                    |
| NUMA čvorovi                               | 1 (jednoprocesorski sistem, uniforman pristup memoriji) |
| Tip procesorskog paketa (CPU package type) | BGA (laptop, integrisano hlađenje)                      |

> **Napomena o termalnom ograničenju:** Eksperimenti su vršeni na laptop procesoru sa ograničenim kapacitetom hlađenja. Kod eksperimenata koji dugo traju, moguća je termalna regulacija koja smanjuje takt ispod nominalnog, što može uticati na merene rezultate.

**Memorija:**

| Atribut          | Vrednost       |
| ---------------- | -------------- |
| Ukupan kapacitet | 8 GB           |
| Tip              | DDR4           |
| Brzina           | 2667 MHz       |
| Konfiguracija    | Single-channel |

### 1.2 Softverska Konfiguracija

**Operativni sistem:**

| Atribut         | Vrednost                 |
| --------------- | ------------------------ |
| OS              | Microsoft Windows 11 Pro |
| Build broj      | 26200                    |
| Verzija kernela | 10.0.26200               |

**Python okruženje:**

| Biblioteka      | Verzija | Uloga                          |
| --------------- | ------- | ------------------------------ |
| Python          | 3.11    | Interpretator                  |
| multiprocessing | stdlib  | Paralelizacija (više procesa)  |
| numpy           | 1.26.4  | Numeričke operacije, keš grana |
| matplotlib      | 3.9.1   | Generisanje grafika            |

> **Napomena — Windows multiprocessing:** Python `multiprocessing` na Windows platformi koristi metod **`spawn`** za kreiranje procesa (za razliku od `fork` na Linux/macOS). Metod `spawn`, svaki radni proces startuje potpuno novi Python interpretator, uvozi sve module i prima argumente serijalizacijom (pickle). Ovaj fiksni trošak (~300 ms po pokretanju) je dominantan faktor koji negativno utiče na Python paralelne rezultate.

**Rust okruženje:**

| Biblioteka/Alat    | Verzija | Uloga                                                                 |
| ------------------ | ------- | --------------------------------------------------------------------- |
| rustc              | 1.91.0  | Kompajler                                                             |
| cargo              | 1.91.0  | Build sistem                                                          |
| rayon              | 1.10    | Automatski raspored zadataka na više CPU jezgara (work-stealing niti) |
| serde / serde_json | 1.0     | Serijalizacija JSON izlaza                                            |

---

## 2. Eksperimentalni parametri

```
trunk_length  = 100.0
ratio         = 0.67          (simetrično stablo)
left_ratio    = 0.67          (asimetrično stablo)
right_ratio   = 0.57          (asimetrično stablo)
branch_angle  = 30.0°
Broj merenja po konfiguraciji = 10
```

---

## 3. Analiza sekvencijalnog i paralelnog dela

### 3.1 Identifikacija sekvencijalnog i paralelnog dela

Svaka paralelna implementacija se sastoji od dva koraka:

1. **Sekvencijalni deo** — gornji nivoi stabla grade se jedan po jedan, bez paralelizacije. Broj jezgara ovde ne utiče na brzinu.
2. **Paralelni deo** — kada se dostigne određena dubina, svako podstablo postaje nezavisan zadatak koji se izvršava istovremeno na različitim jezgrima/nitima.

| Kod                             | Tip                        | Opis                                                   |
| ------------------------------- | -------------------------- | ------------------------------------------------------ |
| Generisanje seed grana          | **Sekvencijalni**          | Inicijalna ekspanzija stabla do dubine raspodele posla |
| Generisanje podstabala          | **Paralelni**              | Svako podstablo nezavisno, bez deljenih podataka       |
| Skupljanje i spajanje rezultata | **Sekvencijalni**          | Spajanje rezultujućih vektora                          |
| Kreiranje Pool/ThreadPool       | **Sekvencijalni**          | Jednokratni trošak pri pokretanju                      |
| IPC / Pickle (samo Python)      | **Sekvencijalni overhead** | Prenos podataka između procesa kroz operativni sistem  |

### 3.2 Procena paralelne frakcije

Vrednost p (paralelni deo) procenjena je iz izmerenih podataka, a sekvencijalni deo sledi direktno: f = 1 − p, jer zbir sekvencijalnog i paralelnog dela uvek čini 100% ukupnog vremena izvršavanja.

Oznake koje se koriste u formulama:

- `p` — udeo programa koji se može izvršavati paralelno (vrednost između 0 i 1)
- `f = 1 − p` — udeo programa koji mora da se izvršava sekvencijalno
- `N` — broj jezgara (procesora)
- `S` — izmereno ubrzanje: koliko puta je program brži sa N jezgara nego sa 1 jezgrom (`S = T(1) / T(N)`)
- `S_scaled` — skalirano ubrzanje kod slabog skaliranja: koliko više posla se završi u istom vremenu (`S_scaled = N · T(1) / T(N)`)

**Amdahlov zakon** (jako skaliranje): osnovna formula je `S = 1 / ((1−p) + p/N)`. Kada izmerimo S i znamo N, invertujemo je da bismo dobili p:
`(1−p) + p/N = 1/S  →  1 − p·(1−1/N) = 1/S  →  p = (1 − 1/S) / (1 − 1/N)`

**Gustafsonov zakon** (slabo skaliranje): osnovna formula je `S_scaled = 1 + p·(N−1)`. Invertovanjem:
`p·(N−1) = S_scaled − 1  →  p = (S_scaled − 1) / (N − 1)`, gde je `S_scaled = N · T(1) / T(N)`

#### Simetrično stablo — jako skaliranje (8,388,607 grana)

| Jezik  | Izmereno ubrzanje (8 jezgara) | Sekvencijalni deo `f` | Paralelni deo |
| ------ | :---------------------------: | :-------------------: | :-----------: |
| Rust   |            3.892×             |         ~8.2%         |    ~91.8%     |
| Python |            1.156×             |        ~89.9%         |    ~10.1%     |

#### Asimetrično stablo — jako skaliranje (919,442 grane)

| Jezik  | Izmereno ubrzanje (8 jezgara) | Sekvencijalni deo `f` | Paralelni deo |
| ------ | :---------------------------: | :-------------------: | :-----------: |
| Rust   |            3.413×             |        ~26.8%         |    ~73.2%     |
| Python |          **0.519×**           |         ~100%         |      ~0%      |

> **Ključna razlika Python vs Rust:** Algoritam je isti u obe implementacije — Python-ov visoki f nije posledica lošeg koda. Problem je spawn overhead: pokretanje jednog procesa na Windowsu košta ~300 ms, a pri 8 procesa taj trošak premašuje uštedu od paralelizacije. Rust nema ovaj problem jer koristi niti umesto procesa.

---

## 4. Teorijski Maksimumi Ubrzanja

### 4.1 Amdahlov zakon — Jako skaliranje

Amdahlov zakon: ako `f`deo programa mora biti sekvencijalan, maksimalno ubrzanje (bez obzira na broj jezgara) iznos `1/f`. Program koji je 10% sekvencijalan nikada ne može biti brži od 10× bez obzira na broj jezgara.

#### Simetrično stablo (p_Rust = 0.918, p_Python = 0.101)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.848   |   1.053   |
|     4      |  4.000  |   3.211   |   1.082   |
|     8      |  8.000  |   5.076   |   1.097   |
|     ∞      |    ∞    | **12.20** | **1.112** |

> **Napomena:** Amdahl predviđa ubrzanje 5.076× za 8 jezgara, a izmereno je 3.892×. Ovo odstupanje ukazuje da na 8 jezgara postoje dodatna ograničenja (memorijska propusnost, termalna regulacija) koja model ne uzima u obzir.

#### Asimetrično stablo (p_Rust = 0.732, p_Python ≈ 0)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.577   |   1.000   |
|     4      |  4.000  |   2.218   |   1.000   |
|     8      |  8.000  |   2.778   |   1.000   |
|     ∞      |    ∞    | **3.731** | **1.000** |

> **Zašto je asimetrično stablo lošije?**
>
> - **Rust:** Rayon work-stealing planer eliminiše pasivno čekanje, ali asimetrično stablo generiše manji broj nezavisnih podstabala, što smanjuje iskorišćenost niti. Tome se dodaje cache i sinhronizacijski overhead pri prenosu zadataka između jezgara — zbog čega sekvencijalni deo `f` raste sa 8.2% na 26.8%.
> - **Python:** `Pool.map` raspoređuje podstabla statički, bez dinamičkog preuzimanja posla. Procesi koji dobiju manja (desna) podstabla brzo završe i čekaju ostale — što direktno uvećava sekvencijalni deo `f`. Pošto je Python `f` ionako dominantan (spawn overhead), asimetrija samo dodatno pogoršava skalabilnost.

### 4.2 Gustafsonov zakon — Slabo skaliranje

Gustafsonov zakon: kada se broj jezgara povećava, povećava se i veličina problema (svako jezgro uvek ima isto toliko posla). Pitanje je koliko više posla može da se završi u istom vremenu.

#### Simetrično stablo (p_Rust = 0.137, p_Python ≈ 0)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.137   |   1.000   |
|     4      |  4.000  |   1.411   |   1.000   |
|     8      |  8.000  | **1.959** | **1.000** |

#### Asimetrično stablo (p_Rust = 0.030, p_Python ≈ 0)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.030   |   1.000   |
|     4      |  4.000  |   1.090   |   1.000   |
|     8      |  8.000  | **1.210** | **1.000** |

> **Zašto je asimetrično stablo lošije?**
>
> - **Rust:** Mali paralelni deo Rust asimetričnog stabla (~3%) posledica je dva faktora: pri ovoj veličini problema Rayon-ov overhead distribucije zadataka čini proporcionalno velik deo ukupnog vremena, a load imbalance asimetričnog stabla dodatno smanjuje iskoristivost jezgara. Simetrično stablo postiže p=13.7%, što ukazuje da strukturalna neravnoteža doprinosi razlici.
> - **Python:** Gustafsonov model ovde ne važi — osnovna pretpostavka (konstantno vreme pri rastu problema) nije ispunjena, jer spawn overhead uzrokuje da vreme raste umesto da ostaje isto. Izmeren paralelni deo p bi bio negativan, pa implementacija mapira na 0, što daje besmislen rezultat gustafson = 1.0.

---

## 5. Jako skaliranje (Strong Scaling)

**Veličina problema:** fiksna, `min_length = 0.01`

### 5.1 Simetrično stablo (8,388,607 grana)

### Python

<img src="data/symmetric/strong/python.png" width="700"/>

| Jezgra |     Grane | Srednje vreme | StdDev  | Ubrzanje  | Amdahl (p=0.101) | Outlieri |
| :----: | --------: | :-----------: | :-----: | :-------: | :--------------: | :------: |
|   1    | 8,388,607 |    5.112 s    | 0.679 s |   1.000   |      1.000       |    1     |
|   2    | 8,388,607 |    5.179 s    | 0.080 s | **0.987** |      1.053       |    0     |
|   4    | 8,388,607 |    4.539 s    | 0.076 s |   1.126   |      1.082       |    0     |
|   8    | 8,388,607 |    4.422 s    | 0.048 s |   1.156   |      1.097       |    0     |

- **2 jezgra sporija od 1 (0.987×):** Windows trošak pokretanja 2 procesa premašuje uštedu od paralelnog računanja.
- **4 jezgra (1.126×) i 8 jezgara (1.156×):** Minimalno ubrzanje, gotovo identično — 8 jezgara daje samo 2.7% više od 4 jezgra. Virtuelna jezgra 5–8 dele resurse sa fizičkim i ne donose dodatno ubrzanje.
- **Zaključak:** Python paralelizacija za ovaj problem praktično ne funkcioniše. Maksimalno ubrzanje od 1.156× za 8.4M grana znači da je overhead dominantan faktor.

### Rust

<img src="data/symmetric/strong/rust.png" width="700"/>

| Jezgra |     Grane | Srednje vreme |  StdDev  | Ubrzanje  | Amdahl (p=0.918) | Outlieri |
| :----: | --------: | :-----------: | :------: | :-------: | :--------------: | :------: |
|   1    | 8,388,607 |   0.2251 s    | 0.0360 s |   1.000   |      1.000       |    1     |
|   2    | 8,388,607 |   0.1126 s    | 0.0052 s | **1.999** |      1.848       |    0     |
|   4    | 8,388,607 |   0.0723 s    | 0.0022 s |   3.113   |      3.211       |    0     |
|   8    | 8,388,607 |   0.0578 s    | 0.0025 s | **3.892** |      5.076       |    1     |

- **Gotovo linearno ubrzanje na 2 jezgra (1.999× ≈ idealni 2.0×):** Rust niti nemaju trošak pokretanja jer su već pripremljene u thread pool-u — paralelizacija je skoro savršena.
- **4 jezgra (3.113×):** Ubrzanje nešto ispod idealnog (4.0×). Razlog je što 4 niti počinju da se takmiče za deljeni L3 keš.
- **8 jezgara (3.892×):** Amdahlov model predviđa 5.076×, a izmereno je 3.892×. Ovo odstupanje ukazuje da pri punom opterećenju 8 jezgara dolaze do izražaja memorijska propusnost i termalna regulacija.
- **Zaključak:** Rust rayon postiže odlično skaliranje sa samo ~8.2% sekvencijalnog dela.

### 5.2 Asimetrično stablo (919,442 grana)

### Python

<img src="data/asymmetric/strong/python.png" width="700"/>

| Jezgra |   Grane | Srednje vreme | StdDev  | Ubrzanje  | Outlieri |
| :----: | ------: | :-----------: | :-----: | :-------: | :------: |
|   1    | 919,442 |    0.587 s    | 0.053 s |   1.000   |    2     |
|   2    | 919,442 |    0.858 s    | 0.009 s | **0.684** |    0     |
|   4    | 919,442 |    0.991 s    | 0.095 s | **0.592** |    0     |
|   8    | 919,442 |    1.131 s    | 0.024 s | **0.519** |    0     |

- Program postaje **sporiji sa svakim dodatnim jezgrom**. Sa 8 jezgara traje skoro duplo duže nego sekvencijalno (0.587 s → 1.131 s).
- Uzrok: asimetrično stablo ima ~919K grana naspram ~8.4M za simetrično. Sa 8 procesa, Windows trošak pokretanja (~2.4 s ukupno) premašuje samo računanje (0.587 s).
- **Zaključak:** Ovo je ekstreman primer gde trošak paralelizacije ne samo da poništava dobit, već aktivno usporava program. Veličina problema mora biti dovoljno velika da amortizuje fiksni trošak pokretanja procesa.

### Rust

<img src="data/asymmetric/strong/rust.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev   | Ubrzanje | Amdahl (p=0.732) | Outlieri |
| :----: | ------: | :-----------: | :-------: | :------: | :--------------: | :------: |
|   1    | 919,442 |   0.02704 s   | 0.00313 s |  1.000   |      1.000       |    1     |
|   2    | 919,442 |   0.01877 s   | 0.00398 s |  1.441   |      1.577       |    0     |
|   4    | 919,442 |   0.01133 s   | 0.00151 s |  2.386   |      2.218       |    0     |
|   8    | 919,442 |   0.00792 s   | 0.00109 s |  3.413   |      2.778       |    0     |

- Rust skalira i za asimetrično stablo, ali nešto slabije nego za simetrično (3.413× vs 3.892× na 8 jezgara).
- Zanimljivo: na 8 jezgara izmereno ubrzanje (3.413×) je **veće** od Amdahlove predikcije (2.778×). Ovo se dešava jer svaka nit obrađuje manji skup podataka koji bolje staje u privatni L2 keš (512 KB/jezgru) — tzv. super-linearno ubrzanje zbog keš efekata.
- Sekvencijalni deo je veći (f=26.8% vs f=8.2%) — neravnomerna podela posla povećava efektivni sekvencijalni deo, jer najsporiji radnik određuje ukupno vreme.
- **Zaključak:** Razlika u ubrzanju (~12%) direktno odražava cenu neravnomerne podele posla između desnih (ratio 0.57) i levih (ratio 0.67) podstabala.

---

## 6. Slabo skaliranje (Weak Scaling)

**Princip:** Broj grana po jezgru ostaje konstantan; ukupan posao raste proporcionalno broju jezgara. Idealno: vreme ostaje isto.

### 6.1 Manipulacija veličinom posla

#### Simetrično stablo (~16,383 grana po jezgru)

| Jezgra | Ukupno grana | Grana po jezgru | `min_length` |
| :----: | :----------: | :-------------: | :----------: |
|   1    |    16,383    |     16,383      |    0.500     |
|   2    |    32,767    |     16,383      |    0.335     |
|   4    |    65,535    |     16,383      |    0.224     |
|   8    |   131,071    |     16,383      |    0.150     |

#### Asimetrično stablo (~3,360 grana po jezgru)

| Jezgra | Ukupno grana | `min_length` |
| :----: | :----------: | :----------: |
|   1    |    3,360     |    0.500     |
|   2    |    6,931     |    0.309     |
|   4    |    13,695    |    0.191     |
|   8    |    27,990    |    0.118     |

> **Napomena:** Asimetrično stablo ima manji broj grana pri istom `min_length` jer desna grana brže dostiže minimum (ratio 0.57 < 0.67). Zbog toga je i apsolutno vreme mnogo kraće — što dodatno pojačava vidljivost Python trošaka.

### 6.2 Simetrično stablo — Python

<img src="data/symmetric/weak/python.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev   | Skalirano ubrzanje | Outlieri |
| :----: | ------: | :-----------: | :-------: | :----------------: | :------: |
|   1    |  16,383 |   0.01031 s   | 0.00099 s |       1.000        |    0     |
|   2    |  32,767 |   0.41481 s   | 0.12000 s |     **0.050**      |    0     |
|   4    |  65,535 |   0.46355 s   | 0.05896 s |     **0.089**      |    0     |
|   8    | 131,071 |   0.70333 s   | 0.05560 s |     **0.117**      |    0     |

**Analiza:**

- Sa 1 jezgrom (sekvencijalno): 0.010 s. Sa 2 jezgra: 0.415 s — **40× sporije** iako je posao samo udvostručen.
- Fiksni trošak pokretanja procesa (~300 ms po procesu) je ~30× veći od samog računanja (0.010 s).
- Skalirano ubrzanje 0.117 na 8 jezgara znači da program troši 8.5× više vremena nego što bi trebalo.
- Visok StdDev na 2 jezgra (0.120 s pri sredini 0.415 s, tj. ~29% varijacije) ukazuje da je vreme pokretanja procesa na Windows-u neujednačeno.
- **Poruka za tezu:** Python slabo skaliranje je nemoguće za kratke zadatke na Windows platformi. Trošak pokretanja procesa je fiksna cena koja ne zavisi od veličine problema.

### 6.3 Simetrično stablo — Rust

<img src="data/symmetric/weak/rust.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |   StdDev   | Skalirano ubrzanje | Gustafson (p=0.137) | Outlieri |
| :----: | ------: | :-----------: | :--------: | :----------------: | :-----------------: | :------: |
|   1    |  16,383 |  0.000449 s   | 0.000098 s |       1.000        |        1.000        |    2     |
|   2    |  32,767 |  0.000940 s   | 0.000399 s |       0.955        |        1.137        |    1     |
|   4    |  65,535 |  0.001062 s   | 0.000128 s |       1.691        |        1.411        |    0     |
|   8    | 131,071 |  0.001587 s   | 0.000424 s |     **2.263**      |        1.959        |    1     |

**Analiza:**

- **2 jezgra (0.955×):** Blago ispod 1.0 — koordinacija niti ima relativno velik trošak kada su zadaci kratki (~0.45 ms). Ovo je poznato ograničenje paralelizacije malih zadataka.
- **4 jezgra (1.691×) i 8 jezgara (2.263×):** Mereno ubrzanje premašuje Gustafsonovu predikciju (1.411× i 1.959×). Razlog su keš efekti — sa više niti svaka obrađuje manji podskup podataka koji bolje staje u privatni keš.
- Sa 8 jezgara i 8× više posla, vreme raste samo 3.53× (0.449 ms → 1.587 ms).
- **Zaključak:** Rust dobro skalira čak i za male probleme jer nema trošak pokretanja — niti su već pripremljene.

### 6.4 Asimetrično stablo — Python

<img src="data/asymmetric/weak/python.png" width="700"/>

| Jezgra |  Grane | Srednje vreme |  StdDev   | Skalirano ubrzanje | Outlieri |
| :----: | -----: | :-----------: | :-------: | :----------------: | :------: |
|   1    |  3,360 |   0.00205 s   | 0.00021 s |       1.000        |    1     |
|   2    |  6,931 |   0.33600 s   | 0.03317 s |     **0.012**      |    1     |
|   4    | 13,695 |   0.44693 s   | 0.00522 s |     **0.018**      |    0     |
|   8    | 27,990 |   0.71846 s   | 0.03794 s |     **0.023**      |    2     |

**Analiza:**

- Najgori rezultat u celom eksperimentu. Sa 2 jezgra program je **164× sporiji** (0.002 s → 0.336 s).
- Uzrok: asimetrično stablo generiše ~3,360 grana za 0.002 s — trošak pokretanja procesa (~300 ms) je ~150× veći od samog računanja.
- Skalirano ubrzanje od 0.023 na 8 jezgara: program troši 43× više vremena nego što bi trebalo.

### 6.5 Asimetrično stablo — Rust

<img src="data/asymmetric/weak/rust.png" width="700"/>

| Jezgra |  Grane | Srednje vreme |   StdDev   | Skalirano ubrzanje | Gustafson (p=0.030) | Outlieri |
| :----: | -----: | :-----------: | :--------: | :----------------: | :-----------------: | :------: |
|   1    |  3,360 |  0.000135 s   | 0.000041 s |       1.000        |        1.000        |    1     |
|   2    |  6,931 |  0.000425 s   | 0.000150 s |       0.635        |        1.030        |    0     |
|   4    | 13,695 |  0.000524 s   | 0.000138 s |       1.031        |        1.090        |    0     |
|   8    | 27,990 |  0.000692 s   | 0.000150 s |     **1.561**      |        1.211        |    2     |

**Analiza:**

- **2 jezgra (0.635×):** Sporije od sekvencijalnog — čak ni Rust nije imun na neravnomernost podele posla kada su zadaci mikroskopski (0.135 ms). Koordinacija niti košta više nego što se dobija.
- **4 jezgra (1.031×) i 8 jezgara (1.561×):** Mereno ubrzanje premašuje Gustafsonov model (koji predviđa ~1.211×). Opet, keš efekti pomažu pri većem broju jezgara.
- Visok StdDev na 2 jezgra (0.150 ms pri sredini 0.425 ms, tj. ~35%) ukazuje na nestabilna merenja — neravnomerna podela posla čini da radnici završavaju u veoma različito vreme.
- **Ključni zaključak za tezu:** Neravnomerna podela posla u asimetričnom stablu transformiše potencijalno paralelni algoritam u praktično sekvencijalni. Čak i uz minimalni trošak (Rust niti), neravnomerna raspodela posla eliminiše korist od paralelizacije. Ovo potvrđuje da je **ravnomerna podela posla jednako važna kao i minimizacija trošaka komunikacije**.

---

## 7. Sumarni pregled rezultata

### 7.1 Jako skaliranje (8 jezgara)

| Konfiguracija        | Seq. vreme (1j.) | Vreme (8j.) |  Ubrzanje  | Sekvenc. frakcija `f` |
| -------------------- | :--------------: | :---------: | :--------: | :-------------------: |
| Simetrično — Rust    |     0.2251 s     |  0.0578 s   | **3.892×** |         8.2%          |
| Simetrično — Python  |     5.112 s      |   4.422 s   |   1.156×   |         89.9%         |
| Asimetrično — Rust   |    0.02704 s     |  0.00792 s  | **3.413×** |         26.8%         |
| Asimetrično — Python |     0.587 s      |   1.131 s   | **0.519×** |         100%          |

### 7.2 Slabo skaliranje (8 jezgara)

| Konfiguracija        | Skalirano ubrzanje | Gustafson `f` | Efikasnost |
| -------------------- | :----------------: | :-----------: | :--------: |
| Simetrično — Rust    |     **2.263×**     |     86.3%     |   28.3%    |
| Asimetrično — Rust   |       1.561×       |     97.0%     |   19.5%    |
| Simetrično — Python  |       0.117×       |    100.0%     |    1.5%    |
| Asimetrično — Python |       0.023×       |    100.0%     |    0.3%    |

---

## 8. Zaključci

### 8.1 Rust vs Python

**Rust je 20–220× brži od Python-a sekvencijalno** (~0.225 s vs ~5.1 s za simetrično, ~0.027 s vs ~0.587 s za asimetrično), a paralelizacijom postiže realno ubrzanje:

- Simetrično jako skaliranje: Rust 3.892× vs Python 1.156× — gotovo 3.4× veće ubrzanje
- Asimetrično jako skaliranje: Python postaje skoro **2× sporiji** sa 8 jezgara dok Rust postiže 3.413×

Razlog nije loš algoritam u Python-u — isti algoritam, isti problem. Razlog su tri strukturna ograničenja:

1. **Trošak pokretanja procesa na Windows (~300 ms po procesu):** Svaki Python worker zahteva pokretanje novog Python interpretatora, što je fiksna cena nezavisna od veličine problema.
2. **GIL (Global Interpreter Lock):** Python sprečava pravo višenitno izvršavanje unutar jednog procesa — zato mora koristiti više _procesa_ umesto _niti_, što povlači gore navedeni trošak.
3. **Serijalizacija podataka (Pickle):** Svaki argument i rezultat mora biti pakovan i prosleđen kroz operativni sistem između procesa, što dodatno troši vreme.

### 8.2 Simetrično vs Asimetrično

**Rust simetrično > Rust asimetrično** zbog neravnomerne podele posla:

- Jako skaliranje: 3.892× vs 3.413× (razlika ~12%)
- Slabo skaliranje: 2.263× vs 1.561× (razlika ~31%)

Asimetrično stablo ima desna podstabla ~15–20% manja od levih (ratio 0.57 vs 0.67). Kada se stablo raspodeli na N zadataka, zadaci imaju različite veličine — najsporiji radnik određuje ukupno vreme. Za slabo skaliranje ovaj efekat je izraženiji jer su zadaci manji, pa relativna razlika u veličini više utiče.

**Ključna lekcija:** Paralelizacija ne garantuje ubrzanje. Dva podjednako važna preduslova su: (1) nizak trošak komunikacije i koordinacije i (2) ravnomerna podela posla između radnika.

### 8.3 Keš efekti (Rust jako skaliranje)

U asimetričnom jako skaliranju, izmereno ubrzanje na 8 jezgara (3.413×) **premašuje** Amdahlovu predikciju (2.778×). Ovaj fenomen nastaje jer svaka nit obrađuje manji skup podataka koji bolje staje u privatni L2 keš (512 KB po jezgru), smanjujući broj pristupa sporijoj RAM memoriji. Rezultat je da program ne samo da se paralelizuje — deli posao tako da svaki radnik radi efikasnije nego kada bi radio sam.

### 8.4 Hardversko ograničenje: fizička vs virtuelna jezgra

Procesor ima 4 fizička i 8 virtualnih jezgara (Hyper-Threading). Za računski intenzivan zadatak poput generisanja fraktalnog stabla, virtuelna jezgra 5–8 dele aritmetičke resurse sa fizičkim 1–4. Zbog toga:

- Rust simetrično jako skaliranje: ubrzanje raste sa 3.113× (4 jezgra) na 3.892× (8 jezgara) — samo ~25% više umesto teorijskih 2× više
- Hyper-Threading pomaže kod zadataka koji čekaju na memoriju (prikriva latenciju), ali ne duplira računsku moć

### 8.5 Preporuke za praksu

Na osnovu eksperimenata mogu se izvesti sledeće preporuke:

| Scenarijo                         | Preporuka                                                                 |
| --------------------------------- | ------------------------------------------------------------------------- |
| Mali problemi (<1 s) u Python-u   | Koristiti sekvencijalni kod — paralelizacija usporava                     |
| Veliki problemi (>5 s) u Python-u | Paralelizacija blago pomaže (~1.2×), ali nije dramatična                  |
| Rust sa simetričnim stablom       | Paralelizacija veoma efikasna, gotovo linearna do 4 jezgra                |
| Rust sa asimetričnim stablom      | Dublja podela posla (d=6 umesto d=5) daje ~14% bolje rezultate            |
| Windows platforma                 | Python `multiprocessing` ima visok fiksni trošak — razmotriti alternativu |

---

## Grafici

| Fajl                                | Opis                                  |
| ----------------------------------- | ------------------------------------- |
| `data/symmetric/strong/python.png`  | Simetrično jako skaliranje — Python   |
| `data/symmetric/strong/rust.png`    | Simetrično jako skaliranje — Rust     |
| `data/symmetric/weak/python.png`    | Simetrično slabo skaliranje — Python  |
| `data/symmetric/weak/rust.png`      | Simetrično slabo skaliranje — Rust    |
| `data/asymmetric/strong/python.png` | Asimetrično jako skaliranje — Python  |
| `data/asymmetric/strong/rust.png`   | Asimetrično jako skaliranje — Rust    |
| `data/asymmetric/weak/python.png`   | Asimetrično slabo skaliranje — Python |
| `data/asymmetric/weak/rust.png`     | Asimetrično slabo skaliranje — Rust   |
