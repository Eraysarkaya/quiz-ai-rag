# 🎓 GitHub Kurulum Rehberi - Sıfırdan Başlayanlar İçin

Bu rehber seni adım adım yönlendirecek. Her adımı tamamla, sonrakine geç.

---

## 📋 ADIM 1: Git Programını İndir ve Kur

Git, bilgisayarında çalışan bir programdır. GitHub ise internetteki depolama alanı.

### 1.1 İndirme
1. Tarayıcıda bu linke git: **https://git-scm.com/download/win**
2. "Click here to download" butonuna tıkla
3. İndirilen `.exe` dosyasını çalıştır

### 1.2 Kurulum (Varsayılanları Kabul Et)
- Kurulum sihirbazında **"Next"** butonuna bas (8-9 kez)
- Varsayılan ayarları değiştirme
- Son ekranda **"Install"** → **"Finish"**

### 1.3 Kurulumu Doğrula
**PowerShell'i KAPAT ve YENİDEN AÇ**, sonra yaz:
```powershell
git --version
```
✅ Başarılı çıktı: `git version 2.x.x`

---

## 📋 ADIM 2: GitHub Hesabı Oluştur

### 2.1 Kayıt Ol
1. Tarayıcıda: **https://github.com/signup**
2. Email adresini gir
3. Şifre oluştur (min 8 karakter)
4. Kullanıcı adı seç (örnek: `eraydev`)
5. Email doğrulama kodunu gir

### 2.2 Giriş Yap
- https://github.com adresinden giriş yap

---

## 📋 ADIM 3: Git'i Bilgisayarında Ayarla

PowerShell'de şu komutları çalıştır (kendi bilgilerini yaz):

```powershell
git config --global user.name "Senin Adın"
git config --global user.email "senin@email.com"
```

Örnek:
```powershell
git config --global user.name "Eraysarkaya"
git config --global user.email "eraysarkaya20@gmail.com"
```

---

## 📋 ADIM 4: GitHub'da Yeni Repo Oluştur

### 4.1 Repo Oluştur
1. GitHub'da sağ üstte **"+"** butonuna tıkla
2. **"New repository"** seç
3. Repository name: `quiz-ai`
4. **Private** seç (sadece sen görebilirsin)
5. ⚠️ "Add a README file" işaretleme!
6. **"Create repository"** butonuna tıkla

### 4.2 Repo URL'sini Kopyala
Açılan sayfada şöyle bir URL göreceksin:
```
https://github.com/KULLANICI_ADIN/quiz-ai.git
```
Bu URL'yi bir yere not et.

---

## 📋 ADIM 5: Projeyi GitHub'a Yükle

PowerShell'de şu komutları **SIRAYLA** çalıştır:

```powershell
# 1. Proje klasörüne git
cd c:\proje\quiz-ai

# 2. Git deposu başlat
git init

# 3. .gitignore oluştur (gereksiz dosyaları hariç tut)
# Bu komutu çalıştır, dosya otomatik oluşacak
@"
# Dependencies
node_modules/
.next/
__pycache__/
*.pyc
.venv/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# Cache
*.log
.cache/
"@ | Out-File -FilePath .gitignore -Encoding utf8

# 4. Tüm dosyaları ekle
git add .

# 5. İlk commit (kaydetme)
git commit -m "İlk yükleme - Quiz AI projesi"

# 6. GitHub bağlantısı (KENDİ URL'NİZİ YAZIN!)
git remote add origin https://github.com/Eraysarkaya/quiz-ai.git

# 7. Yükle
git push -u origin master
```

⚠️ **6. adımda** `KULLANICI_ADIN` yerine kendi GitHub kullanıcı adını yaz!

### İlk Push'ta Giriş İsteyecek
- Tarayıcı açılacak, GitHub'a giriş yap
- "Authorize" butonuna tıkla

---

## 📋 ADIM 6: Laptopa Klonla

Laptopda (Git kurulu olmalı):

```powershell
# Masaüstüne veya istediğin yere git
cd c:\proje

# Projeyi indir
git clone https://github.com/Eraysarkaya/quiz-ai.git

# Proje klasörüne gir
cd quiz-ai

# Frontend bağımlılıklarını yükle
cd frontend
npm install
cd ..
```

---

## 🔄 GÜNLÜK KULLANIM

### PC'de Değişiklik Yaptıktan Sonra:
```powershell
cd c:\proje\quiz-ai
git add .
git commit -m "Değişiklik açıklaması"
git push
```

### Laptopda Değişiklikleri Almak İçin:
```powershell
cd c:\proje\quiz-ai
git pull
```

---

## 📝 SIK KULLANILAN KOMUTLAR

| Komut | Ne Yapar |
|-------|----------|
| `git status` | Değişiklikleri gösterir |
| `git add .` | Tüm değişiklikleri hazırlar |
| `git commit -m "mesaj"` | Değişiklikleri kaydeder |
| `git push` | GitHub'a yükler |
| `git pull` | GitHub'dan indirir |

---

## ❓ SORUN GİDERME

### "git is not recognized" hatası
→ Git kurulumundan sonra PowerShell'i kapat ve yeniden aç

### "failed to push" hatası
→ Önce `git pull` yap, sonra `git push`

### "please tell me who you are" hatası
→ ADIM 3'ü atlamışsın, git config komutlarını çalıştır
