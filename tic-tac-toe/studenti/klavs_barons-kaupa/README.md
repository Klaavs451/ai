# Klāva botu versijas

- `bot.py` ir aktīvais bots, ko ielādē sacensību programma.
- `versions/bot_v1.py` ir saglabāta pirmā versija. To nemaina, lai varētu
  nākamo versiju pārbaudīt pret veco.

## Spēlēšana un salīdzināšana

No repozitorija mapes palaid:

```powershell
python .\11.uzdevums.py
```

Izvēlies pretinieka līmeni un nospied **Botu savstarpējā cīņa**. Nākamajā
mačā sākuma loma samainās, lai abi boti varētu sākt.

## Nākamās versijas veidošana

Uzlabo `bot.py`, nomaini `BOT_NAME` uz `Klāvs v2` un palaid:

```powershell
python .\11.uzdevums.py --test
```

Pēc tam izvēlies saglabāto **Klāvs v1** pretinieku un pārbaudi, vai jaunā
versija uzvar. Sacensībām tiek iesniegts tikai aktīvais `bot.py`; versiju
arhīvs paredzēts salīdzināšanai.

IQ 1 un IQ 2 ir spēles grūtības līmeņi, nevis īsts IQ mērījums.
