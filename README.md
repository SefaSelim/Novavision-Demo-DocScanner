# DocScanner

NovaVision platformu için geliştirilmiş, telefonla çekilen belge fotoğraflarını
kırpıp taranmış kağıt görünümüne dönüştüren ve yeniden boyutlandıran bir görüntü
işleme paketi (component). Üç executor içerir: DocumentCrop, ScanEffect, Resize.

## Executor'lar

### 1. DocumentCrop — 1 input / 1 output

Belgeyi fotoğraftan tespit edip kırpar veya perspektifini düzeltir.

- **Input:** `inputImage` — ham telefon fotoğrafı
- **Output:** `outputImage` — kırpılmış/düzleştirilmiş belge

**`configCropType`** (dependentDropdownlist, 2 seçenek):

| Seçenek | Alanlar | Açıklama |
|---|---|---|
| `AutoCrop` | `paddingPx` (textInput), `edgeSensitivity` (dropdownlist: Low/High) | En büyük 4 köşeli konturu (Canny + `findContours`) bulup etrafında `paddingPx` kadar boşluk bırakarak kırpar. Kontur bulunamazsa görüntüyü olduğu gibi (padding kadar kenardan kırparak) döndürür. |
| `PerspectiveCorrect` | `cornerDetection` (dropdownlist: Auto/Manual), `outputAspect` (textInput) | 4 köşeyi bulup `getPerspectiveTransform` + `warpPerspective` ile düz bir dikdörtgene oturtur; çıktı en-boy oranı `outputAspect` ile ayarlanır (0.707 ≈ A4). Köşe bulunamazsa (`Manual` ya da tespit başarısız) orijinal görüntüyü değiştirmeden döner. |

### 2. ScanEffect — 2 input / 2 output

Kırpılmış belgeye "taranmış kağıt" efekti uygular ve sonucun kalitesini puanlar.

- **Input:** `inputImage` — kırpılmış belge, `inputReferenceImage` (opsiyonel) — aynı
  ışıkta çekilmiş boş/beyaz bir referans yaması, beyaz dengesi için kullanılır
- **Output:** `outputImage` — taranmış sonuç, `outputQualityScore` — netlik/kontrast
  temelli 0-100 arası basit bir kalite skoru

**`configScanType`** (dependentDropdownlist, 2 seçenek):

| Seçenek | Alanlar | Açıklama |
|---|---|---|
| `BlackWhiteScan` | `sharpenLevel` (textInput), `scanMode` (dropdownlist: HighContrastBW/GrayscaleSoft) | Metin belgeleri için klasik siyah-beyaz tarama görünümü. `HighContrastBW` adaptif eşikleme, `GrayscaleSoft` CLAHE ile kontrast artırılmış gri ton üretir; ardından `sharpenLevel`'e göre unsharp mask uygulanır. |
| `ColorScan` | `brightness` (textInput), `saturationBoost` (textInput), `whiteBalance` (dropdownlist: Auto/Reference) | Renkli belge/fotoğraf tarama modu. `whiteBalance` = `Reference` ise beyaz dengesi `inputReferenceImage`'ın kanal ortalamalarından, `Auto` ise görüntünün kendisinden (gray-world) hesaplanır; ardından parlaklık ve doygunluk ayarlanır. |

### 3. Resize — 1 input / 1 output

Görüntüyü isteğe bağlı olarak yeniden boyutlandırır (otomatik değil — kullanıcı seçer).

- **Input:** `inputImage` — herhangi bir görüntü
- **Output:** `outputImage` — yeniden boyutlandırılmış görüntü

**`configResizeMode`** (dependentDropdownlist, 2 seçenek):

| Seçenek | Alanlar | Açıklama |
|---|---|---|
| `FitLongEdge` | `maxEdge` (textInput), `interpolation` (dropdownlist: Area/Cubic) | En uzun kenarı `maxEdge` piksele ölçekler, en-boy oranını korur. `Area` küçültme, `Cubic` büyütme için idealdir. |
| `ExactSize` | `targetWidth` (textInput), `targetHeight` (textInput), `fitMode` (dropdownlist: Stretch/Pad) | Tam `targetWidth × targetHeight` boyutuna getirir. `Stretch` oranı yok sayıp kutuyu doldurur; `Pad` oranı koruyup kalanı beyazla doldurur. |

Üç executor da hatalı/bozuk girdilerde istisna fırlatmak yerine orijinal görüntüyü
değiştirmeden döndürerek çalışmaya devam eder.

## Servise bağlama

Image'in kök `service.py`'sinde üç executor'ı kaydedin (`{PaketAdı: {ExecutorAdı: Sınıf}}`):

```python
from components.DocScanner.src.executors.DocumentCrop import DocumentCrop
from components.DocScanner.src.executors.ScanEffect import ScanEffect
from components.DocScanner.src.executors.Resize import Resize

executors = {
    "DocScanner": {
        "DocumentCrop": DocumentCrop,
        "ScanEffect": ScanEffect,
        "Resize": Resize,
    }
}
```

`executors/` klasöründe yalnızca gerçek executor dosyaları (`DocumentCrop.py`, `ScanEffect.py`,
`Resize.py`) bulunur; platform bu klasördeki her dosyayı bir executor olarak listelediği için
buraya `__init__.py`/`__main__.py` gibi yardımcı dosyalar konmaz.

## Kullanım

`apps/client.py` her iki executor'ın her seçeneği için örnek bir istek payload'ı üretir.
Servis çalışırken (`service.py`, bu repo'nun konulacağı Image içinde) örnek bir isteği
göndermek için:

```python
from apps.client import build_document_crop_auto_request, send
send(build_document_crop_auto_request())
```

Test görselleri için bkz. [resources/README.md](resources/README.md).
