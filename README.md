# La Gesta de Sant Jordi

Joc de navegador a l'estil de Nimble Quest amb llegendes de dracs catalanes i bestiari de festa. Guies una comitiva que avança com una serp: els herois ataquen sols i tu només tries cap on van. Alliberes presoners perquè s'afegeixin a la cua, i les bèsties de festa no es maten: quan se'ls acaba la pólvora, s'uneixen a la comitiva.

**Juga-hi:** https://pmontp19.github.io/gesta-sant-jordi/ (o obre `index.html` en un navegador: no cal servidor ni instal·lar res).

Fletxes o WASD per girar, Espai per aturar, M per al so. Al mòbil, llisca el dit. Per anar directament a un capítol: `index.html#capitol5`.

## Capítols

| | Lloc | Què hi passa |
|---|---|---|
| I | Montblanc | La llegenda clàssica: el sorteig, la princesa i el drac de l'estany |
| II | Sant Celoni | Soler de Vilardell i l'espasa de virtut del captaire |
| III | Sant Llorenç del Munt | La Brívia de la Mola i Santa Jordina |
| IV | Banyoles | El drac que canvia de mida i Sant Mer |
| V | Festa Major | Correfoc amb la Mulassa de Reus, la Cucafera de Tortosa, la Guita Xica de la Patum i el Drac de Vilafranca |
| VI | La Rambla, 23 d'abril | Conte desexplicat: Cervantes, Shakespeare i un drac vegetarià |

## Com està fet

- `index.html`: tot el joc en un sol fitxer (canvas 2D, so i música amb Web Audio, sense dependències).
- `sprites/`: pixel art de 32×32 px (64×64 per a les bèsties i els dracs grans). Si un sprite no carrega, el joc fa servir els dibuixos de 16×16 que porta dins.
- `art/`: com es generen els sprites.
  - `prompts.json`: el prompt de cada sprite.
  - `gen.mjs`: crida Codex (`gpt-5.6-luna`, eina `image_gen`) amb fons magenta.
  - `pixelate.py`: passa la imatge a una graella real de píxels amb una paleta de 24 colors.
  - `images.json`: amb quin model, quan i amb quin prompt s'ha fet cada imatge.

```sh
node art/gen.mjs mulassa      # regenera un sprite (cal esborrar abans art/raw/mulassa.png)
python3 art/pixelate.py guita --big   # torna a pixelar un original ja descarregat
```

Les imatges originals (`art/raw/`) no són al repositori.
