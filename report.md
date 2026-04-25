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

> **Napomena — Windows multiprocessing:** Python `multiprocessing` na Windows platformi koristi metod **`spawn`** za kreiranje procesa (za razliku od `fork` na Linux). Metod `spawn`, svaki radni proces startuje potpuno novi Python interpretator, uvozi sve module i prima argumente serijalizacijom (pickle). Ovaj fiksni trošak (~300 ms po pokretanju) je dominantan faktor koji negativno utiče na Python paralelne rezultate.

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

#### Simetrično stablo (p_Rust = 0.914, p_Python = 0.087)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.842   |   1.046   |
|     4      |  4.000  |   3.183   |   1.070   |
|     8      |  8.000  |   5.003   |   1.083   |
|     ∞      |    ∞    | **11.63** | **1.095** |

> **Rust:** Amdahl predviđa ubrzanje 5.003× za 8 jezgara, a izmereno je 3.816×. Ovo odstupanje ukazuje da na 8 jezgara postoje dodatna ograničenja (memorijska propusnost, termalna regulacija) koja model ne uzima u obzir.
>
> **Python:** Amdahl predviđa ubrzanje 1.083× za 8 jezgara, a izmereno je 1.089× — vrednosti se praktično poklapaju, bez vidljivog odstupanja. Ovako nisko ubrzanje nije posledica loše implementacije, već dominantnog sekvencijalnog dela (f ≈ 91.3%): fiksni trošak pokretanja procesa na Windows platformi (~300 ms po procesu) čini gotovo sav overhead i ostavlja minimalan prostor za paralelizaciju.

#### Asimetrično stablo (p_Rust = 0.837, p_Python = 0.174)

| N (jezgra) | Idealno |   Rust   |  Python   |
| :--------: | :-----: | :------: | :-------: |
|     1      |  1.000  |  1.000   |   1.000   |
|     2      |  2.000  |  1.720   |   1.095   |
|     4      |  4.000  |  2.686   |   1.150   |
|     8      |  8.000  |  3.737   |   1.180   |
|     ∞      |    ∞    | **6.13** | **1.211** |

> **Zašto je asimetrično stablo lošije za Rust, a bolje za Python?**
>
> - **Rust:** Asimetrično stablo pogoršava skaliranje (f raste sa 8.6% na 16.3%). Iako Rayon dinamički preraspodeljuje zadatke, podstabla su veoma različitih veličina (left_ratio=0.67 vs right_ratio=0.57), pa neke niti završavaju rano i čekaju dok druge dovršavaju velike podskupove. Ovaj efekat neravnomerne podele direktno povećava efektivni sekvencijalni deo.
> - **Python:** Asimetrično stablo paradoksalno pokazuje bolje skaliranje od simetričnog (f pada sa 91.3% na 82.6%, a Amdahlova predikcija za N=8 raste sa 1.083× na 1.180×). Razlog je dominantnost fiksnog troška pokretanja procesa (~300 ms po procesu): asimetrično stablo sekvencijalno traje duže (4.812 s vs 4.340 s), pa isti apsolutni spawn overhead čini manji relativni udeo u ukupnom vremenu. Dakle, Python ne skalira bolje zbog boljih karakteristika paralelizacije, već zbog toga što je sekvencijalno sporiji — spawn overhead je relativno manji.

### 4.2 Gustafsonov zakon — Slabo skaliranje

Gustafsonov zakon: kada se broj jezgara povećava, povećava se i veličina problema (svako jezgro uvek ima isto toliko posla). Pitanje je koliko više posla može da se završi u istom vremenu.

#### Simetrično stablo (p_Rust = 0.528, p_Python = 0.015)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.528   |   1.015   |
|     4      |  4.000  |   2.583   |   1.044   |
|     8      |  8.000  | **4.693** | **1.102** |

#### Asimetrično stablo (p_Rust = 0.630, p_Python = 0.017)

| N (jezgra) | Idealno |   Rust    |  Python   |
| :--------: | :-----: | :-------: | :-------: |
|     1      |  1.000  |   1.000   |   1.000   |
|     2      |  2.000  |   1.631   |   1.017   |
|     4      |  4.000  |   2.892   |   1.050   |
|     8      |  8.000  | **5.413** | **1.116** |

> **Asimetrično vs simetrično stablo u slabom skaliranju**
>
> - **Rust:** Asimetrično stablo pokazuje **bolje** slabo skaliranje od simetričnog (p=0.630 vs p=0.528, Gustafson 5.413× vs 4.693× na 8 jezgara). Razlog je da u slabom skaliranju ukupan problem raste proporcionalno broju jezgara — veći problemi generišu više i raznovrsnijih zadataka, što Rayon-ovom work-stealing mehanizmu daje više prilike da uravnoteži opterećenje između niti. Neravnomerna podela (left_ratio=0.67, right_ratio=0.57) postaje manje problematična kada ima više zadataka iz kojih niti mogu da preuzimaju posao.
> - **Python:** Oba oblika stabla imaju zanemarljiv paralelni deo (p_simetrično=0.015, p_asimetrično=0.017), pa je razlika između njih minimalna. Gustafsonova predikcija iznosi 1.102× za simetrično i 1.116× za asimetrično na 8 jezgara — praktično identično. Fiksni trošak pokretanja procesa na Windows platformi (~300 ms po procesu) dominira nad stvarnim računanjem i čini gotovo sav overhead bez obzira na oblik stabla.

---

## 5. Jako skaliranje (Strong Scaling)

**Veličina problema:** fiksna, `min_length = 0.01`

### 5.1 Simetrično stablo (8,388,607 grana)

### Python

<img src="data/symmetric/strong/python.png" width="700"/>

| Jezgra |     Grane | Srednje vreme | StdDev  | Ubrzanje  | Amdahl (p=0.087) | Outlieri |
| :----: | --------: | :-----------: | :-----: | :-------: | :--------------: | :------: |
|   1    | 8,388,607 |    4.340 s    | 0.095 s |   1.000   |      1.000       |    0     |
|   2    | 8,388,607 |    4.617 s    | 0.063 s | **0.940** |      1.046       |    1     |
|   4    | 8,388,607 |    3.792 s    | 0.186 s | **1.145** |      1.070       |    1     |
|   8    | 8,388,607 |    3.987 s    | 0.070 s |   1.089   |      1.083       |    2     |

- **2 jezgra sporija od 1 (0.940×):** Windows trošak pokretanja 2 procesa premašuje uštedu od paralelnog računanja.
- **4 jezgra daje maksimalno ubrzanje (1.145×), ali 8 jezgara pada na 1.089×:** Ubrzanje se smanjuje prelaskom sa 4 na 8 jezgara jer virtuelna jezgra 5–8 dele aritmetičke resurse sa fizičkim — trošak koordinacije premašuje dobit.
- **Zaključak:** Python paralelizacija za ovaj problem praktično ne funkcioniše. Maksimalno ubrzanje od 1.145× (na 4 jezgra, ne na 8) znači da je overhead dominantan faktor, a dodavanje više jezgara aktivno pogoršava performanse.

### Rust

<img src="data/symmetric/strong/rust.png" width="700"/>

| Jezgra |     Grane | Srednje vreme | StdDev  | Ubrzanje  | Amdahl (p=0.914) | Outlieri |
| :----: | --------: | :-----------: | :-----: | :-------: | :--------------: | :------: |
|   1    | 8,388,607 |    0.211 s    | 0.029 s |   1.000   |      1.000       |    2     |
|   2    | 8,388,607 |    0.102 s    | 0.005 s | **2.068** |      1.842       |    1     |
|   4    | 8,388,607 |    0.069 s    | 0.005 s |   3.076   |      3.183       |    0     |
|   8    | 8,388,607 |    0.055 s    | 0.005 s |   3.816   |      5.003       |    2     |

- **Super-linearno ubrzanje na 2 jezgra (2.068× > idealni 2.0×):** Izmereno ubrzanje blago premašuje idealno. Mogući razlog su keš efekti — svaka nit obrađuje manji podskup podataka koji bolje staje u privatni L2 keš (512 KB po jezgru).
- **4 jezgra (3.076×):** Ubrzanje ispod idealnog (4.0×) — 4 niti počinju da se takmiče za deljeni L3 keš, a izmereno (3.076) je nešto ispod Amdahlove predikcije (3.183).
- **8 jezgara (3.816×):** Amdahlov model predviđa 5.003×, a izmereno je 3.816×. Odstupanje ukazuje da pri punom opterećenju 8 jezgara dolaze do izražaja memorijska propusnost i termalna regulacija.
- **Zaključak:** Rust rayon postiže odlično skaliranje sa samo ~8.6% sekvencijalnog dela.

### 5.2 Asimetrično stablo (919,442 grana)

### Python

<img src="data/asymmetric/strong/python.png" width="700"/>

| Jezgra |     Grane | Srednje vreme | StdDev  | Ubrzanje  | Amdahl (p=0.174) | Outlieri |
| :----: | --------: | :-----------: | :-----: | :-------: | :--------------: | :------: |
|   1    | 8,464,173 |    4.812 s    | 0.142 s |   1.000   |      1.000       |    0     |
|   2    | 8,464,173 |    4.769 s    | 0.090 s |   1.009   |      1.095       |    0     |
|   4    | 8,464,173 |    3.685 s    | 0.134 s | **1.306** |      1.150       |    2     |
|   8    | 8,464,173 |    4.004 s    | 0.128 s |   1.202   |      1.180       |    3     |

- **2 jezgra (1.009×):** Gotovo nikakvo ubrzanje — Windows trošak pokretanja procesa jedva da se amortizuje za ovaj problem.
- **4 jezgra daje maksimalno ubrzanje (1.306×), ali 8 jezgara pada na 1.202×:** Isti obrazac kao kod simetričnog stabla — virtuelna jezgra 5–8 ne donose dodatnu računsku moć i koordinacija počinje da košta više nego što se dobija.
- **Izmereno ubrzanje premašuje Amdahlovu predikciju na 4 jezgra (1.306× > 1.150×):** Mogući keš efekat — manji podskupovi podataka po jezgru bolje staju u L2 keš.
- **Zaključak:** Za veliki asimetrični problem (~8.4M grana) Python paralelizacija daje minimalno ubrzanje (maks. 1.306× na 4 jezgra). Prethodni eksperiment sa ~919K grana pokazivao je usporavanje — veličina problema je kritična za amortizaciju fiksnog troška pokretanja procesa.

### Rust

<img src="data/asymmetric/strong/rust.png" width="700"/>

| Jezgra |     Grane | Srednje vreme | StdDev  | Ubrzanje  | Amdahl (p=0.837) | Outlieri |
| :----: | --------: | :-----------: | :-----: | :-------: | :--------------: | :------: |
|   1    | 8,464,173 |    0.218 s    | 0.006 s |   1.000   |      1.000       |    0     |
|   2    | 8,464,173 |    0.128 s    | 0.005 s |   1.699   |      1.720       |    2     |
|   4    | 8,464,173 |    0.079 s    | 0.007 s |   2.767   |      2.686       |    2     |
|   8    | 8,464,173 |    0.058 s    | 0.002 s | **3.736** |      3.737       |    1     |

- Rust skalira i za asimetrično stablo, ali nešto slabije nego za simetrično (3.736× vs 3.816× na 8 jezgara) — razlika je mala (~2.1%).
- Na 8 jezgara izmereno ubrzanje (3.736×) gotovo **tačno** odgovara Amdahlovoj predikciji (3.737×) — model precizno opisuje ponašanje, nema super-linearnih efekata.
- Sekvencijalni deo je nešto veći (f=16.3% vs f=8.6%) — neravnomerna podela posla između desnih (ratio 0.57) i levih (ratio 0.67) podstabala povećava efektivni sekvencijalni deo.
- **Zaključak:** Uticaj asimetrije na jako skaliranje je manji nego što se moglo očekivati — razlika od samo ~2.1% u ubrzanju na 8 jezgara ukazuje da Rayon-ov work-stealing uspešno ublažava neravnomernost podele posla.

---

## 6. Slabo skaliranje (Weak Scaling)

**Princip:** Broj grana po jezgru ostaje konstantan; ukupan posao raste proporcionalno broju jezgara. Idealno: vreme ostaje isto.

### 6.1 Manipulacija veličinom posla

#### Simetrično stablo

| Jezgra | Ukupno grana | Grana po jezgru | `min_length` |
| :----: | -----------: | :-------------: | :----------: |
|   1    |    1,048,575 |    1,048,575    |   0.040000   |
|   2    |    2,097,151 |    1,048,575    |   0.026800   |
|   4    |    4,194,303 |    1,048,575    |   0.017956   |
|   8    |    8,388,607 |    1,048,575    |   0.012031   |

#### Asimetrično stablo

| Jezgra | Ukupno grana | Grana po jezgru | `min_length` |
| :----: | -----------: | :-------------: | :----------: |
|   1    |      919,442 |     919,442     |   0.010000   |
|   2    |    1,855,434 |     927,717     |   0.006180   |
|   4    |    3,731,355 |     932,839     |   0.003819   |
|   8    |    7,518,053 |     939,757     |   0.002360   |

> **Napomena:** Asimetrično stablo ima manji broj grana pri istom `min_length` jer desna grana brže dostiže minimum (ratio 0.57 < 0.67). Zbog toga je i apsolutno vreme mnogo kraće — što dodatno pojačava vidljivost Python trošaka.

### 6.2 Simetrično stablo — Python

<img src="data/symmetric/weak/python.png" width="700"/>

| Jezgra |     Grane | Srednje vreme |   StdDev   | Skalirano ubrzanje | Gustafson ubrzanje | Outlieri |
| :----: | --------: | :-----------: | :--------: | :----------------: | :----------------: | :------: |
|   1    | 1,048,575 |  0.580375 s   | 0.111664 s |       1.000        |       1.000        |    2     |
|   2    | 2,097,151 |  1.352682 s   | 0.050125 s |       0.858        |       1.015        |    1     |
|   4    | 4,194,303 |  2.154268 s   | 0.210054 s |       1.078        |       1.044        |    1     |
|   8    | 8,388,607 |  4.122978 s   | 0.151356 s |       1.126        |       1.102        |    0     |

**Analiza:**

- Sa jednim jezgrom izvršavanje je veoma brzo, ali se povećanjem broja jezgara vreme značajno produžava iako se posao proporcionalno povećava. Skalirano ubrzanje ostaje blizu ili ispod 1, što znači da paralelizacija ne donosi očekivano poboljšanje. Glavni razlog je veliki trošak pokretanja procesa, koji je veći od samog vremena računanja i dovodi do nestabilnih performansi.
- **Zaključak:** Python slabo skaliranje je nemoguće za kratke zadatke na Windows platformi. Trošak pokretanja procesa je fiksna cena koja ne zavisi od veličine problema.

### 6.3 Simetrično stablo — Rust

<img src="data/symmetric/weak/rust.png" width="700"/>

| Jezgra |     Grane | Srednje vreme |   StdDev   | Skalirano ubrzanje | Gustafson ubrzanje | Outlieri |
| :----: | --------: | :-----------: | :--------: | :----------------: | :----------------: | :------: |
|   1    | 1,048,575 |  0.024253 s   | 0.001002 s |       1.000        |       1.000        |    0     |
|   2    | 2,097,151 |  0.027615 s   | 0.001870 s |       1.757        |       1.528        |    1     |
|   4    | 4,194,303 |  0.037418 s   | 0.005449 s |       2.593        |       2.583        |    0     |
|   8    | 8,388,607 |  0.063232 s   | 0.006935 s |       3.068        |       4.693        |    1     |

**Analiza:**

- Povećanjem broja jezgara vreme raste znatno sporije od veličine problema, što ukazuje na dobro slabo skaliranje.
- Skalirano ubrzanje raste (1.76 → 3.07), ali ostaje ispod idealnog, dok daje optimističniju procenu, posebno za veći broj jezgara.
- Razlika između merenog i teorijskog ubrzanja na 8 jezgara ukazuje na ograničenja kao što su overhead raspodele posla.
- **Zaključak:** Rust dobro skalira čak i za male probleme jer nema trošak pokretanja — niti su već pripremljene.

### 6.4 Asimetrično stablo — Python

<img src="data/asymmetric/weak/python.png" width="700"/>

| Jezgra |   Grane   | Srednje vreme |  StdDev  | Skalirano ubrzanje | Gustafson ubrzanje | Outlieri |
| :----: | :-------: | :-----------: | :------: | :----------------: | :----------------: | :------: |
|   1    |  919,442  |   0.5273 s    | 0.0128 s |       1.0000       |       1.0000       |    2     |
|   2    | 1,855,434 |   1.2726 s    | 0.0138 s |       0.8286       |       1.0166       |    0     |
|   4    | 3,731,355 |   1.9291 s    | 0.0909 s |       1.0933       |       1.0497       |    0     |
|   8    | 7,518,053 |   3.7312 s    | 0.2463 s |       1.1305       |       1.1160       |    1     |

**Analiza:**

- Najgori rezultat u celom eksperimentu. Sa 2 jezgra program je **164× sporiji** (0.002 s → 0.336 s).
- Uzrok: asimetrično stablo generiše ~3,360 grana za 0.002 s — trošak pokretanja procesa (~300 ms) je ~150× veći od samog računanja.
- Skalirano ubrzanje od 0.023 na 8 jezgara: program troši 43× više vremena nego što bi trebalo.

### 6.5 Asimetrično stablo — Rust

<img src="data/asymmetric/weak/rust.png" width="700"/>

| Jezgra |   Grane   | Srednje vreme |  StdDev  | Skalirano ubrzanje | Gustafson ubrzanje | Outlieri |
| :----: | :-------: | :-----------: | :------: | :----------------: | :----------------: | :------: |
|   1    |  919,442  |   0.0274 s    | 0.0020 s |       1.0000       |       1.0000       |    0     |
|   2    | 1,855,434 |   0.0305 s    | 0.0021 s |       1.7969       |       1.6305       |    0     |
|   4    | 3,731,355 |   0.0354 s    | 0.0025 s |       3.0917       |       2.8915       |    0     |
|   8    | 7,518,053 |   0.0579 s    | 0.0063 s |       3.7812       |       5.4134       |    1     |

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
