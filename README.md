# freeAudio Desktop 1.2.1

Türkçe ve İngilizce arayüzlü, Windows 10/11 x64 için bağımsız freeAudio uyarlaması.
NVDA'nın veya ayrı bir Python kurulumunun bulunması gerekmez.

## Çalıştırma

- Taşınabilir: ZIP dosyasını yazılabilir bir klasöre tamamen çıkarın. `freeAudioDesktop.exe` dosyasını açın. ZIP içinden doğrudan çalıştırmayın. `portable.flag` dosyasını koruyun.
- Kurulum: `win64-setup.exe` dosyasını açın. Yeni kurulumda önerilen Tüm kullanıcılar seçeneği Program Files klasörünü kullanır ve Windows yönetici izni ister. Yalnız bu kullanıcı seçeneği LocalAppData/Programs klasörünü kullanır. Başlat menüsünden çalıştırın.
- Ana pencerede **Kütüphaneyi aç**, **Ayarlar**, **Komutlar ve kısayollar**, **Bildirim geçmişi**, **Dil / Language**, **Profil yedekleme ve geri yükleme** ve **Yardım** düğmeleri bulunur.
- Dili değiştirince uygulamayı kapatıp yeniden açın.
- Kütüphanenin Kapat düğmesi kütüphaneyi gizler; çalma ve zamanlayıcılar çalışır. Ana pencerenin Çıkış düğmesi uygulamayı tamamen kapatır ve kayıtları durdurur.

## Ana pencereden ses ve yeni görünüm

Kütüphaneyi açmadan **F5** ile sesi 5 puan azaltın, **F6** ile 5 puan artırın. Aynı işlemler Oynatma grubundaki **Sesi azalt** ve **Sesi artır** düğmeleriyle yapılabilir. **Ses düzeyi (%)** alanına Tab ile ulaşabilir, oklarla değiştirebilir veya değer yazıp Enter ile uygulayabilirsiniz. Kütüphane ve genel ses kısayollarındaki değişiklikler de bu alanda görünür. Sayı yazarken otomatik yenileme yazınızı değiştirmez.

Kütüphanedeki mevcut 0–200 aralığı korunur; 100 üzeri yükseltmedir ve yeniden açılışta kalıcı tercih 100 ile sınırlıdır. Ana pencere Oynatma ve Kütüphane ve uygulama gruplarına ayrılmıştır. Eski düğmelerin kendi aralarındaki Tab sırası ve kütüphanenin sekmeleri korunur. Dar pencerede düğmeler tek sütuna geçer; gerekirse dikey kaydırma kullanılır. Windows sistem renkleri ve native kontroller korunur.

## Odağı değiştirmeden durdurma ve yeniden oynatma

Ana pencere ve kütüphanede **F8** çalan veya bağlanmakta olan medyayı durdurur. Yeniden F8 son dinleneni açar. Aynı düğme **Oynatmayı durdur (F8)** ile **Son dinleneni oynat (F8)** arasında etiket değiştirir; odak bu düğmede kalır. Boşluk veya Enter ile aynı düğmeyi tekrar etkinleştirebilirsiniz. Durdurma henüz tamamlanmamışsa ikinci basış yeniden oynatmayı sıraya alır; üçüncü basış bu isteği iptal eder. F8'i basılı tutmak geçişleri tekrarlamaz.

Ayrı **Oynat / duraklat / sürdür** düğmesi yüklü medyayı duraklatır ve sürdürür. Genel **Ctrl+Alt+Shift+S** her zaman yalnızca durdurur. Bağımsız radyo kayıtları bu oynatma işlemlerinden etkilenmez. Kayıtlı son medya yoksa önce kütüphaneden bir medya seçin.

## Güncelleme

Ayarlardaki **Başlangıçta güncellemeleri otomatik denetle** seçeneği açıkken, uygulama açıldıktan yaklaşık 5 saniye sonra arka planda denetim yapılır. Yeni sürüm varsa ekran okuyucuya bir kez bildirilir; ana penceredeki güncelleme düğmesi sürüm numarasıyla indirme seçeneğine dönüşür. Odak ve çalma korunur. Bu düğmeden indirme/kurulum seçeneklerini açabilirsiniz. İnternet yoksa veya yeni sürüm bulunmazsa başlangıçta ileti verilmez. Siz seçmeden indirme ya da kurulum başlatılmaz.

**Güncellemeleri denetle** yeni sürüm bulunduğunda indirme seçeneklerini sunar. Kurulu sürüm **Güncellemeyi indir ve kur** ile dosyayı indirir, boyutunu ve GitHub SHA-256 özetini doğrular, ayarları kaydeder ve kurulumdan sonra yeniden açılır. İndirme iptal edilebilir. Taşınabilir sürüm yeni ZIP dosyasını indirir; uygulamayı kapatıp ZIP dosyasını açarken kendi `data` klasörünüzü koruyun.

1.0.1'den bu özelliğe geçmek için 1.1.0 kurulumunu bir kez elle çalıştırın. Sonraki sürümler uygulama içinden indirilebilir. Paketler henüz dijital imzalı değildir; dosya özeti doğrulaması yayıncı imzası yerine geçmez. İmzalama durumu: [SIGNING.md](SIGNING.md).

## Anlık radyo kaydı

Radyo veya Favoriler listesindeki sağ tık menüsünü açın. Klavyede aynı menüye Uygulamalar tuşu veya Shift+F10 ile ulaşabilirsiniz.
**Dinlenen istasyonun anlık kaydını başlat** seçeneği o anda çalan radyoyu kaydeder; listede başka bir istasyonu seçmek kaynağı değiştirmez.
Ses verisi alındığında kayıt başladı bildirimi gelir. Durdurmak için aynı menüdeki **Anlık kaydı durdur** seçeneğini kullanın.
**Kayıt klasörünü aç** dosyaya ulaşmanızı sağlar; durdurma bildirimi kaydedilen dosyanın tam yolunu verir.
Kayıt sırasında dinlemeyi durdurmak veya başka istasyona geçmek kaydı değiştirmez. Her kayıt ayrı dosyaya yazılır.
Podcast, sesli kitap ve yerel dosyalar için bu başlatma seçeneği kapalıdır. Bağlantı veya klasör hatası başarı bildirimi yerine hata verir.
Kayıt işlemi sürerken yinelenen tıklamalar ikinci bir kayıt başlatmaz. Mevcut Ctrl+Alt+Shift+E kısayolu da kullanılabilir.

## Kurulum kapsamı

Yeni tüm kullanıcılar kurulumu varsayılan olarak `C:\Program Files\freeAudio Desktop` konumundadır. Yalnız bu kullanıcı kurulumu `%LOCALAPPDATA%\Programs\freeAudio Desktop` konumundadır. Mevcut kurulumu güncellerken önceki kapsam ve konum korunur; eski kullanıcı kurulumları otomatik olarak taşınmaz.

Program Files'a geçmek için önce kullanıcıya özel eski uygulamayı Windows'un uygulama kaldırma bölümünden kaldırın, ardından kurulumu yeniden başlatıp Tüm kullanıcılar seçin. Ayarlar ve favoriler kaldırılmaz. İki kapsamın bu hesapta yan yana kurulması engellenir. İsterseniz geçişten önce uygulamanın profil yedekleme işleviyle yedek alın.

Kurulu sürümün kullanıcı verileri her iki kipte de `%APPDATA%\freeAudioDesktop` altında kalır. Tüm kullanıcılar kurulsa bile herkes kendi profilini kullanır. Program Files içindeki uygulama normal kullanıcı yetkileriyle çalışır; yönetici izni kurulum ve program dosyası güncellemeleri içindir. Taşınabilir sürümün `data` klasörü davranışı değişmez.

## Veri ve yedekleme

Taşınabilir sürüm ayarlar ve kitaplıkları EXE yanındaki `data` klasöründe tutar.
Kurulu sürüm `%APPDATA%\freeAudioDesktop` klasörünü kullanır. Kaldırma bu klasörü silmez.
Kayıt ve indirme klasörleri kaynak uygulamadaki ayarlara tabidir; taşınabilir kullanımda bu yolları da USB diskinize ayarlayın.
Taşınabilir profilin tamamen taşınması için yerel müzik yollarını yeni bilgisayarda yeniden seçmeniz gerekebilir.
GETEM oturum bilgileri Windows hesabına bağlı şifreleme kullanabilir; başka bilgisayarda tekrar giriş gerekebilir.
Profil yedekleme ve geri yükleme düğmesi ayar, favori, abonelik, kitaplık, ilerleme ve yer imi notlarını ZIP olarak yedekler. İndirilen medya, kayıtlar ve hesap giriş bilgileri dahil değildir.
Geri yükleme sonraki açılışta uygulanır; önce mevcut profilin ayrıca yedeği alınır. Sürüm değişimindeki ilk açılışta da `backups` klasörüne önceki profil yedeklenir.
Tam dosya yedeği için uygulama kapalıyken veri klasörünü ayrıca kopyalayabilirsiniz.

## Klavye ve ekran okuyucu

Tab / Shift+Tab ile kontroller, Ctrl+Tab ile kütüphane sekmeleri arasında gezinin.
İstasyon veya bölüm listesinde Enter ile oynatın. Kütüphanede F1 yardım açar.
Genel kısayollar bağımsız uygulamaya göre düzenlenmiştir. Önceki sürümlerde elle atadığınız bileşimler korunur. Windows tarafından ayrılan F12 genel kısayol olarak kullanılamaz.

| İşlem | Varsayılan kısayol |
| --- | --- |
| Radyo penceresi | Ctrl+Alt+Shift+R |
| Podcast | Ctrl+Alt+Shift+O |
| Sesli kitaplar | Ctrl+Alt+Shift+L |
| Müzik kutusu | Ctrl+Alt+Shift+U |
| Oynat / duraklat | Ctrl+Alt+Shift+P |
| Durdur | Ctrl+Alt+Shift+S |
| Önceki / sonraki | Ctrl+Alt+Shift+Sol / Sağ ok |
| Ses artır / azalt | Ctrl+Alt+Shift+Yukarı / Aşağı ok |
| Çalanın bilgisi | Ctrl+Alt+Shift+I |
| Kaydı aç / kapat | Ctrl+Alt+Shift+E |
| Yer imi ekle | Ctrl+Alt+Shift+B |
| Hız azalt / artır | Ctrl+Alt+Shift+F7 / F8 |
| Perde azalt / artır | Ctrl+Shift+F7 / F8 |
| Canlı yayında geri / ileri | Ctrl+Alt+Shift+J / K |

**Komutlar ve kısayollar** bölümünden her komutu çalıştırabilir, kısayolu değiştirebilir veya boş bırakarak kapatabilirsiniz.
NVDA eklentisiyle aynı anda kullanırsanız aynı kısayolun iki uygulamada birden işlenmesini önlemek için birinin kısayollarını değiştirin.
Windows'un kaydetmeyi reddettiği kısayollar açıkça listelenir. Kontroller ve komut çalıştırma düğmesi kullanılmaya devam eder.
Bildirimler çalışan NVDA/JAWS'a iletilir; diğer ekran okuyucular için Windows erişilebilirlik bildirimi kullanılır.
**Uygulama açıldığında son dinleneni sürdür** bu uygulamanın açılışıyla ilgilidir; NVDA'nın açılmasını beklemez.
Braille ayarı açıksa desteklenen ekran okuyucunun braille arayüzüne mesaj gönderilir. Braille aygıtı kullanmıyorsanız kapalı bırakın; bu seçenek uygulamayı NVDA'ya bağımlı yapmaz.
Her bildirim **Bildirim geçmişi** bölümünden tekrar okunabilir ve kopyalanabilir.

## Özellikler ve test durumu

Radyo, favoriler, podcast'ler, GETEM/LibriVox/Gutenberg sesli kitapları, yerel müzik,
yer imleri, kayıtlar, zamanlayıcılar, zaman kaydırma, ses efektleri, ses tanıma,
ses yansıtma ve arka plan müziğinin kaynak modülleri korunmuştur.
Bir özelliğin arayüzde bulunması tüm servislerle test edildiği anlamına gelmez.
GETEM için kendi hesabınız gerekir. Müzik tanıma ve bazı MP3 dönüştürmeleri için
Ayarlar'dan ayrıca FFmpeg yolu seçmeniz gerekebilir; FFmpeg bu pakete dahil değildir.
Zamanlanmış işler uygulama açıkken çalışır; bilgisayar kapalıyken veya uygulama kapalıyken başlamaz.
Canlı servisler erişilebilirlik ve yayın adresi değişikliklerinden etkilenebilir.

Bu sürüm NVDA, Narrator, JAWS ve fiziksel braille ekranla tam kabul testinden geçmemiştir.
Metinli yer imi notları, okuma bitmeden medyaya dönmemek için seçili Windows SAPI sesiyle okunur; ekran okuyucunun kendi sesinden farklı olabilir.
Genel kısayollar başka bir uygulama aynı bileşimi kullanıyorsa kaydedilemeyebilir. Liste her komutun bileşimini ve kullanılamama durumunu gösterir; Varsayılan kısayolu kullan düğmesiyle seçili atamayı sıfırlayabilirsiniz.
EXE ve kurulum paketi kod imzalı değildir.

## Güncelleme

Uygulamanın güncelleme denetimi NVDA eklenti kanalından ayrıdır. Kararlı sürümler için `selcukucar/freeAudio-desktop` GitHub Releases adresi yapılandırılmıştır. Yayın henüz yoksa daha yeni sürüm bulunamadığı bildirilir. Hiçbir NVDA eklentisi indirilmez veya kurulmaz.
Yeni kurulum paketini mevcut kurulumun üzerine kurabilirsiniz; kullanıcı verileri ayrı kalır.
Taşınabilir güncellemede uygulamayı kapatın, `data` klasörünü yedekleyin ve yeni paketi ayrı klasöre çıkarıp veri klasörünüzü taşıyın.
Yayın deposu yokken otomatik denetim kontrolleri ayarlarda gizlidir. Yayın deposu oluşturulduğunda geliştirici `release-channel.json` içindeki `repository` alanını `sahip/depo` biçiminde yapılandırır.
Denetleyici yeni kararlı sürümün sayfasını kullanıcı onayıyla açar; arka planda EXE çalıştırmaz.
Gelecekteki yayın süreci ve hazırlanan GitHub iş akışı `RELEASING.md` dosyasında anlatılır.

## Kaynaktan geliştirme

Windows x64 ve Python 3.14 ile doğrulandı:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python tools/fetch_vendor.py
.venv\Scripts\python prepare.py
.venv\Scripts\python main.py --data-dir .test-profile --language tr
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python main.py --smoke-test --data-dir .smoke-profile --language en
.venv\Scripts\python build.py --build-dir .build --output-dir releases --iscc "C:\tools\Inno Setup\ISCC.exe"
```

`--smoke-test` sekmeleri, ayar panelini, komut kataloğunu ve ses aygıtlarını açar; sonuçları test profilindeki `smoke-test.json` dosyasına yazar.
GitHub kaynak ağacı büyük ikili bağımlılıkları içermez; `tools/fetch_vendor.py` özgün deponun sabitlenmiş commit'inden indirir ve her dosyanın SHA-256 değerini doğrular. Kaynak ZIP bu dosyaları zaten içerir.
`smoke-error.txt` veya `startup-error.txt` oluşmuşsa test başarısızdır.
Üretim ayarlarınız yerine ayrı `--data-dir` kullanın.

`vendor/freeAudio` özgün motor ve içerik modülleridir; masaüstü uyarlamasında ayar metinleri, yükleme sırasında tercih koruması ve ses alt sürecinin boru tanıtıcıları için küçük düzeltmeler yapılmıştır. `desktop` bağımsız Windows hizmetlerini sağlar.
Yeni özellikleri mümkünse `desktop` altında ayrı modüller halinde ekleyin.
Veri biçimi değişirse `storage.py` içindeki `schema_version` için kayıpsız taşıma ekleyin.
Yayın öncesi kabul koşulları ve bilinen eksikler `TEST-REPORT.md` dosyasındadır.

Kaynak: https://github.com/Surveyor123/freeAudio
Temel commit: f1ade61be7e5badd43dd9b58cba80ae26959148b
Özgün telif ve GPL-2.0 lisans metni korunmuştur. Üçüncü taraf bileşenler için `THIRD-PARTY.md` dosyasına bakın.

## English quick start

Extract the entire portable ZIP to a writable folder and run `freeAudioDesktop.exe`, or run the per-user setup.
Use **Dil / Language** to select English, then restart. Python and NVDA are not required to launch the application.
Portable data is stored in `data` next to the executable; installed data is stored in `%APPDATA%\freeAudioDesktop`.
Open Library exposes the original media modules. Commands and Shortcuts allows running commands and changing global hotkeys.
Closing the library keeps playback running; Exit on the main window shuts down playback and recording.
The packages are unsigned. Full screen-reader, braille and advanced-feature acceptance testing remains outstanding.
Default hotkeys use Ctrl+Alt+Shift instead of the NVDA add-on's Windows-key bindings. Existing custom bindings remain unchanged. The command list shows assigned keys and registration failures. F12 is reserved by Windows.
Stable updates are checked through GitHub Releases in `selcukucar/freeAudio-desktop`. Never install an NVDA add-on as a desktop update.

The main **Play / pause / resume** button restarts the last saved media after Stop or F8. Use Tab to focus it, then Space or Enter. For loaded media it pauses or resumes; rapid activations are independent of global hotkey repeat actions.

F8 in the main window and library toggles Stop / Play Last Media without moving focus. The same button changes its label and keeps focus. A second press during a slow stop queues playback, and a third cancels that queued request. Held-key repeats are ignored; Ctrl+Alt+Shift+S remains stop-only.

When automatic startup checks are enabled, the application checks after about five seconds. A new release is announced once and shown on the update button, without a modal window, focus change or playback interruption. Use the button to open download/install options. No download starts without your choice. Offline or up-to-date startups remain quiet.

Main-window volume: F5 decreases and F6 increases by five without opening the library. The native Volume (%) field accepts arrows or a typed value committed with Enter. Library/global changes stay synchronized; active text edits are preserved. Native playback/application groups, larger type and buttons, and adaptive columns improve the presentation while keeping the existing content windows, commands and tab sequence.

New setup defaults to all users in Program Files and requests Windows elevation. Current-user setup remains available in LocalAppData/Programs. Updates preserve the existing scope and directory. To change scope, uninstall the previous application before reinstalling; Roaming profile data is retained. Both modes keep each user’s settings in %APPDATA%/freeAudioDesktop. Portable data behavior is unchanged.
