from pathlib import Path
import tensorflow as tf
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64
from tensorflow.keras import layers
from tensorflow.keras.models import load_model


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = BASE_DIR / "models" / "modelo_deshielo.keras"

SEA_ICE_IMG_SIZE   = 256
SEA_ICE_BATCH_SIZE = 8
SEA_ICE_EPOCHS     = 15
MAX_ICE_TRAIN      = 1000 # Aumentado de 500
MAX_ICE_VAL        = 200
SEED_ICE           = 42

MODEL = None


# 1. Definir la métrica personalizada (obligatorio para la carga)
def iou_metric(y_true, y_pred, smooth=1e-6):
    y_pred_bin = tf.cast(y_pred > 0.5, tf.float32)
    intersection = tf.reduce_sum(y_true * y_pred_bin)
    union = tf.reduce_sum(y_true) + tf.reduce_sum(y_pred_bin) - intersection
    return (intersection + smooth) / (union + smooth)

# 2. Re-definir arquitectura para carga limpia
def conv_block(x, filters, name_prefix):
    x = tf.keras.layers.Conv2D(filters, 3, padding='same', activation='relu', name=f'{name_prefix}_conv1')(x)
    x = tf.keras.layers.Conv2D(filters, 3, padding='same', activation='relu', name=f'{name_prefix}_conv2')(x)
    return x

def spatial_attention_block(x, name_prefix='att'):
    avg_pool = tf.keras.layers.Lambda(lambda t: tf.reduce_mean(t, axis=-1, keepdims=True), name=f'{name_prefix}_avg')(x)
    max_pool = tf.keras.layers.Lambda(lambda t: tf.reduce_max(t, axis=-1, keepdims=True), name=f'{name_prefix}_max')(x)
    concat = tf.keras.layers.Concatenate(name=f'{name_prefix}_concat')([avg_pool, max_pool])
    att_map = tf.keras.layers.Conv2D(1, 7, padding='same', activation='sigmoid', name=f'{name_prefix}_map')(concat)
    out = tf.keras.layers.Multiply(name=f'{name_prefix}_mul')([x, att_map])
    return out

def weighted_bce(y_true, y_pred):
    weights = (y_true * 5.0) + 1.0
    bce = tf.keras.backend.binary_crossentropy(y_true, y_pred)
    return tf.reduce_mean(bce * weights)

def build_ice_model(input_shape=(256, 256, 3)):
    inputs = layers.Input(shape=input_shape, name='input_ice')
    c1 = conv_block(inputs, 16, 'ice_enc1')
    p1 = layers.MaxPooling2D((2, 2))(c1)
    c2 = conv_block(p1, 32, 'ice_enc2')
    p2 = layers.MaxPooling2D((2, 2))(c2)
    b = conv_block(p2, 64, 'ice_bottleneck')
    b = spatial_attention_block(b, 'ice_bottleneck_att')
    u2 = layers.UpSampling2D((2, 2))(b)
    u2 = layers.Concatenate()([u2, c2])
    c3 = conv_block(u2, 32, 'ice_dec2')
    u1 = layers.UpSampling2D((2, 2))(c3)
    u1 = layers.Concatenate()([u1, c1])
    c4 = conv_block(u1, 16, 'ice_dec1')
    outputs = layers.Conv2D(1, 1, activation='sigmoid', name='deshielo_prob')(c4)

    model = tf.keras.models.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss= weighted_bce,
        metrics=[
            tf.keras.metrics.RootMeanSquaredError(name='rmse'), # Re-agregado para evitar KeyError
            'accuracy',
            iou_metric
        ]
    )
    return model


def get_model():
    global MODEL
    
    if MODEL is None:

        model = build_ice_model()

        model.load_weights(MODEL_PATH)

        MODEL = model

    return MODEL

# 5) Inferencia para imagen png/jpg y salida con mapa de calor
def load_ice_image(path, target_size=(SEA_ICE_IMG_SIZE, SEA_ICE_IMG_SIZE)):
    """Carga y normaliza imagen satelital para inferencia."""
    img = Image.open(path).convert('RGB')
    img_np = np.array(img)
    img_rs = tf.image.resize(img_np, target_size, method='bilinear').numpy().astype(np.uint8)
    return img_rs, img_rs.astype(np.float32)[np.newaxis] / 255.0

def create_ice_overlay(rgb_img, prob_map):
    """Genera mapa de calor azul e imagen con overlay para deshielo."""
    cmap = plt.get_cmap('Blues')
    heat = (cmap(prob_map)[..., :3] * 255).astype(np.uint8)
    overlay = (0.55 * rgb_img + 0.45 * heat).astype(np.uint8)
    return heat, overlay

def glacier_report(prob_map, grid_size=4):
    total_percent = float(prob_map.mean() * 100.0)
    h, w = prob_map.shape
    gh, gw = h // grid_size, w // grid_size
    grid = np.zeros((grid_size, grid_size), dtype=np.float32)

    for i in range(grid_size):
        for j in range(grid_size):
            region = prob_map[i*gh:(i+1)*gh, j*gw:(j+1)*gw]
            grid[i, j] = region.mean() * 100.0

    return total_percent, grid

def image_to_base64(img_array):

    buffer = io.BytesIO()

    Image.fromarray(img_array).save(
        buffer,
        format="PNG"
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode()
    
def ice_melt_report(prob_map, grid_size=4):
    """Calcula % de deshielo total y por grilla (grid_size × grid_size)."""
    total_pct = float(prob_map.mean() * 100.0)
    h, w = prob_map.shape
    gh, gw = h // grid_size, w // grid_size
    grid = np.zeros((grid_size, grid_size), dtype=np.float32)
    for i in range(grid_size):
        for j in range(grid_size):
            grid[i, j] = prob_map[i*gh:(i+1)*gh, j*gw:(j+1)*gw].mean() * 100.0
    return total_pct, grid

def predict_glacier(image_path, threshold=0.5, grid_size=4):
    
    model = get_model()

    rgb_img, x = load_ice_image(image_path)

    prob = model.predict(x,verbose=0)[0, :, :, 0]

    print("MIN:", prob.min())
    print("MAX:", prob.max())
    print("MEAN:", prob.mean())
    mask = (prob >= 0.30).astype(np.uint8) * 255

    heat, overlay = create_ice_overlay(rgb_img, prob)

    total_pct, grid = ice_melt_report(prob, grid_size)
    if total_pct < 30:

        status = "Conservado"

    elif total_pct < 60:

        status = "Vulnerable"

    else:

        status = "Crítico"
    return {

        "cobertura_hielo": round(100 - total_pct, 2),

        "deshielo": round(
            total_pct,
            2
        ),

        "estado": status,

        "grid": grid.tolist(),

        "heatmap": image_to_base64(
            heat
        ),

        "overlay": image_to_base64(
            overlay
        ),

        "mask": image_to_base64(
            mask
        )
    }