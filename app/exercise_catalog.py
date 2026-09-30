"""Catálogo base GymVe: tipos de máquina, ejercicios y los 5 días del plan.

Textos originales en español. Las ilustraciones `ek` provienen de Everkinetic
(CC BY-SA 4.0, ver docs/creditos-imagenes.md); sin `ek` se usa el icono propio
del grupo muscular.
"""

from app.models import EquipmentType as E

MUSCLE_GROUPS: dict[str, str] = {
    "pectoral": "Pectoral",
    "espalda": "Espalda",
    "hombro": "Hombro",
    "triceps": "Tríceps",
    "biceps": "Bíceps",
    "piernas": "Piernas",
    "gluteos": "Glúteos",
    "cardio": "Cardio",
}

EQUIPMENT_LABELS: dict[str, str] = {
    "machine": "Máquinas",
    "cable": "Poleas",
    "smith": "Máquina Smith",
    "dumbbell": "Mancuernas y banco",
    "cardio": "Cardio",
}

EQUIPMENT_ICONS: dict[str, str] = {
    "machine": "ti-device-desktop",
    "cable": "ti-arrows-vertical",
    "smith": "ti-building-arch",
    "dumbbell": "ti-barbell",
    "cardio": "ti-run",
}

BRAND_STATUS_LABELS: dict[str, str] = {
    "unknown": "Sin confirmar",
    "probable": "probable",
    "confirmed": "confirmada",
}

EVERKINETIC_CREDIT = "everkinetic"

# slug, nombre neutro, categoría, marca, estado de la marca
MACHINES: list[tuple[str, str, E, str | None, str]] = [
    ("leg_press", "Prensa de piernas", E.machine, "Nautilus", "probable"),
    ("leg_extension", "Extensión de cuádriceps", E.machine, "Nautilus", "probable"),
    ("seated_leg_curl", "Curl femoral sentado", E.machine, "Nautilus", "probable"),
    ("lying_leg_curl", "Curl femoral acostado", E.machine, "Nautilus", "probable"),
    ("hip_abductor", "Abductor de cadera", E.machine, "Nautilus", "probable"),
    ("hip_adductor", "Aductor de cadera", E.machine, "Nautilus", "probable"),
    ("hack_squat", "Hack squat", E.machine, "Nautilus", "probable"),
    ("seated_calf", "Gemelos sentado", E.machine, "Nautilus", "probable"),
    ("chest_press", "Press de pecho selectorizado", E.machine, "Nautilus", "probable"),
    ("chest_press_plate", "Press de pecho con palanca (discos)", E.machine, "Nautilus", "probable"),
    (
        "incline_press_plate",
        "Press inclinado con palanca (discos)",
        E.machine,
        "Nautilus",
        "probable",
    ),
    ("pec_deck", "Pec fly / deltoide posterior", E.machine, "Nautilus", "probable"),
    ("shoulder_press", "Press de hombro", E.machine, "Nautilus", "probable"),
    ("pulldown_plate", "Jalón frontal con palanca (discos)", E.machine, "Nautilus", "probable"),
    ("row_plate", "Remo con palanca (discos)", E.machine, "Nautilus", "probable"),
    ("biceps_curl_machine", "Curl de bíceps en máquina", E.machine, "Nautilus", "probable"),
    ("triceps_machine", "Extensión de tríceps en máquina", E.machine, "Nautilus", "probable"),
    ("dip_machine", "Fondos asistidos / en máquina", E.machine, "Nautilus", "probable"),
    ("lat_pulldown", "Jalón en polea alta", E.cable, "Nautilus", "probable"),
    ("low_row", "Remo bajo sentado en polea", E.cable, "Nautilus", "probable"),
    ("cable_crossover", "Cruce de poleas", E.cable, "Nautilus", "probable"),
    ("smith", "Máquina Smith", E.smith, "Nautilus", "probable"),
    ("adjustable_bench", "Banco ajustable y mancuernas", E.dumbbell, None, "unknown"),
    ("treadmill", "Cinta de correr", E.cardio, "Star Trac", "probable"),
    ("elliptical", "Elíptica", E.cardio, "Star Trac", "probable"),
    ("stationary_bike", "Bicicleta estática", E.cardio, "Star Trac", "probable"),
]


def _ex(
    slug: str,
    name: str,
    eq: E,
    machine: str | None,
    group: str,
    primary: str,
    secondary: str,
    ek: str | None,
    description: str,
    steps: list[str],
) -> dict:
    return {
        "slug": slug,
        "name": name,
        "equipment_type": eq,
        "machine_slug": machine,
        "muscle_group": group,
        "primary_muscles": primary,
        "secondary_muscles": secondary,
        "ek_id": ek,
        "description": description,
        "instructions": "\n".join(steps),
    }


EXERCISES: list[dict] = [
    # ---------------------------------------------------------------- piernas
    _ex(
        "prensa-inclinada", "Prensa de piernas", E.machine, "leg_press", "piernas",
        "Cuádriceps", "Glúteo mayor, isquiotibiales, aductores", "0127",
        "Ejercicio guiado para cargar las piernas con la espalda apoyada. Permite mover "
        "mucho peso con poco riesgo para la zona lumbar.",
        [
            "Siéntate con la espalda y la cadera pegadas al respaldo.",
            "Apoya los pies en la plataforma a la anchura de la cadera.",
            "Quita los seguros y baja hasta que las rodillas formen unos 90°.",
            "Empuja con todo el pie sin bloquear las rodillas arriba.",
        ],
    ),
    _ex(
        "extension-cuadriceps", "Extensión de cuádriceps", E.machine, "leg_extension",
        "piernas", "Cuádriceps", "", "0142",
        "Aísla la parte frontal del muslo. Útil al inicio para calentar la rodilla o al "
        "final para terminar de fatigar el cuádriceps.",
        [
            "Ajusta el respaldo para que la rodilla quede alineada con el eje de la máquina.",
            "Coloca el rodillo justo encima del tobillo.",
            "Extiende las piernas hasta casi estirarlas y aprieta un segundo.",
            "Baja despacio sin dejar caer el peso.",
        ],
    ),
    _ex(
        "curl-femoral-sentado", "Curl femoral sentado", E.machine, "seated_leg_curl",
        "piernas", "Isquiotibiales", "Gemelos", "0119",
        "Trabaja la parte posterior del muslo con la cadera flexionada, lo que alarga el "
        "isquiotibial y aumenta el rango útil.",
        [
            "Ajusta el respaldo y baja el rodillo superior sobre los muslos.",
            "Apoya el rodillo inferior detrás de los tobillos.",
            "Flexiona las rodillas llevando los talones hacia abajo y atrás.",
            "Vuelve controlando, sin que la placa de peso choque.",
        ],
    ),
    _ex(
        "curl-femoral-acostado", "Curl femoral acostado", E.machine, "lying_leg_curl",
        "piernas", "Isquiotibiales", "Gemelos, glúteos", "0117",
        "Versión boca abajo del curl femoral. Mantener la cadera pegada al banco es la "
        "clave para que trabaje el femoral y no la zona lumbar.",
        [
            "Acuéstate boca abajo con las rodillas justo fuera del banco.",
            "Coloca el rodillo sobre los tobillos y sujeta las manijas.",
            "Lleva los talones hacia los glúteos sin despegar la cadera.",
            "Baja lentamente hasta casi estirar las piernas.",
        ],
    ),
    _ex(
        "abduccion-cadera-maquina", "Abducción de cadera en máquina", E.machine,
        "hip_abductor", "gluteos", "Glúteo medio", "Glúteo menor, tensor de la fascia lata",
        "0156",
        "Separar las piernas contra resistencia fortalece la parte lateral del glúteo, "
        "importante para estabilizar la rodilla y la cadera.",
        [
            "Siéntate con la espalda apoyada y las almohadillas por fuera de las rodillas.",
            "Abre las piernas en un movimiento continuo.",
            "Haz una pausa breve con las piernas abiertas.",
            "Cierra despacio resistiendo el peso.",
        ],
    ),
    _ex(
        "aduccion-cadera-maquina", "Aducción de cadera en máquina", E.machine,
        "hip_adductor", "piernas", "Aductores", "Pectíneo, grácil", "0157",
        "Trabaja la cara interna del muslo. Complementa la abducción para mantener el "
        "equilibrio de la cadera.",
        [
            "Siéntate con las almohadillas por dentro de las rodillas.",
            "Elige una apertura inicial cómoda, sin forzar.",
            "Junta las piernas apretando los aductores.",
            "Regresa lentamente a la apertura inicial.",
        ],
    ),
    _ex(
        "gemelos-prensa", "Gemelos en prensa", E.machine, "leg_press", "piernas",
        "Gemelos", "Sóleo", "0273",
        "Aprovecha la prensa para trabajar la pantorrilla con carga alta y la espalda "
        "apoyada.",
        [
            "Siéntate en la prensa con las piernas casi estiradas.",
            "Apoya solo la parte delantera de los pies en el borde inferior de la plataforma.",
            "Empuja con la punta de los pies hasta subir los talones al máximo.",
            "Baja los talones despacio para estirar la pantorrilla.",
        ],
    ),
    _ex(
        "gemelos-sentado", "Gemelos sentado en máquina", E.machine, "seated_calf",
        "piernas", "Sóleo", "Gemelos", "0279",
        "Con la rodilla flexionada el trabajo recae más en el sóleo, el músculo profundo "
        "de la pantorrilla.",
        [
            "Siéntate y coloca la almohadilla sobre la parte baja de los muslos.",
            "Apoya la parte delantera de los pies en el escalón.",
            "Sube los talones todo lo posible y aguanta un segundo.",
            "Baja lentamente hasta sentir el estiramiento.",
        ],
    ),
    _ex(
        "hack-squat", "Hack squat en máquina", E.machine, "hack_squat", "piernas",
        "Cuádriceps", "Glúteo mayor, aductores", "0123",
        "Sentadilla guiada con la espalda apoyada en un respaldo inclinado. Enfatiza el "
        "cuádriceps con buena estabilidad.",
        [
            "Apoya la espalda y los hombros en las almohadillas.",
            "Coloca los pies en el centro de la plataforma a la anchura de los hombros.",
            "Libera los seguros y baja hasta que los muslos queden paralelos a la plataforma.",
            "Sube empujando con todo el pie.",
        ],
    ),
    _ex(
        "sentadilla-smith", "Sentadilla en máquina Smith", E.smith, "smith", "piernas",
        "Cuádriceps", "Glúteo mayor, isquiotibiales, core", "0124",
        "La barra guiada permite concentrarse en la profundidad y la postura sin "
        "preocuparse por el equilibrio.",
        [
            "Coloca la barra sobre la parte alta de la espalda, no sobre el cuello.",
            "Adelanta ligeramente los pies respecto a la barra.",
            "Gira la barra para liberarla y baja con el pecho alto.",
            "Sube empujando el suelo y vuelve a trabar la barra al terminar.",
        ],
    ),
    _ex(
        "sentadilla-goblet", "Sentadilla goblet con mancuerna", E.dumbbell,
        "adjustable_bench", "piernas", "Cuádriceps", "Glúteo mayor, core", None,
        "Sostener una mancuerna frente al pecho ayuda a mantener el torso erguido y a "
        "bajar con buena técnica.",
        [
            "Sujeta una mancuerna vertical con ambas manos a la altura del pecho.",
            "Separa los pies algo más que la anchura de la cadera.",
            "Baja entre las piernas manteniendo los codos por dentro de las rodillas.",
            "Sube sin redondear la espalda.",
        ],
    ),
    _ex(
        "zancadas-mancuernas", "Zancadas con mancuernas", E.dumbbell, "adjustable_bench",
        "piernas", "Cuádriceps", "Glúteo mayor, isquiotibiales", "0115",
        "Ejercicio unilateral que trabaja fuerza y equilibrio. Corrige diferencias entre "
        "una pierna y otra.",
        [
            "De pie, con una mancuerna en cada mano a los costados.",
            "Da un paso largo hacia delante.",
            "Baja hasta que la rodilla de atrás casi toque el suelo.",
            "Empuja con la pierna de delante para volver y alterna.",
        ],
    ),
    _ex(
        "peso-muerto-rumano-mancuernas", "Peso muerto rumano con mancuernas", E.dumbbell,
        "adjustable_bench", "gluteos", "Isquiotibiales, glúteo mayor",
        "Erectores de la columna, antebrazos", "0107",
        "Bisagra de cadera que estira y fortalece la cadena posterior. La espalda se "
        "mantiene neutra durante todo el recorrido.",
        [
            "De pie, con las mancuernas delante de los muslos.",
            "Flexiona un poco las rodillas y mantenlas así.",
            "Lleva la cadera hacia atrás bajando las mancuernas cerca de las piernas.",
            "Sube apretando los glúteos al llegar arriba.",
        ],
    ),
    _ex(
        "peso-muerto-smith", "Peso muerto en máquina Smith", E.smith, "smith", "gluteos",
        "Glúteo mayor, isquiotibiales", "Erectores de la columna", "0100",
        "La barra guiada ayuda a aprender el patrón de bisagra con una trayectoria fija.",
        [
            "Colócate con la barra pegada a las espinillas.",
            "Sujeta la barra con las manos a la anchura de los hombros.",
            "Sube extendiendo cadera y rodillas a la vez, con la espalda recta.",
            "Baja llevando la cadera hacia atrás.",
        ],
    ),
    # ---------------------------------------------------------------- glúteos
    _ex(
        "hip-thrust-smith", "Hip thrust en máquina Smith", E.smith, "smith", "gluteos",
        "Glúteo mayor", "Isquiotibiales, core", None,
        "Empuje de cadera con la espalda apoyada en un banco. Es de los ejercicios que "
        "más activa el glúteo mayor.",
        [
            "Apoya la parte alta de la espalda en un banco perpendicular a la Smith.",
            "Coloca la barra, con almohadilla, sobre la cadera.",
            "Empuja con los talones hasta alinear rodillas, cadera y hombros.",
            "Aprieta arriba un segundo y baja controlando.",
        ],
    ),
    _ex(
        "patada-gluteo-polea", "Patada de glúteo en polea", E.cable, "cable_crossover",
        "gluteos", "Glúteo mayor", "Isquiotibiales", "0112",
        "Extensión de cadera unilateral con tensión constante gracias a la polea.",
        [
            "Coloca la tobillera en la polea baja y sujétate de la estructura.",
            "Inclina un poco el torso y mantén el core firme.",
            "Lleva la pierna hacia atrás sin arquear la espalda.",
            "Vuelve despacio y completa las repeticiones antes de cambiar de pierna.",
        ],
    ),
    _ex(
        "sentadilla-sumo-mancuerna", "Sentadilla sumo con mancuerna", E.dumbbell,
        "adjustable_bench", "gluteos", "Glúteo mayor, aductores", "Cuádriceps", "0152",
        "Con los pies muy abiertos y las puntas hacia fuera, el trabajo se desplaza "
        "hacia glúteos y aductores.",
        [
            "Separa los pies bastante más que los hombros, puntas hacia fuera.",
            "Sujeta una mancuerna con ambas manos entre las piernas.",
            "Baja con el torso erguido y las rodillas en la dirección de los pies.",
            "Sube apretando glúteos.",
        ],
    ),
    # ---------------------------------------------------------------- pectoral
    _ex(
        "press-pecho-maquina", "Press de pecho en máquina", E.machine, "chest_press",
        "pectoral", "Pectoral mayor", "Tríceps, deltoide anterior", "0066",
        "Empuje horizontal guiado. Buena opción para mover carga con seguridad sin "
        "necesitar compañero.",
        [
            "Ajusta el asiento para que las manijas queden a la altura del pecho.",
            "Apoya la espalda y junta ligeramente los omóplatos.",
            "Empuja hasta casi estirar los brazos.",
            "Regresa despacio hasta sentir el estiramiento del pecho.",
        ],
    ),
    _ex(
        "press-pecho-palanca", "Press de pecho con palanca (discos)", E.machine,
        "chest_press_plate", "pectoral", "Pectoral mayor", "Tríceps, deltoide anterior",
        None,
        "Máquina de palanca con discos y brazos independientes. Permite trabajar cada "
        "lado por separado y corregir desequilibrios.",
        [
            "Ajusta el asiento para que las manijas queden a media altura del pecho.",
            "Carga los discos de forma pareja en ambos brazos.",
            "Empuja con ambos brazos o de uno en uno.",
            "Controla la vuelta sin dejar que los discos golpeen.",
        ],
    ),
    _ex(
        "press-inclinado-palanca", "Press inclinado con palanca (discos)", E.machine,
        "incline_press_plate", "pectoral", "Pectoral mayor (porción superior)",
        "Deltoide anterior, tríceps", None,
        "Empuje en ángulo ascendente que enfatiza la parte alta del pecho.",
        [
            "Ajusta el asiento para que las manijas salgan a la altura de la clavícula.",
            "Apoya bien la espalda y los pies.",
            "Empuja hacia arriba y ligeramente al frente.",
            "Baja despacio con los codos a unos 45° del torso.",
        ],
    ),
    _ex(
        "aperturas-pec-deck", "Aperturas en pec deck", E.machine, "pec_deck", "pectoral",
        "Pectoral mayor", "Deltoide anterior", None,
        "Movimiento de aducción que aísla el pecho: juntar los brazos frente al cuerpo "
        "es su función principal.",
        [
            "Ajusta el asiento para que los brazos queden a la altura del pecho.",
            "Sujeta las manijas o apoya los antebrazos en las almohadillas.",
            "Junta los brazos al frente sin encoger los hombros.",
            "Abre despacio hasta sentir estiramiento, sin pasar de la línea de los hombros.",
        ],
    ),
    _ex(
        "press-banca-smith", "Press de banca en máquina Smith", E.smith, "smith",
        "pectoral", "Pectoral mayor", "Tríceps, deltoide anterior", "0078",
        "Press de banca con barra guiada. Muy similar al clásico, pero más estable para "
        "entrenar sin ayudante.",
        [
            "Acuéstate en un banco plano con la barra sobre la mitad del pecho.",
            "Sujeta la barra un poco más abierta que los hombros y libérala.",
            "Baja hasta rozar el pecho con los codos a unos 45°.",
            "Empuja hacia arriba y vuelve a trabar la barra al terminar.",
        ],
    ),
    _ex(
        "press-inclinado-smith", "Press inclinado en máquina Smith", E.smith, "smith",
        "pectoral", "Pectoral mayor (porción superior)", "Deltoide anterior, tríceps", "0081",
        "Con el banco a 30–45° el empuje se concentra en la parte alta del pecho.",
        [
            "Coloca el banco inclinado bajo la barra.",
            "La barra debe bajar hacia la parte alta del pecho.",
            "Libera la barra y baja controlando.",
            "Empuja sin despegar la espalda del banco.",
        ],
    ),
    _ex(
        "press-inclinado-mancuernas", "Press inclinado con mancuernas", E.dumbbell,
        "adjustable_bench", "pectoral", "Pectoral mayor (porción superior)",
        "Deltoide anterior, tríceps", "0080",
        "Las mancuernas dan más rango de movimiento que la barra y obligan a cada brazo "
        "a trabajar por su cuenta.",
        [
            "Ajusta el respaldo del banco entre 30° y 45°.",
            "Sube las mancuernas apoyándolas en los muslos al recostarte.",
            "Empuja hacia arriba juntándolas ligeramente al final.",
            "Baja hasta que los codos queden un poco por debajo del banco.",
        ],
    ),
    _ex(
        "aperturas-inclinadas-mancuernas", "Aperturas inclinadas con mancuernas",
        E.dumbbell, "adjustable_bench", "pectoral", "Pectoral mayor (porción superior)",
        "Deltoide anterior", "0062",
        "Ejercicio de aislamiento para el pecho alto con estiramiento amplio.",
        [
            "Recuéstate en el banco inclinado con las mancuernas arriba y palmas enfrentadas.",
            "Flexiona un poco los codos y mantenlos así.",
            "Abre los brazos en arco hasta sentir el estiramiento.",
            "Cierra el arco apretando el pecho.",
        ],
    ),
    _ex(
        "cruce-poleas", "Cruce de poleas", E.cable, "cable_crossover", "pectoral",
        "Pectoral mayor", "Deltoide anterior, serrato", "0048",
        "La polea mantiene tensión en todo el recorrido. Cambiando la altura de las "
        "poleas se enfatiza la parte alta, media o baja del pecho.",
        [
            "Coloca las poleas a la altura deseada y sujeta una manija en cada mano.",
            "Da un paso al frente con un pie adelantado para estabilizarte.",
            "Junta las manos frente al pecho con los codos semiflexionados.",
            "Vuelve despacio controlando el peso.",
        ],
    ),
    # ---------------------------------------------------------------- hombro
    _ex(
        "press-hombro-maquina", "Press de hombro en máquina", E.machine, "shoulder_press",
        "hombro", "Deltoide anterior y medio", "Tríceps, trapecio", None,
        "Empuje vertical guiado para los hombros sin cargar tanto la zona lumbar.",
        [
            "Ajusta el asiento para que las manijas queden a la altura de los hombros.",
            "Apoya la espalda completa en el respaldo.",
            "Empuja hacia arriba sin bloquear los codos.",
            "Baja hasta que las manos queden cerca de las orejas.",
        ],
    ),
    _ex(
        "vuelo-posterior-maquina", "Vuelo posterior en máquina", E.machine, "pec_deck",
        "hombro", "Deltoide posterior", "Romboides, trapecio medio", None,
        "Usa la máquina de pec fly al revés para trabajar la parte trasera del hombro, "
        "clave para una buena postura.",
        [
            "Siéntate mirando hacia el respaldo con el pecho apoyado.",
            "Sujeta las manijas con los brazos al frente, a la altura de los hombros.",
            "Abre los brazos hacia atrás sin encoger los hombros.",
            "Vuelve despacio al frente.",
        ],
    ),
    _ex(
        "elevaciones-laterales-mancuernas", "Elevaciones laterales con mancuernas",
        E.dumbbell, "adjustable_bench", "hombro", "Deltoide medio", "Trapecio", "0018",
        "El ejercicio más directo para dar anchura al hombro. Se hace con poco peso y "
        "mucho control.",
        [
            "De pie, con una mancuerna en cada mano a los costados.",
            "Con los codos un poco flexionados, sube los brazos hacia los lados.",
            "Detente cuando las manos lleguen a la altura de los hombros.",
            "Baja lentamente sin balancear el cuerpo.",
        ],
    ),
    _ex(
        "elevacion-frontal-mancuernas", "Elevación frontal con mancuernas", E.dumbbell,
        "adjustable_bench", "hombro", "Deltoide anterior", "Pectoral mayor (porción superior)",
        "0033",
        "Aísla la parte delantera del hombro. Puede hacerse alternando brazos.",
        [
            "De pie, con las mancuernas delante de los muslos.",
            "Sube un brazo al frente hasta la altura de los hombros.",
            "Baja despacio y repite con el otro brazo.",
            "Mantén el torso quieto durante todo el movimiento.",
        ],
    ),
    # ---------------------------------------------------------------- espalda
    _ex(
        "jalon-polea-agarre-ancho", "Jalón al pecho con agarre ancho", E.cable,
        "lat_pulldown", "espalda", "Dorsal ancho", "Bíceps, redondo mayor, romboides", None,
        "Ejercicio base para la anchura de la espalda. Se tira de la barra hacia el pecho "
        "llevando los codos hacia abajo.",
        [
            "Ajusta el rodillo para que sujete bien los muslos.",
            "Toma la barra con las manos más abiertas que los hombros.",
            "Inclínate un poco atrás y lleva la barra a la parte alta del pecho.",
            "Sube controlando hasta estirar los brazos.",
        ],
    ),
    _ex(
        "jalon-agarre-v", "Jalón con agarre en V", E.cable, "lat_pulldown", "espalda",
        "Dorsal ancho", "Bíceps, romboides", "0096",
        "El agarre neutro y cerrado permite un recorrido largo y suele ser cómodo para "
        "los hombros.",
        [
            "Engancha el agarre en V a la polea alta.",
            "Siéntate con los muslos bajo el rodillo.",
            "Tira hacia el pecho sacando el pecho hacia delante.",
            "Estira los brazos por completo al subir.",
        ],
    ),
    _ex(
        "jalon-palanca", "Jalón frontal con palanca (discos)", E.machine, "pulldown_plate",
        "espalda", "Dorsal ancho", "Redondo mayor, trapecio, romboides", None,
        "Versión de palanca del jalón, con brazos independientes. Permite trabajar un "
        "lado cada vez.",
        [
            "Ajusta el asiento y el rodillo de los muslos.",
            "Sujeta las manijas con los brazos estirados.",
            "Lleva los codos hacia abajo y atrás.",
            "Sube despacio hasta sentir el estiramiento del dorsal.",
        ],
    ),
    _ex(
        "remo-sentado-polea", "Remo sentado en polea", E.cable, "low_row", "espalda",
        "Dorsal ancho, romboides", "Bíceps, deltoide posterior, trapecio", "0025",
        "Tirón horizontal que da grosor a la espalda media.",
        [
            "Siéntate con los pies en los apoyos y las rodillas algo flexionadas.",
            "Sujeta el agarre con la espalda recta.",
            "Lleva el agarre hacia el abdomen juntando los omóplatos.",
            "Estira los brazos sin redondear la espalda.",
        ],
    ),
    _ex(
        "remo-unilateral-polea", "Remo a un brazo en polea", E.cable, "low_row", "espalda",
        "Dorsal ancho", "Romboides, bíceps", None,
        "La variante unilateral aumenta el recorrido y ayuda a equilibrar ambos lados.",
        [
            "Engancha una manija en D a la polea baja.",
            "Siéntate y sujeta la manija con una mano.",
            "Tira llevando el codo hacia atrás, cerca del cuerpo.",
            "Estira el brazo dejando que el hombro avance un poco.",
        ],
    ),
    _ex(
        "remo-smith-prono", "Remo en máquina Smith con agarre prono", E.smith, "smith",
        "espalda", "Dorsal ancho, romboides", "Deltoide posterior, bíceps", "0022",
        "Remo inclinado con barra guiada. El agarre prono involucra más la espalda alta.",
        [
            "Coloca la barra a la altura de las rodillas.",
            "Inclina el torso con la espalda recta y sujeta la barra con las palmas hacia ti.",
            "Lleva la barra hacia el abdomen.",
            "Baja controlando sin perder la postura.",
        ],
    ),
    _ex(
        "remo-palanca", "Remo con palanca (discos)", E.machine, "row_plate", "espalda",
        "Dorsal ancho, romboides", "Bíceps, deltoide posterior", None,
        "Remo con el pecho apoyado, lo que libera la zona lumbar y permite cargar más.",
        [
            "Apoya el pecho en la almohadilla.",
            "Sujeta las manijas con los brazos estirados.",
            "Tira llevando los codos hacia atrás.",
            "Vuelve despacio a la posición inicial.",
        ],
    ),
    _ex(
        "pulldown-brazos-rectos", "Pulldown con brazos rectos", E.cable, "lat_pulldown",
        "espalda", "Dorsal ancho", "Tríceps (cabeza larga), redondo mayor", "0092",
        "Aísla el dorsal sin que el bíceps participe. Buen ejercicio de activación.",
        [
            "De pie frente a la polea alta, sujeta la barra con los brazos estirados.",
            "Inclina un poco el torso hacia delante.",
            "Baja la barra en arco hasta los muslos sin doblar los codos.",
            "Sube lentamente hasta la altura de la cabeza.",
        ],
    ),
    # ---------------------------------------------------------------- bíceps
    _ex(
        "curl-biceps-polea", "Curl de bíceps en polea", E.cable, "cable_crossover", "biceps",
        "Bíceps braquial", "Braquial, braquiorradial", "0212",
        "La polea mantiene tensión incluso abajo, donde las mancuernas pierden carga.",
        [
            "De pie frente a la polea baja, sujeta la barra con las palmas hacia arriba.",
            "Pega los codos a los costados.",
            "Sube la barra hasta la altura del pecho.",
            "Baja despacio sin mover los codos.",
        ],
    ),
    _ex(
        "curl-martillo-mancuernas", "Curl martillo con mancuernas", E.dumbbell,
        "adjustable_bench", "biceps", "Braquial, braquiorradial", "Bíceps braquial", "0227",
        "El agarre neutro trabaja el braquial y el antebrazo además del bíceps.",
        [
            "De pie, mancuernas a los lados con las palmas mirando al cuerpo.",
            "Sube las mancuernas sin girar las muñecas.",
            "Aprieta arriba un segundo.",
            "Baja despacio.",
        ],
    ),
    _ex(
        "curl-biceps-maquina", "Curl de bíceps en máquina", E.machine,
        "biceps_curl_machine", "biceps", "Bíceps braquial", "Braquial", "0253",
        "Los brazos apoyados evitan el balanceo y aíslan el bíceps.",
        [
            "Ajusta el asiento para que las axilas queden en el borde del apoyo.",
            "Sujeta las manijas con las palmas hacia arriba.",
            "Flexiona los codos hasta el final del recorrido.",
            "Baja despacio hasta casi estirar.",
        ],
    ),
    # ---------------------------------------------------------------- tríceps
    _ex(
        "extension-triceps-cuerda", "Extensión de tríceps con cuerda", E.cable,
        "cable_crossover", "triceps", "Tríceps braquial", "Ancóneo", "0206",
        "Con la cuerda puedes separar las manos al final y contraer más el tríceps.",
        [
            "Engancha la cuerda en la polea alta y sujétala con las palmas enfrentadas.",
            "Pega los codos al cuerpo.",
            "Extiende los brazos hacia abajo separando las manos al final.",
            "Sube controlando hasta que los antebrazos queden paralelos al suelo.",
        ],
    ),
    _ex(
        "extension-triceps-maquina", "Extensión de tríceps en máquina", E.machine,
        "triceps_machine", "triceps", "Tríceps braquial", "", "0210",
        "Aislamiento guiado del tríceps con los brazos apoyados.",
        [
            "Ajusta el asiento y apoya los brazos en la almohadilla.",
            "Sujeta las manijas con los codos flexionados.",
            "Extiende los brazos por completo.",
            "Vuelve despacio a la posición inicial.",
        ],
    ),
    _ex(
        "fondos-maquina", "Fondos en máquina", E.machine, "dip_machine", "triceps",
        "Tríceps braquial", "Pectoral mayor (porción inferior), deltoide anterior", "0171",
        "Empuje hacia abajo con el torso vertical. La máquina permite elegir la carga.",
        [
            "Siéntate y sujeta las manijas a los lados del cuerpo.",
            "Mantén el torso erguido y los codos hacia atrás.",
            "Empuja hacia abajo hasta estirar los brazos.",
            "Sube despacio hasta que los codos formen unos 90°.",
        ],
    ),
    _ex(
        "patada-triceps-mancuerna", "Patada de tríceps con mancuerna", E.dumbbell,
        "adjustable_bench", "triceps", "Tríceps braquial", "Deltoide posterior", "0204",
        "Aislamiento con el brazo paralelo al suelo; la contracción máxima está al "
        "estirar el codo.",
        [
            "Apoya una rodilla y una mano en el banco.",
            "Sube el codo hasta que el brazo quede pegado al cuerpo y paralelo al suelo.",
            "Extiende el antebrazo hacia atrás.",
            "Vuelve despacio sin mover el codo.",
        ],
    ),
    # ---------------------------------------------------------------- cardio
    _ex(
        "cinta-correr", "Cinta de correr", E.cardio, "treadmill", "cardio",
        "Sistema cardiovascular", "Cuádriceps, gemelos, glúteos", None,
        "Caminar rápido o trotar unos minutos eleva la temperatura y prepara las "
        "articulaciones antes de la fuerza.",
        [
            "Súbete con los pies a los lados de la banda y enciende a baja velocidad.",
            "Empieza caminando y sube la velocidad poco a poco.",
            "Mantén la mirada al frente y evita apoyarte en los pasamanos.",
            "Baja la velocidad al final para recuperar.",
        ],
    ),
    _ex(
        "eliptica", "Elíptica", E.cardio, "elliptical", "cardio",
        "Sistema cardiovascular", "Glúteos, cuádriceps, hombros", None,
        "Cardio de bajo impacto que mueve brazos y piernas a la vez.",
        [
            "Sube a los pedales y sujeta las manijas móviles.",
            "Empieza a un ritmo suave.",
            "Ajusta la resistencia para poder hablar con algo de esfuerzo.",
            "Reduce el ritmo el último minuto.",
        ],
    ),
    _ex(
        "bicicleta-estatica", "Bicicleta estática", E.cardio, "stationary_bike", "cardio",
        "Sistema cardiovascular", "Cuádriceps, glúteos", None,
        "Calentamiento suave para las rodillas antes de un día de tren superior o "
        "inferior.",
        [
            "Ajusta el sillín para que la rodilla quede casi estirada abajo.",
            "Pedalea con resistencia baja el primer minuto.",
            "Sube la resistencia hasta un esfuerzo moderado.",
            "Baja la resistencia al terminar.",
        ],
    ),
]


# (slug, series, reps, % del peso máximo, minutos para cardio, descanso en s)
def _s(slug: str, sets: int, reps: int, pct: int | None = None, rest: int = 90) -> tuple:
    return (slug, sets, reps, pct, None, rest)


def _c(slug: str, minutes: int) -> tuple:
    return (slug, 1, 0, None, minutes, 0)


PLAN_DAYS: list[dict] = [
    {
        "day": 1,
        "title": "Día 1 · Tren inferior — Piernas y glúteos",
        "focus": "tren inferior",
        "items": [
            _c("cinta-correr", 5),
            _s("prensa-inclinada", 4, 12, 70),
            _s("extension-cuadriceps", 3, 12, 65, 75),
            _s("curl-femoral-sentado", 3, 12, 65, 75),
            _s("abduccion-cadera-maquina", 3, 15, 60, 60),
            _s("sentadilla-goblet", 3, 12, None, 75),
            _s("gemelos-prensa", 3, 15, 70, 60),
        ],
    },
    {
        "day": 2,
        "title": "Día 2 · Tren superior — Pecho, hombros y tríceps",
        "focus": "tren superior",
        "items": [
            _c("cinta-correr", 5),
            _s("press-pecho-palanca", 4, 10, 75),
            _s("aperturas-pec-deck", 3, 12, 70, 75),
            _s("press-hombro-maquina", 4, 10, 75),
            _s("vuelo-posterior-maquina", 3, 12, 65, 60),
            _s("press-inclinado-mancuernas", 3, 10, 70),
            _s("elevaciones-laterales-mancuernas", 3, 15, None, 60),
            _s("extension-triceps-cuerda", 3, 12, 70, 60),
        ],
    },
    {
        "day": 3,
        "title": "Día 3 · Tren inferior — Glúteos y femoral",
        "focus": "tren inferior",
        "items": [
            _c("eliptica", 5),
            _s("hip-thrust-smith", 4, 10, 75),
            _s("curl-femoral-acostado", 3, 12, 70, 75),
            _s("peso-muerto-rumano-mancuernas", 3, 10, 70),
            _s("patada-gluteo-polea", 3, 15, None, 60),
            _s("abduccion-cadera-maquina", 3, 15, 65, 60),
            _s("sentadilla-sumo-mancuerna", 3, 12, None, 75),
        ],
    },
    {
        "day": 4,
        "title": "Día 4 · Tren superior — Espalda, bíceps y hombros",
        "focus": "tren superior",
        "items": [
            _c("bicicleta-estatica", 5),
            _s("jalon-polea-agarre-ancho", 4, 10, 75),
            _s("remo-sentado-polea", 4, 10, 75),
            _s("remo-smith-prono", 3, 10, 70),
            _s("jalon-agarre-v", 3, 12, 70, 75),
            _s("pulldown-brazos-rectos", 3, 12, None, 60),
            _s("curl-biceps-polea", 3, 12, 70, 60),
            _s("curl-martillo-mancuernas", 3, 12, None, 60),
            _s("elevacion-frontal-mancuernas", 3, 12, None, 60),
        ],
    },
    {
        "day": 5,
        "title": "Día 5 · Tren inferior — Cuádriceps y glúteos",
        "focus": "tren inferior",
        "items": [
            _c("cinta-correr", 5),
            _s("sentadilla-smith", 4, 10, 75, 120),
            _s("hack-squat", 3, 10, 75),
            _s("prensa-inclinada", 3, 12, 70),
            _s("extension-cuadriceps", 3, 15, 65, 60),
            _s("zancadas-mancuernas", 3, 12, None, 75),
            _s("aduccion-cadera-maquina", 3, 15, 60, 60),
            _s("gemelos-sentado", 3, 15, 70, 60),
        ],
    },
]

PLAN_DESCRIPTION = (
    "Plan semanal GymVe de 5 días (tren inferior / superior) pensado para Fitness 24 "
    "Seven San José de Bavaria. Máquinas, poleas, Smith, mancuernas y cardio."
)
