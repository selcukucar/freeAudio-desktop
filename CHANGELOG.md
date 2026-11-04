# 1.0.0

- Bağımsız uygulama için Windows tuşu içermeyen varsayılan kısayollar. Windows'un ayırdığı F12 yerine yer imi için Ctrl+Alt+Shift+B.
- Özel kısayollar ve kapatılmış atamalar korunur. Komut listesi tuş bileşimlerini ve kullanılamama durumunu gösterir; seçili kısayol varsayılana döndürülebilir.
- Kısayol ayarı diske kaydedilemezse önceki çalışan atama geri yüklenir.
- GitHub kararlı güncelleme kanalı ve elle başlatılan derlemelerin paket çıktılarının saklanması hazırlandı.
- Özgün depodaki 2018 FFmpeg çalıştırılabilir dosyası dağıtımın dışında tutuldu. Gerektiren özellikler için Ayarlar'dan harici FFmpeg yolu seçilir.
- Kullanıcı GETEM girişini ve sesli kitap, radyo ve podcast oynatmayı doğruladı.

# 0.1.0-alpha.3

- Yedeklerdeki ayar değerleri ve favori/ilerleme dosyalarının temel yapısı geri yüklemeden önce doğrulanıyor. Hatalı yedek, önceki sağlam yedeğin üzerine yazılmıyor.
- Otomatik yedek oluşturulamaması uygulamanın açılmasını engellemiyor; kullanıcıya bildirim veriliyor.
- Kayıt sürerken çıkış için onay isteniyor. Son ayar kaydı başarısız olsa bile kapanış tamamlanıyor.
- Güncelleme denetimi kapanmış pencereye bildirim göndermiyor; aynı anda yinelenen denetimler birleştiriliyor.
- Ayar kaydetme hataları kullanıcıya bildiriliyor; aynı hata her otomatik kayıtta tekrar seslendirilmiyor.
- Kaynak ZIP, derleme klasörlerini, sanal ortamları, yayın çıktılarını ve standart yerel test profillerini dışarıda tutuyor.
- 50 otomatik test geçti.

# 0.1.0-alpha.2

- Başlangıç ayarı artık uygulamanın kendi açılışında son dinleneni sürdürmeyi anlatıyor.
- Bildirim sesi seçimi “Ekran okuyucu” / “Windows sesi” olarak adlandırıldı. Braille'in isteğe bağlı ekran okuyucu desteği olduğu açıklanıyor.
- Ayar sıfırlama mesajı uygulamanın yeniden başlatılmasını istiyor. Komut açıklamaları seçilen dilde gösteriliyor.
- Henüz yayın kanalı yokken işlevsiz otomatik güncelleme kontrolleri ayarlardan gizleniyor.
- Profil ZIP yedekleme, doğrulanmış geri yükleme, geri yükleme öncesi ve sürüm değişiminde otomatik profil yedeği eklendi.
- Eski sürümün ses, başlangıç ve braille tercihleri korunuyor.
- Aygıt ve ses listesi henüz yüklenirken Kaydet'e basılması kayıtlı tercihleri silmiyor.
- Günlük dosyaları sınırlı boyutta döndürülüyor.
- Türkçe ve İngilizce yardım, başlıklar ve içindekiler bağlantıları olan erişilebilir HTML olarak yenilendi.
- Yayın kanalı dosyası, paket doğrulama aracı ve gelecekteki GitHub deposu için taslak sürüm iş akışı hazırlandı.
- Profil geri yükleme, HTTP podcast, anlık kayıt, zaman kaydırma ve kayıtlı ayarların korunması için testler eklendi.
- Canlı LibriVox/Gutenberg arama ve bölüm çözümleme kontrolleri başarılı oldu.

# 0.1.0-alpha.1

NVDA'dan bağımsız ilk masaüstü uyarlaması; Türkçe/İngilizce arayüz, taşınabilir ZIP, kullanıcı hesabına kurulum ve genel kısayol yönetimi.
