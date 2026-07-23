/*
  Belge tarayıcı soyutlaması — SRS §3.1 (Akıllı Belge Tarayıcı).

  SRS OpenCV ile 4 köşe tespiti + perspektif düzeltme istiyor. Bu, native C++
  (JSI) entegrasyonu gerektiren, FAZ 4'ün EN RİSKLİ parçası. Bu yüzden bir arayüz
  arkasına alıyoruz (HTR motoruyla aynı desen):

    RawCaptureScanner — ham fotoğraf (kenar tespiti yok). Hemen çalışır, her yerde.
    OpenCVScanner     — native OpenCV; dev build + JSI binding gerektirir (sonra).

  Böylece kamera ekranı hangi tarayıcının çalıştığını bilmez; OpenCV hazır olunca
  tek satır config değişir.
*/

export interface ScanResult {
  /** Düzeltilmiş/işlenmiş görselin cihaz yolu. Ham modda çekilen foto ile aynı. */
  uri: string;
  /** İşleme uygulandı mı (perspektif düzeltme, gölge temizleme). */
  processed: boolean;
}

export interface DocumentScanner {
  /** Verilen ham fotoğrafı işler. Ham modda olduğu gibi döndürür. */
  process(photoUri: string): Promise<ScanResult>;
}

/** Kenar tespiti yapmadan ham fotoğrafı kullanır. Prod öncesi güvenli varsayılan. */
export class RawCaptureScanner implements DocumentScanner {
  async process(photoUri: string): Promise<ScanResult> {
    return { uri: photoUri, processed: false };
  }
}

/**
 * OpenCV tarayıcı yer tutucu. Gerçek uygulama JSI üzerinden native OpenCV
 * çağırır: 4 köşe tespiti, perspektif warp, gölge temizleme. Şu an native binding
 * olmadığı için ham fotoğrafa düşer — böylece uygulama çalışır, sadece işleme yapmaz.
 */
export class OpenCVScanner implements DocumentScanner {
  async process(photoUri: string): Promise<ScanResult> {
    // TODO(faz4): react-native-vision-camera frame processor + OpenCV JSI.
    //   1. Kağıdın 4 köşesini bul (findContours + approxPolyDP)
    //   2. getPerspectiveTransform + warpPerspective ile düzelt
    //   3. adaptiveThreshold ile gölge/aydınlatma temizle
    return { uri: photoUri, processed: false };
  }
}

let _scanner: DocumentScanner | null = null;

export function getScanner(): DocumentScanner {
  if (!_scanner) _scanner = new RawCaptureScanner();
  return _scanner;
}
