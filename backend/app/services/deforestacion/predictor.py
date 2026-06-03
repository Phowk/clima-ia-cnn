from pathlib import Path
import json
import tensorflow as tf
import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io
import base64


IMG_SIZE = 256

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = BASE_DIR / "models" / "modelo_deforestacion.keras"

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

def build_model_for_loading(input_shape=(256, 256, 3)):
    inputs = tf.keras.layers.Input(shape=input_shape)
    c1 = conv_block(inputs, 16, 'enc1')
    p1 = tf.keras.layers.MaxPooling2D((2,2))(c1)
    c2 = conv_block(p1, 32, 'enc2')
    p2 = tf.keras.layers.MaxPooling2D((2,2))(c2)
    b = conv_block(p2, 64, 'bottleneck')
    b = spatial_attention_block(b, 'bottleneck_att')
    u2 = tf.keras.layers.UpSampling2D((2,2))(b)
    u2 = tf.keras.layers.Concatenate()([u2, c2])
    c3 = conv_block(u2, 32, 'dec2')
    u1 = tf.keras.layers.UpSampling2D((2,2))(c3)
    u1 = tf.keras.layers.Concatenate()([u1, c1])
    c4 = conv_block(u1, 16, 'dec1')
    outputs = tf.keras.layers.Conv2D(1, 1, activation='sigmoid')(c4)
    model = tf.keras.models.Model(inputs, outputs)
    return model

def get_model():

    global MODEL

    if MODEL is None:

        model = build_model_for_loading()

        model.load_weights(MODEL_PATH)

        MODEL = model

    return MODEL

# 5) Inferencia para imagen png/jpg y salida con mapa de calor
def load_rgb_image(path, target_size=(IMG_SIZE, IMG_SIZE)):
    img = Image.open(path).convert('RGB')
    img = np.array(img)
    img_resized = tf.image.resize(img, target_size, method='bilinear').numpy().astype(np.uint8)
    x = img_resized.astype(np.float32) / 255.0
    return img_resized, x[None, ...]

def create_heat_overlay(rgb_img, prob_map):
    # prob_map: [0,1]
    cmap = plt.get_cmap('jet')
    heat = cmap(prob_map)[..., :3]  # RGB
    heat_u8 = (heat * 255).astype(np.uint8)
    overlay = (0.6 * rgb_img + 0.4 * heat_u8).astype(np.uint8)
    return heat_u8, overlay

def deforestation_report(prob_map, grid_size=4):
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

def predict_image(image_path, threshold=0.5, grid_size=4):
    model = get_model()

    rgb_img, x = load_rgb_image(image_path)

    prob = model.predict(x,verbose=0)[0,:,:,0]

    mask = (prob >= threshold).astype(np.uint8) * 255

    heat, overlay = create_heat_overlay(rgb_img, prob) 
    
    total_percent, grid = deforestation_report(prob, grid_size)
    if total_percent < 20:
        risk = "Bajo"

    elif total_percent < 50:
        risk = "Medio"
    
    else:
        risk = "Alto"
    
    return {

    "porcentaje": round(total_percent, 2),

    "riesgo": risk,

    "grid": grid.tolist(),

    "heatmap": image_to_base64(heat),

    "overlay": image_to_base64(overlay),

    "mask": image_to_base64(mask)
}
