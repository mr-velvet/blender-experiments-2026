"""layout.py — plano de mobiliario (decisao de design do TD).

Define, por comodo, quais moveis vao, em que posicao relativa e rotacao.

Posicao: dada como (u, v) em coordenadas LOCAIS do comodo, onde
  u in [0,1] = posicao ao longo de X do comodo (0 = parede esquerda do comodo, 1 = direita)
  v in [0,1] = posicao ao longo de Y (0 = FRENTE aberta, 1 = parede de FUNDO)
Convertidas pra mundo no pipeline usando o bbox do comodo (rooms.json).

rot_z: rotacao em graus (Z up). 0 = asset "olhando" pra +Y (fundo).
  Como a frente e aberta (camera em -Y), moveis encostados no fundo geralmente
  ficam de frente pra camera com rot_z=180.

target_w: largura alvo (m) ao longo do eixo maior do movel; o pipeline escala o
  asset uniformemente pra bater nessa dimensao (mantendo proporcao). None = nao reescala.

apoio: 'floor' assenta a base do bbox em z do piso; 'wall_back' encosta no fundo;
  numeros sobrescrevem.

Cada item: slot (chave no furniture_*.json), comodo (floor,side), u, v, rot_z, target_w
"""

# mapa slot -> assetBaseId vem dos furniture_*.json carregados no pipeline.
# Aqui so o posicionamento. O campo "src" diz de qual json puxar o id.

# substituicoes deliberadas (decisao de TD):
#  - kids_bed -> Bunk bed: nao duplicar a Sahara do casal
#  - plant (office_kids) -> backup raster: o asset Geo Nodes principal explode o
#    bbox (geometria do modifier em escala absurda) -> inutilizavel na pratica
#  - table lamp (bedroom) -> backup: o Binic tem escala nativa de ~447m, fica deformado
OVERRIDE_IDS = {
    ("office_kids", "kids_bed"): ("Bunk bed", "f0a54602-44c9-4bf3-a804-0246dc494872"),
    ("office_kids", "plant"):    ("Plant Pot Small (backup)", "3be63453-33f6-46ab-9fc9-bde11230fedd"),
    ("bedroom", "table lamp"):   ("Table lamp (backup)", "4cbcad7d-4b9d-4b7d-9bd7-c7901994cada"),
}

# (floor,side) de cada comodo definido em 02_build_house.py:
#   F0 left=Sala  right=Cozinha
#   F1 left=Quarto casal  right=Banheiro
#   F2 left=Quarto infantil  right=Escritorio

# target_h = escala pela ALTURA real (m). Mais confiavel quando o bbox XY do asset
# tem geometria espuria. target_w = escala pelo maior lado XY. Usar um dos dois.
LAYOUT = [
    # ---------------- TERREO: SALA (F0 left) — comodo ~4.3m x 4.8m ----------------
    {"src": "livingroom", "slot": "rug",         "floor": 0, "side": "left",  "u": 0.40, "v": 0.55, "rot_z": 0,   "target_w": 2.6, "apoio": "rug"},
    {"src": "livingroom", "slot": "sofa",        "floor": 0, "side": "left",  "u": 0.40, "v": 0.85, "rot_z": 180, "target_w": 2.1},
    {"src": "livingroom", "slot": "coffee_table","floor": 0, "side": "left",  "u": 0.40, "v": 0.52, "rot_z": 0,   "target_w": 1.1},
    {"src": "livingroom", "slot": "tv",          "floor": 0, "side": "left",  "u": 0.40, "v": 0.10, "rot_z": 0,   "target_h": 0.5},
    {"src": "livingroom", "slot": "bookshelf",   "floor": 0, "side": "left",  "u": 0.88, "v": 0.85, "rot_z": 180, "target_h": 1.9},
    {"src": "livingroom", "slot": "armchair",    "floor": 0, "side": "left",  "u": 0.85, "v": 0.32, "rot_z": 235, "target_h": 0.85},
    {"src": "livingroom", "slot": "floor_lamp",  "floor": 0, "side": "left",  "u": 0.92, "v": 0.62, "rot_z": 0,   "target_h": 1.55},

    # ---------------- TERREO: COZINHA (F0 right) — comodo ~3.3m x 4.8m ----------------
    {"src": "kitchen", "slot": "refrigerator", "floor": 0, "side": "right", "u": 0.12, "v": 0.86, "rot_z": 180, "target_h": 1.9},
    {"src": "kitchen", "slot": "stove",        "floor": 0, "side": "right", "u": 0.38, "v": 0.88, "rot_z": 180, "target_h": 0.95},
    {"src": "kitchen", "slot": "kitchen_sink", "floor": 0, "side": "right", "u": 0.66, "v": 0.88, "rot_z": 180, "target_w": 1.1},
    {"src": "kitchen", "slot": "microwave",    "floor": 0, "side": "right", "u": 0.90, "v": 0.88, "rot_z": 180, "target_w": 0.5, "apoio": 0.9},
    {"src": "kitchen", "slot": "dining_table", "floor": 0, "side": "right", "u": 0.45, "v": 0.40, "rot_z": 0,   "target_w": 1.5},
    {"src": "kitchen", "slot": "dining_chair", "floor": 0, "side": "right", "u": 0.22, "v": 0.40, "rot_z": 90,  "target_h": 0.85},
    {"src": "kitchen", "slot": "dining_chair2","floor": 0, "side": "right", "u": 0.68, "v": 0.40, "rot_z": 270, "target_h": 0.85, "reuse": "dining_chair"},

    # ---------------- ANDAR 1: QUARTO CASAL (F1 left) ----------------
    {"src": "bedroom", "slot": "bed",        "floor": 1, "side": "left", "u": 0.42, "v": 0.62, "rot_z": 0,   "target_w": 2.0},
    {"src": "bedroom", "slot": "nightstand", "floor": 1, "side": "left", "u": 0.82, "v": 0.86, "rot_z": 180, "target_h": 0.55},
    {"src": "bedroom", "slot": "wardrobe",   "floor": 1, "side": "left", "u": 0.10, "v": 0.40, "rot_z": 90,  "target_h": 2.15},
    {"src": "bedroom", "slot": "dresser",    "floor": 1, "side": "left", "u": 0.88, "v": 0.30, "rot_z": 180, "target_h": 1.0},
    {"src": "bedroom", "slot": "table lamp", "floor": 1, "side": "left", "u": 0.82, "v": 0.86, "rot_z": 180, "target_h": 0.45, "apoio": 0.55},
    {"src": "bedroom", "slot": "mirror",     "floor": 1, "side": "left", "u": 0.90, "v": 0.62, "rot_z": 270, "target_h": 1.6},

    # ---------------- ANDAR 1: BANHEIRO (F1 right) ----------------
    {"src": "bathroom", "slot": "bathtub",       "floor": 1, "side": "right", "u": 0.32, "v": 0.84, "rot_z": 90,  "target_w": 1.6},
    {"src": "bathroom", "slot": "toilet",        "floor": 1, "side": "right", "u": 0.82, "v": 0.85, "rot_z": 180, "target_h": 0.8},
    {"src": "bathroom", "slot": "bathroom_sink", "floor": 1, "side": "right", "u": 0.85, "v": 0.45, "rot_z": 270, "target_h": 0.85},
    {"src": "bathroom", "slot": "bathroom",      "floor": 1, "side": "right", "u": 0.55, "v": 0.30, "rot_z": 0,   "target_h": 0.3},

    # ---------------- ANDAR 2: QUARTO INFANTIL (F2 left) ----------------
    {"src": "office_kids", "slot": "kids_bed", "floor": 2, "side": "left", "u": 0.32, "v": 0.74, "rot_z": 180, "target_w": 2.0},
    {"src": "office_kids", "slot": "toy",      "floor": 2, "side": "left", "u": 0.72, "v": 0.45, "rot_z": 200, "target_h": 0.45},
    {"src": "office_kids", "slot": "plant",    "floor": 2, "side": "left", "u": 0.90, "v": 0.85, "rot_z": 0,   "target_h": 0.7},

    # ---------------- ANDAR 2: ESCRITORIO (F2 right) ----------------
    {"src": "office_kids", "slot": "desk",         "floor": 2, "side": "right", "u": 0.42, "v": 0.84, "rot_z": 180, "target_w": 1.4},
    {"src": "office_kids", "slot": "office_chair", "floor": 2, "side": "right", "u": 0.42, "v": 0.55, "rot_z": 0,   "target_h": 1.0},
    {"src": "office_kids", "slot": "computer",     "floor": 2, "side": "right", "u": 0.42, "v": 0.86, "rot_z": 180, "target_h": 0.45, "apoio": "on_desk"},
    {"src": "office_kids", "slot": "bookshelf",    "floor": 2, "side": "right", "u": 0.86, "v": 0.82, "rot_z": 180, "target_h": 1.9},
]
