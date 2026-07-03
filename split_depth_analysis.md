# Analiza dubine raspodele posla (Split Depth)

---

## 1. Definicija i heuristika

Paralelna implementacija najpre sekvencijalno gradi gornje nivoe stabla do dubine `split_depth`, a zatim svako podstablo na toj dubini predaje kao nezavisan zadatak radnom procesu/niti. Korišćena heuristika je:

```
split_depth = floor(log2(N * 4))
```

| N (jezgra) | split_depth (heuristika) |
| :--------: | :----------------------: |
|     2      |            3             |
|     4      |            4             |
|     8      |            5             |

Faktor 4 zasnovan je na principu prekomerne raspodele zadataka (oversubscription): generiše se višestruko više zadataka nego što ima raspoloživih jezgara, čime se obezbeđuje da jezgra koja završe ranije odmah preuzmu nove zadatke.

---

## 2. Eksperiment

**Cilj:** utvrditi da li je heuristika empirijski opravdana za asimetrično stablo i zašto Python ne profitira od promene `split_depth`.

**Parametri eksperimenta:**

| Parametar      | Vrednost         |
| -------------- | ---------------- |
| Stablo         | Asimetrično      |
| `left_ratio`   | 0.67             |
| `right_ratio`  | 0.57             |
| `min_length`   | 0.0023           |
| Broj grana     | 8,464,173        |
| N (jezgra)     | 8                |
| `split_depth`  | 1 – 12           |
| Ponavljanja    | 3 (Rust: 5)      |

Sekvencijalno vreme meri se jednom pre petlje i koristi kao imenilac za sve vrednosti ubrzanja.

---

## 3. Rezultati

### Rust

| d     | num_tasks | par_mean (s) |  speedup | efikasnost | napomena     |
| :---: | --------: | -----------: | -------: | :--------: | ------------ |
|   1   |         2 |      0.17867 |   1.52×  |   19.0%    |              |
|   2   |         4 |      0.14682 |   1.85×  |   23.2%    |              |
|   3   |         8 |      0.09858 |   2.76×  |   34.5%    |              |
|   4   |        16 |      0.08201 |   3.32×  |   41.5%    |              |
| **5** |    **32** |  **0.06972** | **3.90×** | **48.8%** | **heuristika** |
|   6   |        64 |      0.06870 |   3.96×  |   49.5%    |              |
|   7   |       128 |      0.07011 |   3.88×  |   48.5%    |              |
| **8** |   **256** |  **0.06367** | **4.27×** | **53.4%** | **empirijski optimum** |
|   9   |       512 |      0.06452 |   4.22×  |   52.7%    |              |
|  10   |     1,024 |      0.07051 |   3.86×  |   48.2%    |              |
|  11   |     2,048 |      0.08572 |   3.18×  |   39.7%    |              |
|  12   |     4,096 |      0.10556 |   2.58×  |   32.2%    |              |

### Python

| d     | num_tasks | par_mean (s) |  speedup | efikasnost | napomena       |
| :---: | --------: | -----------: | -------: | :--------: | -------------- |
|   1   |         2 |      6.86945 |   1.15×  |   14.4%    |                |
|   2   |         4 |      4.89451 |   1.62×  |   20.2%    |                |
|   3   |         8 |      4.33892 |   1.83×  |   22.8%    |                |
|   4   |        16 |      4.27542 |   1.85×  |   23.2%    |                |
| **5** |    **32** |  **4.38104** | **1.81×** | **22.6%** | **heuristika** |
|   6   |        64 |      4.38993 |   1.81×  |   22.6%    |                |
|   7   |       128 |      4.42893 |   1.79×  |   22.4%    |                |
|   8   |       256 |      4.46664 |   1.77×  |   22.2%    |                |
|   9   |       512 |      4.58765 |   1.73×  |   21.6%    |                |
|  10   |     1,024 |      5.01738 |   1.58×  |   19.8%    |                |
|  11   |     2,048 |      4.72614 |   1.68×  |   21.0%    |                |
|  12   |     4,096 |      4.76309 |   1.66×  |   20.8%    |                |

---

## 4. Analiza

### Rust

Ubrzanje raste od d=1 do d=8, a zatim opada. Empirijski optimum je **d=8 (4.27×)**. Heuristika d=5 daje **3.90×** — razlika od ~9.5%.

Pad ubrzanja za d≥9 nastaje jer sekvencijalna faza postaje prevelika: pri d=8 sekvencijalno se obrađuje 255 gornjih grana, pri d=9 već 511, itd. Za asimetrično stablo, leva i desna podstabla na istoj dubini nisu jednake veličine (`r_left ≠ r_right`), pa heuristika obezbeđuje više zadataka nego što ima jezgara — Rayon-ov algoritam krađe posla dinamički raspoređuje neujednačena opterećenja.

Razlika od ~9.5% između d=5 i d=8 postoji, ali nije uvek vredna komplikacije: pri d=8 sekvencijalna faza je 8× veća (255 vs 31 grana), a empirijska dobit zavisi od konkretne strukture stabla i hardvera.

### Python

Kriva je praktično ravna za d≥3 (raspon 1.58–1.85×). Trošak pokretanja novih procesa i pickle serijalizacije dominira nad neravnomernošću zadataka — bez obzira na to koliko zadataka postoji, svaki mora da se serijalizuje pre slanja i deserijalizuje po povratku. Zbog toga vrednost `split_depth` nema praktičnog uticaja za Python multiprocessing.

---

## 5. Zaključak

| Implementacija | Empirijski optimum | Heuristika (d=5) | Razlika |
| -------------- | :----------------: | :--------------: | :-----: |
| Rust           |       d=8 (4.27×)  |    d=5 (3.90×)   |  ~9.5%  |
| Python         |       d=4 (1.85×)  |    d=5 (1.81×)   |  ~2.2%  |

Heuristika `floor(log2(N*4))` je praktičan izbor: automatski se prilagođava broju jezgara, drži sekvencijalnu fazu u razumnim granicama i daje rezultate bliske empirijskom optimumu za obe implementacije.
