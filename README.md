# freeAudio Desktop 1.0.0

Türkçe ve İngilizce arayüzlü, Windows 10/11 x64 için bağımsız freeAudio uyarlaması.
NVDA'nın veya ayrı bir Python kurulumunun bulunması gerekmez.

## Çalıştırma

- Taşınabilir: ZIP dosyasını yazılabilir bir klasöre tamamen çıkarın. `freeAudioDesktop.exe` dosyasını açın. ZIP içinden doğrudan çalıştırmayın. `portable.flag` dosyasını koruyun.
- Kurulum: `win64-setup.exe` dosyasını açın. Kullanıcı hesabınıza kurulur, yönetici yetkisi istemez. Başlat menüsünden çalıştırın.
- Ana pencerede **Kütüphaneyi aç**, **Ayarlar**, **Komutlar ve kısayollar**, **Bildirim geçmişi**, **Dil / Language**, **Profil yedekleme ve geri yükleme** ve **Yardım** düğmeleri bulunur.
- Dili değiştirince uygulamayı kapatıp yeniden açın.
- Kütüphanenin Kapat düğmesi kütüphaneyi gizler; çalma ve zamanlayıcılar çalışır. Ana pencerenin Çıkış düğmesi uygulamayı tamamen kapatır ve kayıtları durdurur.

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
