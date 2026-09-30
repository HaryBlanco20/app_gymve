# Créditos de imágenes y datos de ejercicios

## Ilustraciones de ejercicios — Everkinetic (CC BY-SA 4.0)

- Fuente: [github.com/everkinetic/data](https://github.com/everkinetic/data), commit
  `446bb9a3d0c3beb6b84f7c9d77dfc8af707a2ab6`. Proyecto de datos abiertos basado en
  everkinetic.com, creado por Greg Priday.
- Licencia: [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/).
- Archivos: `app/static/exercises/everkinetic/<id>-relaxation.png` (posición inicial) y
  `<id>-tension.png` (posición final), **sin modificar**. Si se editan, la versión derivada debe
  publicarse bajo CC BY-SA 4.0.
- Atribución visible en la app: pie de la ficha de cada ejercicio (`/app/exercises/{id}`).
- Para volver a descargarlas: `python scripts/fetch_exercise_images.py`.

## Iconos de grupo muscular — originales GymVe

`app/static/exercises/groups/*.svg` son dibujos propios de GymVe. Se usan cuando no hay una
ilustración Everkinetic equivalente (máquinas de palanca con discos, pec deck, hip thrust,
cardio, etc.).

## Textos del catálogo

Nombres, descripciones e instrucciones en `app/exercise_catalog.py` son redacción original
de GymVe en español.

## Qué NO se usa

- **Imágenes de free-exercise-db** (yuhonas/free-exercise-db): su origen no está claro y
  parte parece venir de ExRx. Solo su JSON (Unlicense) sería utilizable como referencia; hoy
  GymVe no lo incluye.
- **Capturas o renders de la app Fitness Online**: son propiedad de sus autores; solo se
  usaron como referencia de experiencia de uso.

## Marcas de máquinas

Las máquinas del catálogo (`machines`) guardan el **tipo** como base y `brand` / `model`
como campos opcionales. La marca se siembra como «Nautilus (probable)» para fuerza y
«Star Trac (probable)» para cardio, según evidencia indirecta. La usuaria la confirma desde
«Mi gym». GymVe no está afiliada a Nautilus, Star Trac ni Fitness 24 Seven.
