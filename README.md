# DocScanner

NovaVision platformu için geliştirilmiş, telefonla çekilen belge fotoğraflarını
kırpıp taranmış kağıt görünümüne dönüştüren bir görüntü işleme paketi (component).
İki executor içerir: DocumentCrop, ScanEffect.

## Executor'lar

### 1. DocumentCrop — 1 input / 1 output

Belgeyi fotoğraftan tespit edip kırpar veya perspektifini düzeltir.

- **Input:** `inputImage` — ham telefon fotoğrafı
- **Output:** `outputImage` — kırpılmış/düzleştirilmiş belge

**`configCropType`** (dependentDropdownlist, 2 seçenek):

| Seçenek | Alanlar | Açıklama |
|---|---|---|
| `AutoCrop` | `paddingPx` (textInput), `edgeSensitivity` (dropdownlist: Low/High) | Belgenin 4 köşesini (Otsu segmentasyonu + kapalı Canny kenarları, en büyük geçerli sayfa) bulup perspektifini düzeltir ve belgenin **kendi doğal oranında** düz bir dikdörtgene oturtur; `paddingPx` kadar beyaz kenar payı bırakır. Köşeler bulunamazsa (belge kareyi kaplıyorsa) tüm kareyi döndürür. |
| `PerspectiveCorrect` | `cornerDetection` (dropdownlist: Auto/Manual), `outputAspect` (textInput) | Aynı 4-köşe tespiti + perspektif düzeltme; ardından çıktıyı `outputAspect` oranına **esnetmeden, beyaz padding ile** oturtur (0.707 ≈ A4). Köşe bulunamazsa (`Manual` ya da tespit başarısız) orijinal görüntüyü döndürür. |

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

Her iki executor da hatalı/bozuk girdilerde istisna fırlatmak yerine orijinal görüntüyü
değiştirmeden döndürerek çalışmaya devam eder.

## Servise bağlama

Image'in kök `service.py`'sinde iki executor'ı kaydedin (`{PaketAdı: {ExecutorAdı: Sınıf}}`):

```python
from components.DocScanner.src.executors.DocumentCrop import DocumentCrop
from components.DocScanner.src.executors.ScanEffect import ScanEffect

executors = {
    "DocScanner": {
        "DocumentCrop": DocumentCrop,
        "ScanEffect": ScanEffect,
    }
}
```

`executors/` klasöründe yalnızca gerçek executor dosyaları (`DocumentCrop.py`, `ScanEffect.py`)
bulunur; platform bu klasördeki her dosyayı bir executor olarak listelediği için
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
