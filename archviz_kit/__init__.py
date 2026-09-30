"""archviz-render-kit — mimari görselleştirme için render ön ayarları ve yardımcıları.

Bu paket Blender'a bağımlı değildir; kamera matematiği, ön ayar çözümleme ve
çekim listesi üretimi saf Python olarak çalışır ve test edilebilir.
Blender'a bağlanan kısımlar `blender/` klasöründedir ve `archviz_kit.bridge`
üzerinden aynı mantığı kullanır.
"""

from archviz_kit.framing import (
    fit_distance_m,
    horizontal_fov_deg,
    ortho_scale_for_area,
    sensor_height_mm,
    shift_y_for_target,
    vertical_fov_deg,
)
from archviz_kit.naming import output_name, slugify
from archviz_kit.presets import (
    QUALITY_TIERS,
    available_presets,
    load_preset,
    resolve,
    validate_preset,
)
from archviz_kit.shotlist import build_shotlist

__version__ = "0.1.0"

__all__ = [
    "QUALITY_TIERS",
    "available_presets",
    "build_shotlist",
    "fit_distance_m",
    "horizontal_fov_deg",
    "load_preset",
    "ortho_scale_for_area",
    "output_name",
    "resolve",
    "sensor_height_mm",
    "shift_y_for_target",
    "slugify",
    "validate_preset",
    "vertical_fov_deg",
]