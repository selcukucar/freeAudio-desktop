# 1.2.0

- Ana pencereye ses düzeyi alanı, Sesi azalt ve Sesi artır düğmeleri eklendi. Kütüphane açılmadan F5/F6 ile ses beşer puan değiştirilebilir; alana doğrudan değer yazıp Enter ile uygulanabilir.
- Ses alanı oynatıcı, kütüphane ve genel kısayollarla eşzamanlıdır. Kullanıcı sayı yazarken otomatik yenileme yazılan değeri değiştirmez. Mevcut 0–200 ses aralığı ve 100 üzerindeki yükseltmenin oturumluk davranışı korunur.
- Ana pencere, standart Windows kontrolleriyle Oynatma ve Kütüphane ve uygulama gruplarına ayrıldı. Başlık ve çalan medya daha belirgin, düğmeler daha yüksek ve düzen iki sütunludur; dar pencerede tek sütuna geçilir.
- Mevcut pencereler, sekmeler, komutlar, başlangıç davranışı, F8 geçişi ve genel kısayollar korunur. Ses alanının düzenlenebilir native bölümünün ekran okuyucu adı ayrıca doğrulandı.
- Windows sistem renkleri ve yazı tipi kullanılır; özel çizilmiş düğme veya yeni bir gezinme katmanı eklenmez. Yeni arayüz testleri Türkçe/İngilizce adları, klavye sırasını ve dar pencere genişliğini denetler.

# 1.1.3

- Başlangıçta otomatik güncelleme denetimi açıkken uygulama açıldıktan yaklaşık 5 saniye sonra arka planda denetim yapılır.
- Yeni sürüm ekran okuyucuya bir kez bildirilir ve ana penceredeki güncelleme düğmesinde sürüm numarasıyla gösterilir. Bildirim pencere açmaz, odağı değiştirmez ve çalmayı durdurmaz.
- Güncelleme düğmesi bulunan sürümün indirme/kurulum seçeneklerini açar. Kullanıcı seçmeden dosya indirilmez veya kurulmaz.
- İnternet yoksa veya yeni sürüm bulunmazsa başlangıçta gereksiz ileti verilmez. Otomatik denetim tercihi korunur.
- Bekleyen başlangıç denetimi kapanışta iptal edilir; arka plan istekleri arayüz iş parçacığına aktarılır. Otomatik denetim sürerken yapılan elle denetim isteği kaybolmaz.

# 1.1.2

- Ana pencere ve kütüphanede F8 artık durdurma / son dinleneni yeniden oynatma arasında geçiş yapar. Aynı düğme odağı değiştirmeden yeniden kullanılabilir; etiketi mevcut işlevini gösterir.
- Durdurma sürerken ikinci basış yeniden oynatmayı sıraya alır; üçüncü basış bu isteği iptal eder. Durdurma ve yeniden açma aynı anda ses motorunu yönetmez.
- Henüz bağlanmakta olan yayın F8 ile iptal edilir. Başarısız son medya çözümlemesinde bekleyen bağlantı durumu temizlenir.
- F8 basılı tutulduğunda otomatik tuş tekrarı geçiş yapmaz. Değiştirici tuşlarla F8 kullanan diğer kısayollar korunur. Genel Ctrl+Alt+Shift+S yalnız durdurma olarak kalır.
- Başka bir oynatma komutundan sonra geç tamamlanan durdurma işleminin kontrolleri bekleme durumunda bırakması önlendi.
- Duraklatılmış medya durum metninde belirtilir. Kapanmış bildirim kontrolüne geç gelen mesajlar yok sayılır.
- Oynatma, HTTP kayıt, zaman kaydırma, profil yedekleme/geri yükleme, kısayol ve güncelleme doğrulama testleri genişletildi.

# 1.1.1

- Durdur veya F8 sonrasında ana penceredeki oynatma düğmesinin son dinleneni yeniden başlatamaması düzeltildi.
- Düğme Oynat / duraklat / sürdür olarak adlandırıldı. Medya durdurulmuşsa kayıtlı son medya yeniden açılır; medya yüklüyse duraklatılır veya sürdürülür.
- Düğmenin hızlı ve art arda kullanımı genel kısayolların çift/üç basış ayarlarından ayrıldı; her düğme etkinleştirmesi bir oynatma işlemi yapar.
- Son dinlenen bulunmuyorsa kütüphaneden seçim yapılmasını isteyen bildirim korunur. Kapanış sırasında yeni oynatma başlatılmaz.
- 1.1.0 üzerine kurulum ve profil koruma denetimi yayın sürecine bağlandı.

# 1.1.0

- Ana pencereye ve kütüphaneye erişilebilir Durdur düğmesi eklendi. Ana pencere ve kütüphanede F8; genel Ctrl+Alt+Shift+S aynı durdurma yolunu kullanır.
- Başlangıçta otomatik sürdürme açıksa ilk odak Durdur düğmesindedir. Ana pencerede çalan medya ve duraklat/sürdür düğmesi bulunur.
- Durdurulan bağlantının gecikmeli profil veya başlangıç işlemiyle tekrar çalması önlendi. Ses motorunun yanıtını beklemek arayüzü engellemez.
- Kurulu uygulama yeni sürümü doğrudan indirip doğrulayabilir, ayarları koruyarak kurabilir ve yeniden açılabilir. Taşınabilir sürüm ZIP indirir.
- İptal, bağlantı kesilmesi, eksik/bozuk dosya ve güvenilmeyen yönlendirme durumlarında kurulum başlatılmaz. Dosya çalıştırılmadan önce tekrar doğrulanır.
- Türkçe ve İngilizce arayüz ve yardım güncellendi. Mevcut paketler imzasızdır; SignPath Foundation uygunluk sınırı SIGNING.md içinde açıklanır.

# 1.0.1

- Radyo ve Favoriler sağ tık menüsüne anlık kayıt başlat/durdur ve kayıt klasörünü aç eklendi. Uygulamalar tuşu ve Shift+F10 aynı menüyü açar.
- Fareyle sağ tık olayı listelere bağlandı; tıklanan satır seçilir. Kayıt komutu o anda dinlenen radyoyu kaydeder.
- Bağlantı çözümleme ve kayıt başlatma arayüzü engellemeden yürür. Başarı yalnızca ses verisi alındığında bildirilir.
- Kayıt adları benzersizdir; aynı dakikadaki kayıtlar eski dosyaya eklenmez.
- Veri göndermeyen yayınlarda durdurma beklemesi sınırlandı. Dosya kapanmadan dönüştürme yapılmaz; boş kayıt başarı olarak sunulmaz.
- Hatalı bağlantı, yazılamayan klasör, istasyon değişimi, yinelenen tıklama ve kapanış sırasında kayıt başlatma senaryoları test edildi.
- Kayıt durdurma bildirimi dosyanın tam yolunu verir. Türkçe/İngilizce yardım güncellendi.

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
