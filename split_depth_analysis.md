# Analiza dubine raspodele posla (Split Depth)

---

## 1. Definicija i heuristika

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

---

## 2. Model troška

Za datu `split_depth = d` i broj jezgara `N`:

- `N_seq = 2^d − 1` — grane izračunate sekvencijalno (pre podele posla)
- `N_parallel = N_total − N_seq` — grane u podstablima (paralelni deo)
- `T_ideal = N_seq + ⌈N_parallel / N⌉` — savršena podela posla
- `T_dynamic` — simulacija dinamičkog raspoređivanja (LPT): radnik koji završi zadatak odmah uzima sledeći

---

## 3. Simetrično stablo — analiza

Simetrično stablo ima **imbalance = 1.0** za svaku dubinu — sva podstabla imaju identičan broj grana. Zbog toga je podela posla uvek savršena.

| d     |  N_seq | num_tasks |    max_task | imbalance | T_ideal (8j.) | T_dynamic (8j.) |
| ----- | -----: | --------: | ----------: | :-------: | ------------: | --------------: |
| 1     |      1 |         2 |   4,194,303 |   1.000   |     1,048,577 |       4,194,304 |
| 3     |      7 |         8 |   1,048,575 |   1.000   |     1,048,582 |       1,048,582 |
| **5** | **31** |    **32** | **262,143** | **1.000** | **1,048,603** |     **262,174** |
| 8     |    255 |       256 |      32,767 |   1.000   |     1,048,799 |          33,022 |
| 12    |  4,095 |     4,096 |       2,047 |   1.000   |     1,052,159 |           6,142 |

_(Bold = heuristika za 8 jezgara)_

**Zaključak:** T_ideal je minimalan na d=1 i blago raste sa d (zbog sve većeg sekvencijalnog dela). Heuristika d=5 daje T_ideal samo **0.003% lošije** od optimalnog d=1 — razlika je zanemariva. Heuristika je opravdana jer stvara više zadataka nego što ima jezgara (32 zadatka za 8 jezgara), što osigurava dobro iskorišćenje procesora.

---

## 4. Asimetrično stablo — analiza

Asimetrično stablo (r_left=0.67, r_right=0.57) **povećava neravnomernost sa svakom dubinom** — desna podstabla su sve manja relativno prema levima:

| d      |     N_seq | num_tasks |   max_task |  mean_task | imbalance | T_ideal (8j.) | T_dynamic (8j.) |
| ------ | --------: | --------: | ---------: | ---------: | :-------: | ------------: | --------------: |
| 1      |         1 |         2 |    514,906 |    459,720 |   1.120   |       114,932 |         514,907 |
| 3      |         7 |         8 |    161,522 |    114,929 |   1.405   |       114,937 |         161,529 |
| **5**  |    **31** |    **32** | **50,350** | **28,731** | **1.752** |   **115,826** |      **50,381** |
| 6      |        63 |        64 |     27,991 |     14,365 |   1.949   |       114,986 |          28,054 |
| 7      |       127 |       128 |     15,516 |      7,182 |   2.160   |       115,042 |          15,643 |
| **11** | **2,047** | **2,048** |  **1,466** |    **448** | **3.273** |   **116,722** |       **3,513** |
| 12     |     4,095 |     4,096 |        822 |        223 |   3.678   |       118,514 |           4,917 |

_(Bold d=5 = heuristika; bold d=11 = optimalni T_dynamic za 8 jezgara)_

**Ključni zaključci:**

1. **T_ideal je skoro isti za sve dubine** (114,932 do 118,514 — razlika ~3%) — povećanje sekvencijalnog dela kompenzuje bolja podela posla.
2. **T_dynamic dramatično opada sa dubinom:** heuristika d=5 daje T_dynamic=50,381, dok optimalno d=11 daje T_dynamic=3,513 — to je **14× bolje u realnom scenariju**.
3. **Neravnomernost raste eksponencijalno** sa dubinom jer se razlika između levog i desnog podstabla multiplicira na svakom nivou.
4. Heuristika `max(1, ceil(log2(N*4)))` je projektovana za simetrična stabla i **ne uzima u obzir neravnomernost podele posla**. Za asimetrična stabla, dublja podela je teorijski bolja.

---

## 5. Empirijska potvrda (Rust, asimetrično, 8 jezgara)

|   d   |  speedup  | efikasnost |
| :---: | :-------: | :--------: |
|   1   |   1.021   |   12.8%    |
|   2   |   1.870   |   23.4%    |
|   3   |   2.685   |   33.6%    |
|   4   |   2.426   |   30.3%    |
| **5** | **2.658** | **33.2%**  |
| **6** | **3.020** | **37.8%**  |
|   7   |   2.392   |   29.9%    |
|   8   |   2.527   |   31.6%    |
|   9   |   2.133   |   26.7%    |
|  10   |   1.683   |   21.0%    |
|  11   |   2.045   |   25.6%    |
|  12   |   2.046   |   25.6%    |

**d=6 daje empirijski najviše ubrzanje (3.020×)** — jedna dubina dublje od heuristike (d=5 → 2.658×). Ovo je konzistentno sa teorijskim modelom koji pokazuje da veća dubina smanjuje neravnomernost podele posla.

**Python empirijski:** Svi split_depth-ovi daju ubrzanje < 1 (0.583–0.817×) — trošak pokretanja novih procesa potpuno dominira, heuristika nije relevantna.

---

## 6. Zaključak

| Stablo      | Optimalna metrika | Optimalni d (8j.) | Heuristika (d=5) | Razlika |
| ----------- | :---------------: | :---------------: | :--------------: | :-----: |
| Simetrično  |      T_ideal      |        d=1        |       d=5        | ~0.003% |
| Asimetrično |     T_dynamic     |       d=11        |       d=5        | **14×** |
| Asimetrično |    Empirijski     |        d=6        |       d=5        |  ~14%   |

Heuristika je dobra za simetrična stabla ali suboptimalna za asimetrična. Za produkcionu upotrebu sa neravnomernim stablima, optimalna `split_depth` bi trebala da zavisi od strukture stabla (odnosa ratia) i da cilja na minimizaciju `max_task`.
