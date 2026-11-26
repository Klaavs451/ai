# Blackjack — Klāvs

Šī ir Klāva darba mape Blackjack bota uzdevumam.

`app.py` palaiž vietējo Blackjack galdu, kur `klavs_bot` spēlē pret
dīleri. Saskarne rāda running/true count, nākamo likmi, rokas punktus un bota
lēmuma pamatojumu. Dzīvajā gājienu žurnālā redzamas atklātās kārtis, dīlera
gājieni un katra raunda iznākums. Apakšējās pogas ļauj sākt vienu raundu,
palaist automātisku 10 roku demonstrāciju, to apturēt vai atiestatīt galdu.

Palaišana no repozitorija saknes:

```powershell
python blackjack\klavs\app.py
```

`bot.py` īsteno pasniedzēja API: `place_bet` un `decide_action`. Bots izmanto
Hi-Lo kāršu skaitīšanu no publiski redzamās vēstures. `game.py` un `app.py`
veido vietējo demonstrāciju ar 4 kavu kopējo kurpi, dīleri un likmēm.

Demonstrācija ir viena bota pret dīleri; pasniedzēja turnīrā boti dalīs vienu
kopēju kurpi un `history` ietvers arī citu botu atklātās kārtis.

Botu un spēles loģikas testi:

```powershell
python -m unittest discover -s blackjack\klavs -p "test_*.py" -v
```
