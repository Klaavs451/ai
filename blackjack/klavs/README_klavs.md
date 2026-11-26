# Blackjack — Klāvs

Šī ir Klāva darba mape Blackjack bota uzdevumam.

`app.py` palaiž vietējo Blackjack galdu, kur `klavs_bot` spēlē pret
dīleri. Saskarne rāda running/true count, nākamo likmi, rokas punktus un bota
lēmuma pamatojumu. Publiskās kurpes audits rāda redzamo kāršu statistiku un
jaukšanas reižu skaitu; statistikas novirze nav pierādījums manipulācijai.
Dzīvajā gājienu žurnālā redzamas atklātās kārtis, dīlera gājieni un raunda
iznākums. Apakšējās pogas ļauj sākt raundu, palaist 10 roku demonstrāciju,
to apturēt vai atiestatīt galdu.

Palaišana no repozitorija saknes:

```powershell
python blackjack\klavs\app.py
```

Visu atrasto Blackjack botu turnīra skats ar dzīvajām botu kamerām un
līdertabulu:

```powershell
python blackjack\tournament.py
```

`bot.py` īsteno pasniedzēja API: `place_bet` un `decide_action`. Bots izmanto
Hi-Lo kāršu skaitīšanu no publiski redzamās vēstures un agresīvu likmju
izkliedi: no 10 līdz 200 žetoniem atkarībā no true count. Pie negatīva vai
zema skaita tas paliek pie minimuma; likmi nepalielina tikai tāpēc, ka zaudēja.
Likme ir ierobežota līdz 10% no pašreizējā bankroll (noapaļota uz leju līdz 10
žetoniem, bet ne zemāk par minimālo likmi), tāpēc tā sarūk līdz ar bankroll.
Neparastas publisko kāršu proporcijas vai neiespējamas kārtis liek botam
samazināt likmi līdz minimumam un izlaist skaita novirzes, dubultošanu un dalīšanu.
Šāds statistikas brīdinājums nav pierādījums manipulācijai vai dīlera rīcībai.
`game.py` un `app.py` veido vietējo demonstrāciju ar 4 kavu kopējo kurpi,
dīleri un likmēm.

Demonstrācija ir viena bota pret dīleri; pasniedzēja turnīrā boti dalīs vienu
kopēju kurpi un `history` ietvers arī citu botu atklātās kārtis.

Botu un spēles loģikas testi:

```powershell
python -m unittest discover -s blackjack\klavs -p "test_*.py" -v
```
