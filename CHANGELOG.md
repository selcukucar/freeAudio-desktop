# 2.2.0

- Ana pencereye Dinlemeye devam et eklendi: yarım kalan podcastler ve sesli kitaplar konumlarıyla listelenir; mevcut çevrimdışı podcast dosyası kullanılır.
- İndirmelere podcast grubu, dinlenmiş/dinlenmemiş süzgeçleri, durum işaretleme, podcast adını düzenleme ve disk kullanım bilgisi eklendi. Önizleme ve abonelikten indirmeler podcast adını korur; adı bilinmeyen eski dosyalar elle gruplandırılabilir.
- Ana pencere düğmelerine değiştirilebilir Ctrl+Shift kısayolları eklendi; kullanılabilir atamalar düğme adlarında görünür. Önceki/sonraki bölüm, kütüphane, indirmeler, geçmiş, ayarlar, komutlar, bildirimler, dil, güncelleme, yedek, yardım, hakkında ve çıkışa doğrudan erişilebilir. Kısayol grubu, yeniden deneme ve ayrıntılı Windows hata kodları sunulur.
- Hızlı uyku zamanlayıcısında 15/30/60 dakika, 1–480 dakika özel süre ve podcast/kitap bölümünün sonunda durdurma bulunur. Kayıtlar ve indirmeler bağımsız sürer. Eski takvimli zamanlayıcılar korunur.
- Bilgisayarı kapatma isteğe bağlıdır ve varsayılan değildir. En az 60 saniyelik uyarı, geri sayım ve iptal düğmesi vardır. Aktif kayıt/indirme, durdurma hatası veya kapatma hazırlığı sırasında yeniden oynatma kapatmayı iptal eder. Diğer uygulamalar zorla kapatılmaz. Testlerde gerçek bilgisayarı kapatma çalıştırılmaz.
- Bozuk indirme/geçmiş verisi onarım öncesi korunur; gelecekteki şema üzerine yazılmaz. Metadata kaydedilemezse dosya silinmez. Kilitli dosyaların listeden kaybolması, geçmiş temizledikten sonra ilk öğenin atlanması ve eski uyku zamanlayıcısının yeni yayına/ses düzeyine müdahalesi düzeltildi.
- Türkçe ve İngilizce yardım ve erişilebilir kontrol etiketleri güncellendi. Paketler imzasızdır.

# 2.1.1

- Ana pencerede görünür radyo kaydı başlat/durdur ve önceki/sonraki bölüm düğmeleri bulunur. Kayıt düğmesi atanmış ve kullanılabilir kısayolu da belirtir.
- Sesli kitap bölümünü düğmeyle değiştirince kütüphanenin otomatik ilerleme durumu da yeni bölümle eşleşir; eski bölümden devam etme riski giderildi.
- Podcast ve sesli kitap sekmelerinde bölüm düğmeleri, komut listesinde uygulama/favori-kitaplık grupları ve güncelleme penceresinde okunabilir sürüm notları bulunur.
- Bölüm geçişi, kayıt odağı, kısayol durumu ve sürüm notlarının bağlantı hatasında davranışı test edildi. 2.1 serisindeki bütün yenilikleri içerir.

# 2.1.0

- Ana pencereye Radyo kaydını başlat / durdur düğmesi eklendi. Atanmış kayıt kısayolu görünür; kayıt oynatmadan bağımsız olarak durdurulabilir. Düğme odağı işlem boyunca korunur.
- Ana pencereye ve Podcast / Sesli Kitaplar sekmelerine Önceki bölüm / Sonraki bölüm düğmeleri eklendi. Çalan içeriğin bölümü esas alınır; kitaplar arasında atlanmaz. İlk/son bölümde bilgi verilir. Çevrimdışı podcastlerde indirilenler listesinin sırası kullanılır.
- Bölüm bağlantıları arka planda hazırlanır. F8 veya başka oynatma komutuyla iptal edilen bir isteğin geç tamamlanıp yeniden oynatma başlatması engellenir.
- Komutlar ve kısayollar, uygulama komutları ile favori/kitaplık öğelerinin kısayollarını ayrı gruplarda gösterir. Bir favori adına otomatik oluşturulan komutlar ve atanmış tuşları korunur.
- Güncelleme penceresine ekran okuyucuyla okunabilen sürüm notları ve işlem seçimi eklendi. Notlar arka planda yüklenir; yüklenemese de indirme seçenekleri kullanılabilir.

# 2.0.0

- Kayıt dizini kullanımı merkezileştirildi: yeni kayıtlar, podcast/kitap indirmeleri, beğenilen şarkı listesi ve klasörü aç komutu seçilen dizini kullanır. Tırnaklı yollar normalleştirilir; ayar kaydedilirken yazılabilirlik sınanır. Geçersiz veya kullanılamayan dizinde varsayılan C: klasörüne geçilmez. Planlı kaydın özel hedefi varsa korunur. Podcast yeniden denemeleri güncel dizini kullanır.

- Ana pencereye İndirmeler ve çevrimdışı podcastler eklendi. İki eşzamanlı indirme, kuyruk, bayt/MB ilerlemesi, iptal, yeniden deneme ve klasörü açma işlemleri bulunur. İlerleme kullanıcı istediğinde bildirilir.
- Tamamlanmış podcastler çevrimdışı oynatılabilir; özgün bölüm adresi konum anahtarı olarak korunur. İndirmeler yeniden açılışta listede kalır. Kesilen indirmeler kullanıcı seçimiyle baştan denenir. Mevcut 1.2.2 dosyaları aynı bölüm indirilmek istendiğinde listeye alınır, üzerine yazılmaz.
- Listeden kaldır dosyayı korur; dosyayı sil ayrıca onay ister. Aktif indirmeler uygulama çıkışında onayla iptal edilir; pencereyi kapatmak indirmeyi kesmez.
- Dinleme geçmişi son 200 farklı radyo, podcast, kitap veya yerel medyayı yeniden açar. GETEM geçici proxy adresleri saklanmaz; kitap bağlantısı yeniden oluşturulur. Geçmişi temizlemek medya dosyalarını silmez.
- Yeni pencereler standart Windows kontrolleri kullanır. Enter oynatır, Tab düğmelere geçer; F5/F6 ses ve F8 durdur/oynat işlevleri korunur. Liste yenilemeleri seçimi korur, odağı değiştirmez.
- Hakkında penceresine, yardım dosyalarına ve README’ye özgün freeAudio NVDA eklentisinin geliştiricisi Çağrı Doğan için teşekkür ve kaynak bağlantısı eklendi. Mevcut telif ve lisans bildirimleri korunur.
- Yetkili bir imzalama hizmeti edinildiğinde bağlanabilmesi için isteğe bağlı harici imzalama kancası eklendi. Uygulama paketlemeden, kurulum dosyası SHA-256 hesaplanmadan önce imzalanıp doğrulanabilir. Bu sürümde bağlı sertifika olmadığı için yayımlanan paketler imzasızdır.

# 1.2.2

- Podcast arama sonuçlarındaki bölüm önizleme menüsüne Bölümü indir eklendi. İçerik tuşu veya Shift+F10 ile erişilebilir; indirmek için abone olmak gerekmez. Abone olunan bölüm listesindeki indirme de aynı yöntemi kullanır.
- İndirme tamamlandığında ve dosya zaten mevcut olduğunda tam dosya yolu bildirilir. Aynı bölümün eşzamanlı tekrar indirilmesi engellenir; seçim değiştirilse de başlatılan bölüm indirilir.
- İndirmeler geçici dosyaya yazılıp tamamlanınca son adına taşınır. Boş, eksik veya HTML hata yanıtları başarı olarak bildirilmez; hata durumunda geçici dosya temizlenir. Önceki dosyalar korunur.
- Aynı başlıklı farklı bölümlerin dosya adları ayırt edilir. İndirme bitiminde liste seçimi yoksa düğme yanlışlıkla etkinleştirilmez; kapatılmış pencereye gelen sonuçlar güvenle yok sayılır.

# 1.2.1

- Yeni kurulumlarda tüm kullanıcılar / Program Files varsayılandır. Kurulum kipinde yalnız bu kullanıcı seçilirse LocalAppData/Programs kullanılır. Windows yönetici izni yalnız tüm kullanıcılar kurulumunda gerekir.
- Mevcut kurulumların kapsamı ve konumu güncellemede korunur. Eski sürümün kapsam belirtmeyen güncelleyicisi de desteklenir.
- Uygulama içi güncelleme, kurulum kapsamını açıkça iletir. Program Files kurulumu tüm kullanıcılar olarak, kullanıcıya özel kurulum aynı kullanıcı kapsamında güncellenir.
- Ayarlar, favoriler, kitaplıklar ve ilerleme yine her Windows kullanıcısının AppData/Roaming/freeAudioDesktop klasöründedir. Kurulum ve kaldırma bu verileri taşımaz veya silmez.
- Farklı kapsamda mevcut kurulum varsa ikinci bir kopya oluşturulmaz. Kapsamı değiştirmek için eski uygulamayı kaldırıp yeniden kurun; profil verileri korunur.
- Windows derlemesinde eski kullanıcı kurulumundan yükseltme, varsayılan Program Files kurulumu, iki kapsamın güncellenmesi ve kapsam çakışmalarının engellenmesi test edilir.

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
