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

> **Napomena o termalnom ograničenju:** Radi se o laptop procesoru sa pasivnim/aktivnim hlađenjem ograničenog kapaciteta. Kod eksperimenata koji dugo traju (posebno Python sa 8 jezgara), moguća je termalna regulacija koja smanjuje takt ispod nominalnog, što može uticati na merene rezultate.

**Memorija:**

| Atribut          | Vrednost                   |
| ---------------- | -------------------------- |
| Ukupan kapacitet | 8 GB                       |
| Tip              | DDR4                       |
| Brzina           | 2667 MHz                   |
| Konfiguracija    | Single-channel (verovatno) |

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

> **Napomena — Windows multiprocessing:** Python `multiprocessing` na Windows platformi koristi metod **`spawn`** za kreiranje procesa (za razliku od `fork` na Linux/macOS). Kod `spawn`-a, svaki radni proces startuje potpuno novi Python interpretator, uvozi sve module i prima argumente serializacijom (pickle). Ovaj overhead (~300 ms po pokretanju) je dominantan faktor koji negativno utiče na Python paralelne rezultate.

**Rust okruženje:**

| Biblioteka/Alat    | Verzija | Uloga                                                                                   |
| ------------------ | ------- | --------------------------------------------------------------------------------------- |
| rustc              | 1.91.0  | Kompajler                                                                               |
| cargo              | 1.91.0  | Build sistem                                                                            |
| rayon              | 1.10    | Automatski raspored zadataka na više CPU jezgara (work-stealing niti)                   |
| serde / serde_json | 1.0     | Serijalizacija JSON izlaza                                                              |

---

## 2. Fiksni parametri svih eksperimenata

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

### 3.1 Identifikacija delova

| Deo koda                        | Tip                        | Opis                                                   |
| ------------------------------- | -------------------------- | ------------------------------------------------------ |
| Generisanje seed grana          | **Sekvencijalni**          | Inicijalna ekspanzija stabla do dubine raspodele posla |
| Generisanje podstabala          | **Paralelni**              | Svako podstablo nezavisno, bez deljenih podataka       |
| Skupljanje i spajanje rezultata | **Sekvencijalni**          | Concatenation rezultujućih vektora                     |
| Kreiranje Pool/ThreadPool       | **Sekvencijalni**          | Jednovremenski overhead pri pokretanju                 |
| IPC / Pickle (samo Python)      | **Sekvencijalni overhead** | Serializacija argumenata i rezultata između procesa    |

### 3.2 Procena sekvencijalne frakcije

Sekvencijalna frakcija `f` procenjena je iz izmerenih podataka koristeći:

- **Amdahlov zakon** (jako skaliranje): `f = (1/S − 1/N) / (1 − 1/N)` gde je `S` izmereno ubrzanje na N jezgara
- **Gustafsonov zakon** (slabo skaliranje): `f = (N − S_scaled) / (N − 1)` gde je `S_scaled = N · T(1) / T(N)`

#### Simetrično stablo — jako skaliranje (8.4M grana)

| Jezik  | Izmereno ubrzanje (8j.) | Sekvencijalni deo `f` | Paralelni deo |
| ------ | :---------------------: | :-------------------: | :-----------: |
| Rust   |         4.083×          |        ~13.7%         |     ~86.3%    |
| Python |         1.048×          |        ~94.8%         |      ~5.2%    |

#### Asimetrično stablo — jako skaliranje (919K grana)

| Jezik  | Izmereno ubrzanje (8j.) | Sekvencijalni deo `f` | Paralelni deo |
| ------ | :---------------------: | :-------------------: | :-----------: |
| Rust   |         3.478×          |        ~18.6%         |     ~81.4%    |
| Python |        **0.483×**       |        ~100%          |      ~0%      |

> **Ključna razlika Python vs Rust:** Sekvencijalni deo algoritma je praktično isti za obe implementacije. Python-ov visoki `f` nije posledica lošeg algoritma — isti sekvenijalni Python kod za 919K grana traje **0.585 s**, a Windows `spawn` overhead po pokretanju iznosi **~300 ms**. Kada se pokrene 8 procesa, taj overhead troši više vremena nego što paralelizacija štedi.

---

## 4. Teorijski Maksimumi Ubrzanja

### 4.1 Amdahlov zakon — Jako skaliranje

#### Simetrično stablo (f\_Rust = 0.137, f\_Python = 0.948)

| N (jezgra) | Idealno |  Rust  | Python |
| :--------: | :-----: | :----: | :----: |
|     1      |  1.000  |  1.000 |  1.000 |
|     2      |  2.000  |  1.759 |  1.027 |
|     4      |  4.000  |  2.835 |  1.041 |
|     8      |  8.000  |  4.082 |  1.048 |
|     ∞      |    ∞    | **7.30** | **1.055** |

#### Asimetrično stablo (f\_Rust = 0.186, f\_Python = 1.0)

| N (jezgra) | Idealno |  Rust  | Python |
| :--------: | :-----: | :----: | :----: |
|     1      |  1.000  |  1.000 |  1.000 |
|     2      |  2.000  |  1.686 |  1.000 |
|     4      |  4.000  |  2.567 |  1.000 |
|     8      |  8.000  |  3.473 |  1.000 |
|     ∞      |    ∞    | **5.38** | **1.000** |

### 4.2 Gustafsonov zakon — Slabo skaliranje

#### Simetrično stablo (f\_Rust = 0.734, f\_Python = 1.0)

| N (jezgra) | Idealno |  Rust  | Python |
| :--------: | :-----: | :----: | :----: |
|     1      |  1.000  |  1.000 |  1.000 |
|     2      |  2.000  |  1.266 |  1.000 |
|     4      |  4.000  |  1.798 |  1.000 |
|     8      |  8.000  |  **2.862** | **1.000** |

#### Asimetrično stablo (f\_Rust = 0.960, f\_Python = 1.0)

| N (jezgra) | Idealno |  Rust  | Python |
| :--------: | :-----: | :----: | :----: |
|     1      |  1.000  |  1.000 |  1.000 |
|     2      |  2.000  |  1.040 |  1.000 |
|     4      |  4.000  |  1.120 |  1.000 |
|     8      |  8.000  |  **1.280** | **1.000** |

> **Ključna razlika simetrično vs asimetrično (Rust):** Gustafsonov `f` za Rust skok sa 0.734 (simetrično) na 0.960 (asimetrično). Uzrok je **neuravnoteženost posla (load imbalance)** — desna grana asimetričnog stabla ima faktor 0.57 naspram 0.67 leve, pa podstabla desno imaju manje grana. Jedan radnik brzo završi sa manjim podstablom i čeka dok drugi radi veće. Taj gubitak vremena u čekanju se ponaša kao sekvencijalni deo.

---

## 5. Analiza dubine raspodele posla (Split Depth)

### 5.1 Definicija i heuristika

Paralelna implementacija najpre sekvencijalno gradi gornje nivoe stabla do dubine `split_depth`, a zatim svako podstablo na toj dubini predaje kao nezavisan zadatak radnom procesu/niti. Korišćena heuristika je:

```
split_depth = max(1, ceil(log2(N * 4)))
```

| N (jezgra) | split_depth (heuristika) |
| :--------: | :----------------------: |
|     1      |            3             |
|     2      |            3             |
|     4      |            4             |
|     8      |            5             |

Pitanje: **da li je ova heuristika optimalna?**

### 5.2 Model troška

Za datu `split_depth = d` i broj jezgara `N`:

- `N_seq = 2^d − 1` (grane izračunate sekvencijalno)
- `N_parallel = N_total − N_seq` (grane u podstablima)
- `T_ideal = N_seq + ⌈N_parallel / N⌉` — savršena raspodela posla
- `T_worst = N_seq + max_task` — najsporiji radnik određuje ukupno vreme

### 5.3 Simetrično stablo — analiza

Simetrično stablo ima **imbalance = 1.0** za svaku dubinu — sva podstabla imaju identičan broj grana. Zbog toga `T_ideal = T_worst` i podela posla je uvek savršena.

| d  | N_seq  | num_tasks | max_task  | imbalance | T_ideal (8j.) | T_worst (8j.) |
|----|-------:|----------:|----------:|:---------:|--------------:|--------------:|
| 1  |      1 |         2 | 4,194,303 |   1.000   |   1,048,577   |   4,194,304   |
| 3  |      7 |         8 | 1,048,575 |   1.000   |   1,048,582   |   1,048,582   |
| **5** |  **31** |    **32** | **262,143** | **1.000** | **1,048,603** | **262,174** |
| 8  |    255 |       256 |    32,767 |   1.000   |   1,048,799   |      33,022   |
| 12 |  4,095 |     4,096 |     2,047 |   1.000   |   1,052,159   |       6,142   |

*(Bold = heuristika za 8 jezgara)*

**Zaključak za simetrično stablo:** T_ideal je minimalan na d=1 i blago raste sa d (zbog sve većeg N_seq). Heuristika d=5 daje T_ideal samo **0.003% lošije** od optimalnog d=1 — razlika je zanemariva. Heuristika je opravdana jer stvara više zadataka nego što ima jezgara (32 zadatka za 8 jezgara), što osigurava dobro iskorišćenje procesora.

### 5.4 Asimetrično stablo — analiza

Asimetrično stablo (r_left=0.67, r_right=0.57) **povećava imbalance sa svakom dubinom** — desna podstabla su sve manja relativno prema levima:

| d  | N_seq | num_tasks | max_task | mean_task | imbalance | T_ideal (8j.) | T_worst (8j.) |
|----|------:|----------:|---------:|----------:|:---------:|--------------:|--------------:|
| 1  |     1 |         2 |  514,906 |  459,720  |   1.120   |     114,932   |     514,907   |
| 3  |     7 |         8 |  161,522 |  114,929  |   1.405   |     114,937   |     161,529   |
| **5** | **31** |    **32** |  **50,350** | **28,731** | **1.752** | **115,826** | **50,381** |
| 6  |    63 |        64 |   27,991 |   14,365  |   1.949   |     114,986   |      28,054   |
| 7  |   127 |       128 |   15,516 |    7,182  |   2.160   |     115,042   |      15,643   |
| **11** | **2,047** | **2,048** | **1,466** | **448** | **3.273** | **116,722** | **3,513** |
| 12 | 4,095 |     4,096 |      822 |      223  |   3.678   |     118,514   |       4,917   |

*(Bold = heuristika d=5 za 8 jezgara; Bold d=11 = optimalni T_worst)*

**Ključni zaključci:**

1. **T_ideal je skoro isti za sve dubine** (114,932 do 118,514 — razlika ~3%) — povećanje N_seq kompenzuje bolja raspodela.
2. **T_worst dramatično opada sa dubinom:** heuristika d=5 daje T_worst=50,381, dok optimalno d=11 daje T_worst=3,513 — to je **14× bolje u najgorem slučaju**.
3. **Imbalance raste eksponencijalno** sa dubinom jer se razlika između levog i desnog podstabla multiplicira na svakom nivou.
4. Heuristika `max(1, ceil(log2(N*4)))` je dizajnirana za simetrična stabla i **ne uzima u obzir load imbalance**. Za asimetrična stabla dublja podela je teorijski bolja.

### 5.5 Empirijska potvrda (Rust, asimetrično, 8 jezgara)

| d  | speedup | efikasnost |
|:--:| :-----: | :--------: |
| 1  |  1.021  |   12.8%    |
| 2  |  1.870  |   23.4%    |
| 3  |  2.685  |   33.6%    |
| 4  |  2.426  |   30.3%    |
| **5** | **2.658** | **33.2%** |
| **6** | **3.020** | **37.8%** |
| 7  |  2.392  |   29.9%    |
| 8  |  2.527  |   31.6%    |
| 9  |  2.133  |   26.7%    |
| 10 |  1.683  |   21.0%    |
| 11 |  2.045  |   25.6%    |
| 12 |  2.046  |   25.6%    |

**d=6 daje empirijski najviše ubrzanje (3.020×)** — jedna dubina dublje od heuristike (d=5 → 2.658×). Ovo je konzistentno sa teorijskim modelom koji pokazuje da veća dubina smanjuje load imbalance.

**Python empirijski:** Svi split_depth-ovi daju speedup < 1 (0.583–0.817×) — spawn overhead potpuno dominira, heuristika nije relevantna.

### 5.6 Zaključak

| Stablo       | Optimalna metrika | Optimalni d (8j.) | Heuristika (d=5) | Razlika  |
| ------------ | :---------------: | :---------------: | :--------------: | :------: |
| Simetrično   | T_ideal           | d=1               | d=5              | ~0.003%  |
| Asimetrično  | T_worst           | d=11              | d=5              | **14×**  |
| Asimetrično  | Empirijski        | d=6               | d=5              | ~14%     |

Heuristika je dobra za simetrična stabla ali suboptimalna za asimetrična. Za produkcijsku upotrebu sa neravnomernim stablima, optimalna `split_depth` bi trebala da zavisi od strukture stabla (odnosa ratia) i da cilja na minimizaciju `max_task`, a ne samo na broj zadataka.

---

## 6. Jako skaliranje (Strong Scaling)

**Veličina problema:** fiksna, `min_length = 0.01`

### 5.1 Simetrično stablo — Python (8,388,607 grana)

<img src="data/symmetric/strong/python.png" width="700"/>

| Jezgra |     Grane |  Srednje vreme | StdDev  | Ubrzanje | Amdahl (f=0.948) | Outlieri |
| :----: | --------: | :------------: | :-----: | :------: | :--------------: | :------: |
|   1    | 8,388,607 |   4.526 s      | 0.221 s |  1.000   |      1.000       |    0     |
|   2    | 8,388,607 |   4.892 s      | 0.210 s | **0.925** |     1.027       |    0     |
|   4    | 8,388,607 |   4.251 s      | 0.472 s |  1.065   |      1.041       |    0     |
|   8    | 8,388,607 |   4.319 s      | 0.166 s |  1.048   |      1.048       |    0     |

**Analiza:**

- **2 jezgra sporija od 1 (0.925×):** Dodavanje drugog procesa donosi neto gubitak. Windows `spawn` overhead za pokretanje 2 procesa (~600 ms ukupno) premašuje uštedu od paralelnog računanja.
- **4 jezgra:** Blago ubrzanje (1.065×) ali visok StdDev (0.472 s) ukazuje na nestabilna merenja, verovatno usled termalnog usporavanja ili OS schedulera.
- **8 jezgara:** Skoro identično sa 4 jezgra (1.048×). Virtuelna jezgra 5–8 dele resurse sa fizičkim i ne donose dodatno ubrzanje.
- **Zaključak:** Python paralelizacija za ovaj problem praktično ne funkcioniše. Maksimalno ubrzanje od 1.065× za 8.4M grana znači da je overhead ~95% efektivnog vremena.

### 5.2 Simetrično stablo — Rust (8,388,607 grana)

<img src="data/symmetric/strong/rust.png" width="700"/>

| Jezgra |     Grane | Srednje vreme |  StdDev  | Ubrzanje | Amdahl (f=0.137) | Outlieri |
| :----: | --------: | :-----------: | :------: | :------: | :--------------: | :------: |
|   1    | 8,388,607 |  0.2223 s     | 0.0299 s |  1.000   |      1.000       |    0     |
|   2    | 8,388,607 |  0.1075 s     | 0.0082 s | **2.068** |     1.759       |    0     |
|   4    | 8,388,607 |  0.0694 s     | 0.0050 s |  3.204   |      2.835       |    0     |
|   8    | 8,388,607 |  0.0545 s     | 0.0035 s | **4.083** |     4.083       |    1     |

**Analiza:**

- **Super-linearno ubrzanje na 2 jezgra (2.068× > idealni 2.0×):** Izmereno ubrzanje premašuje teorijski ideal. Uzrok su **keš efekti** — sa 2 niti svaka obrađuje upola manji skup podataka, koji bolje staje u L2/L3 keš, smanjujući broj cache miss-ova. Ovaj fenomen je poznat kao super-linearno ubrzanje zbog prostorne lokalnosti.
- **4 jezgra (3.204×):** Premašuje Amdahlov maksimum za 2 i 4 jezgra — keš efekat i dalje prisutan.
- **8 jezgara (4.083×):** Ubrzanje veće od 4 fizička jezgra. Virtuelna jezgra pomažu jer dok jedna nit čeka na memoriju, druga izvršava instrukcije na istom fizičkom jezgru (Hyper-Threading). f vrednost procenjena sa 8 jezgara (0.137) važi za ovaj slučaj.
- **Zaključak:** Rust rayon postiže odlično skaliranje. Algoritam ima samo ~13.7% sekvencijalnog dela, teorijski maksimum ~7.3×, ograničen jedino brojem fizičkih jezgara.

### 5.3 Asimetrično stablo — Python (919,442 grane)

<img src="data/asymmetric/strong/python.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev  | Ubrzanje | Outlieri |
| :----: | ------: | :-----------: | :------: | :------: | :------: |
|   1    | 919,442 |   0.585 s     | 0.058 s  |  1.000   |    2     |
|   2    | 919,442 |   0.823 s     | 0.035 s  | **0.710** |   1     |
|   4    | 919,442 |   0.774 s     | 0.028 s  | **0.756** |   1     |
|   8    | 919,442 |   1.210 s     | 0.222 s  | **0.483** |   0     |

**Analiza:**

- Program postaje **sporiji sa svakim dodatnim jezgrom**. Sa 8 jezgara traje 2.07× duže nego sekvencijalno.
- Uzrok: asimetrično stablo ima ~919K grana naspram ~8.4M za simetrično — manje računanja znači da spawn overhead dominira još više. Sa 8 procesa, Windows spawn cost (~2.4 s ukupno) premašuje samo računanje (0.585 s).
- Sekvencijalna frakcija procijenjena na f=1.0 (clamped) jer je mereni "speedup" < 1.
- **Argument za tezu:** Ovo je ekstreman primer gde overhead IPC-a ne samo da poništava dobit od paralelizacije, već aktivno usporava program. Veličina problema mora biti dovoljno velika da amortizuje fiksni overhead.

### 5.4 Asimetrično stablo — Rust (919,442 grane)

<img src="data/asymmetric/strong/rust.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev  | Ubrzanje | Amdahl (f=0.186) | Outlieri |
| :----: | ------: | :-----------: | :------: | :------: | :--------------: | :------: |
|   1    | 919,442 |  0.02481 s    | 0.00128 s |  1.000  |      1.000       |    0     |
|   2    | 919,442 |  0.01690 s    | 0.00304 s |  1.468  |      1.687       |    2     |
|   4    | 919,442 |  0.01012 s    | 0.00227 s |  2.452  |      2.567       |    0     |
|   8    | 919,442 |  0.00713 s    | 0.00071 s |  3.478  |      3.478       |    0     |

**Analiza:**

- Rust skalira i za asimetrično stablo, ali nešto slabije nego za simetrično (3.478× vs 4.083× na 8 jezgara).
- Sekvencijalni deo je malo veći (f=0.186 vs f=0.137) — load imbalance povećava efektivni sekvencijalni deo, jer najsporiji radnik određuje ukupno vreme.
- **Simetrično vs Asimetrično Rust:** Razlika u ubrzanju (~15%) direktno odražava cenu neravnomerne podele posla između podstabala desnog (ratio 0.57) i levog (ratio 0.67) tipa.

---

## 6. Slabo skaliranje (Weak Scaling)

**Princip:** Broj grana po jezgru ostaje konstantan; ukupan posao raste proporcionalno broju jezgara. Idealno: vreme ostaje isto.

### 6.1 Manipulacija veličinom posla

#### Simetrično stablo (16,383 grana po jezgru)

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
|   4    |   13,695     |    0.191     |
|   8    |   27,990     |    0.118     |

> **Napomena:** Asimetrično stablo ima manji broj grana pri istoj dubini jer desna grana brže dostiže `min_length` (ratio 0.57 < 0.67). Zbog toga je i apsolutno vreme mnogo kraće — što dodatno pojačava vidljivost Python spawn overhead-a.

### 6.2 Simetrično stablo — Python

<img src="data/symmetric/weak/python.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev   | Skalirano ubrzanje | Outlieri |
| :----: | ------: | :-----------: | :-------: | :----------------: | :------: |
|   1    |  16,383 |  0.00868 s    | 0.00040 s |       1.000        |    0     |
|   2    |  32,767 |  0.37003 s    | 0.06333 s |     **0.047**      |    2     |
|   4    |  65,535 |  0.48135 s    | 0.04745 s |     **0.072**      |    0     |
|   8    | 131,071 |  0.60351 s    | 0.02954 s |     **0.115**      |    0     |

**Analiza:**

- Sa 1 jezgrom (sekvencijalno): 0.009 s. Sa 2 jezgra: 0.370 s — **42× sporije** iako je posao samo udvostručen.
- Fiksni spawn overhead (~300 ms po procesu) je ~34× veći od samog računanja (0.009 s).
- Skalirano ubrzanje 0.115 na 8 jezgara znači da program troši 8.7× više vremena nego što bi trebalo.
- **Argument za tezu:** Python slabo skaliranje je nemoguće za probleme kraćeg od ~1–2 s po jezgru na Windows platformi. Spawn overhead je fiksna cena koja ne zavisi od veličine problema.

### 6.3 Simetrično stablo — Rust

<img src="data/symmetric/weak/rust.png" width="700"/>

| Jezgra |   Grane | Srednje vreme |  StdDev   | Skalirano ubrzanje | Gustafson (f=0.734) | Outlieri |
| :----: | ------: | :-----------: | :-------: | :----------------: | :-----------------: | :------: |
|   1    |  16,383 |  0.000725 s   | 0.000338 s |       1.000       |        1.000        |    1     |
|   2    |  32,767 |  0.000961 s   | 0.000189 s |       1.509       |        1.266        |    0     |
|   4    |  65,535 |  0.001342 s   | 0.000342 s |       2.161       |        1.799        |    0     |
|   8    | 131,071 |  0.002025 s   | 0.000255 s |     **2.864**     |        2.864        |    1     |

**Analiza:**

- Sa 8 jezgara i 8× više posla, vreme raste samo 2.79× (0.725 ms → 2.025 ms) — efikasnost 35.8%.
- Skalirano ubrzanje (2.864) premašuje Gustafsonov model za 2 i 4 jezgra — ponovo keš efekti pomažu.
- f=0.734: ~73% posla je "efektivno sekvencijalno" za ovaj mali obim zadataka. Koordinacija niti (Rayon work-stealing) ima relativno veći trošak kada su zadaci kratki.
- **Zaključak:** Rust dobro skalira čak i za male probleme jer nema spawn overhead — niti su već pripremljene u thread pool-u.

### 6.4 Asimetrično stablo — Python

<img src="data/asymmetric/weak/python.png" width="700"/>

| Jezgra |  Grane | Srednje vreme |  StdDev   | Skalirano ubrzanje | Outlieri |
| :----: | -----: | :-----------: | :-------: | :----------------: | :------: |
|   1    |  3,360 |  0.00201 s    | 0.00042 s |       1.000        |    0     |
|   2    |  6,931 |  0.32247 s    | 0.02058 s |     **0.012**      |    1     |
|   4    | 13,695 |  0.37601 s    | 0.00625 s |     **0.021**      |    1     |
|   8    | 27,990 |  0.58950 s    | 0.05039 s |     **0.027**      |    0     |

**Analiza:**

- Još katastrofalnije od simetričnog slučaja. Sa 2 jezgra program je **160× sporiji** (0.002 s → 0.322 s).
- Uzrok: asimetrično stablo generiše ~3,360 grana sekvencijalno za 0.002 s — spawn overhead (~300 ms) je ~150× veći od samog računanja.
- Skalirano ubrzanje od 0.027 na 8 jezgara: program troši 37× više vremena nego što bi trebalo.

### 6.5 Asimetrično stablo — Rust

<img src="data/asymmetric/weak/rust.png" width="700"/>

| Jezgra |  Grane | Srednje vreme |   StdDev  | Skalirano ubrzanje | Gustafson (f=0.960) | Outlieri |
| :----: | -----: | :-----------: | :-------: | :----------------: | :-----------------: | :------: |
|   1    |  3,360 |  0.000222 s   | 0.000050 s |       1.000       |        1.000        |    0     |
|   2    |  6,931 |  0.000430 s   | 0.000135 s |       1.033       |        1.040        |    1     |
|   4    | 13,695 |  0.000530 s   | 0.000152 s |       1.676       |        1.121        |    1     |
|   8    | 27,990 |  0.001384 s   | 0.001177 s |     **1.283**     |        1.283        |    2     |

**Analiza:**

- Rust asimetrično slabo skaliranje je znatno lošije od simetričnog (1.283× vs 2.864× na 8 jezgara).
- f=0.960 — gotovo ceo posao se ponaša kao sekvencijalan zbog load imbalance.
- Visok StdDev na 8 jezgara (0.001177 s pri sredini 0.001384 s, tj. ~85% varijacije) ukazuje na nestabilna merenja — radnici završavaju u različito vreme, a najsporiji određuje ukupno vreme.
- **Ključni zaključak za tezu:** Load imbalance u asimetričnom stablu transformiše potencijalno paralelni algoritam u praktično sekvencijalni. Čak i uz nultu overhead (Rust niti), neravnomerna podela posla eliminše korist od paralelizacije. Ovo potvrđuje da je **ravnomerna podela posla jednako važna kao i minimizacija overhead-a**.

---

## 7. Sumarni pregled rezultata

### 7.1 Jako skaliranje (8 jezgara)

| Konfiguracija              | Seq. vreme (1j.) | Vreme (8j.)  | Ubrzanje | Sekvenc. frakcija `f` |
| -------------------------- | :--------------: | :----------: | :------: | :-------------------: |
| Simetrično — Rust          |    0.2223 s      |   0.0545 s   | **4.083×** |       13.7%         |
| Simetrično — Python        |    4.526 s       |   4.319 s    |   1.048× |       94.8%           |
| Asimetrično — Rust         |    0.02481 s     |   0.00713 s  | **3.478×** |       18.6%         |
| Asimetrično — Python       |    0.585 s       |   1.210 s    | **0.483×** |      100%           |

### 7.2 Slabo skaliranje (8 jezgara)

| Konfiguracija              | Skalirano ubrzanje | Gustafson `f` | Efikasnost |
| -------------------------- | :----------------: | :-----------: | :--------: |
| Simetrično — Rust          |      **2.864×**    |     73.4%     |   35.8%    |
| Asimetrično — Rust         |       1.283×       |     96.0%     |   16.0%    |
| Simetrično — Python        |       0.115×       |    100.0%     |    1.4%    |
| Asimetrično — Python       |       0.027×       |    100.0%     |    0.3%    |

---

## 8. Zaključci

### 8.1 Rust vs Python

**Rust je 22–307× brži od Python-a sekvencijalno**, a paralelizacijom postiže realno ubrzanje:

- Simetrično jako skaliranje: Rust 4.083× vs Python 1.048× — razlika faktora ~4 u ubrzanju
- Asimetrično jako skaliranje: Python postaje **2× sporiji** sa 8 jezgara dok Rust postiže 3.478×

Razlog nije loš algoritam u Python-u — isti algoritam, isti problem. Razlog je:
1. **Spawn overhead na Windows:** Svaki Python worker zahteva ~300 ms za pokretanje, nezavisno od veličine problema
2. **GIL (Global Interpreter Lock):** Sprečava pravo višenitno računanje unutar jednog procesa — zbog toga Python mora koristiti više *procesa* umesto *niti*, što povlači spawn overhead
3. **Pickle serializacija:** Svaki argument i rezultat mora biti serializovan kroz pipe između procesa

### 8.2 Simetrično vs Asimetrično

**Rust simetrično > Rust asimetrično** zbog load balancinga:

- Jako skaliranje: 4.083× vs 3.478× (razlika ~15%)
- Slabo skaliranje: 2.864× vs 1.283× (razlika ~55%)

Asimetrično stablo ima desna podstabla ~20% manja od levih (ratio 0.57 vs 0.67). Kada se stablo raspodeli na N zadataka, zadaci imaju različite veličine — najsporiji radnik određuje ukupno vreme (Amdahlov zakon primenjeno na load imbalance). Za slabo skaliranje ovaj efekat je razorniji jer su zadaci manji pa relativna razlika u veličini više utiče.

**Ključna lekcija:** Paralalizacija ne garantuje ubrzanje. Dva podjednako važna preduslova su: (1) nizak overhead komunikacije/koordinacije i (2) ravnomerna podela posla.

### 8.3 Super-linearno ubrzanje (Rust simetrično jako skaliranje)

Na 2 jezgra izmereno ubrzanje je 2.068× — veće od teorijskog ideala od 2.0×. Ovo je poznati fenomen: svaka nit obrađuje manji skup podataka koji bolje staje u privatni L2 keš (512 KB/jezgru), smanjujući broj promašaja kešom. Ovaj efekat nestaje na 4+ jezgara gde L3 keš postaje usko grlo.

### 8.4 Hardversko ograničenje: fizička vs virtuelna jezgra

Procesor ima 4 fizička i 8 virtualnih jezgara (Hyper-Threading). Za računski intenzivan zadatak poput generisanja fraktalnog stabla, virtuelna jezgra 5–8 dele ALU resurse sa fizičkim 1–4. Zbog toga:
- Rust ubrzanje ne raste linearno između 4 i 8 jezgara
- 8 jezgara daje ~27% više ubrzanja od 4 (4.083× vs 3.204×) umesto 2× više

---

## Grafici

Grafici se nalaze u direktorijumu `data/`:

| Fajl                                  | Opis                                           |
| ------------------------------------- | ---------------------------------------------- |
| `data/symmetric/strong/python.png`    | Simetrično jako skaliranje — Python            |
| `data/symmetric/strong/rust.png`      | Simetrično jako skaliranje — Rust              |
| `data/symmetric/weak/python.png`      | Simetrično slabo skaliranje — Python           |
| `data/symmetric/weak/rust.png`        | Simetrično slabo skaliranje — Rust             |
| `data/asymmetric/strong/python.png`   | Asimetrično jako skaliranje — Python           |
| `data/asymmetric/strong/rust.png`     | Asimetrično jako skaliranje — Rust             |
| `data/asymmetric/weak/python.png`     | Asimetrično slabo skaliranje — Python          |
| `data/asymmetric/weak/rust.png`       | Asimetrično slabo skaliranje — Rust            |
