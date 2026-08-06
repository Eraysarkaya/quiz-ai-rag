# Deney Sonuçları

**Rapor Tarihi:** 2026-03-23 20:27  
**Hakem Model:** GPT-OSS 120B  
**Ortak Bağlam Dosyası:** `shared_rag_contexts.json`  
**Değerlendirilen Konu Sayısı:** 100  
**Retrieval Ayarları:** `top_k = 5`, `min_score = 0.25`

## 1. Genel Değerlendirme

Bu deneyde 100 sabit bilim konusu için retrieval süreci bir kez çalıştırılmış, elde edilen bağlamlar dondurulmuş ve tüm üretici modeller aynı ortak bağlam dosyası üzerinden değerlendirilmiştir. Bu nedenle gözlenen farkların retrieval varyansından değil, esas olarak üretici model performansından kaynaklandığı kabul edilmektedir.

Elde edilen sonuçlara göre en yüksek genel skor `0.795` ile **LLaMA 3.3 70B** modelinde gözlenmiştir. Bununla birlikte **LLaMA 4 Scout** modeli `0.793` genel skor ile çok yakın bir performans sergilemiştir. Bu nedenle üst sıradaki iki model arasında belirgin bir üstünlükten ziyade, birbirine oldukça yakın bir başarı düzeyi bulunduğu değerlendirilmelidir.

## 2. Değerlendirme İstemi Özeti

Sonuçların elde edilmesinde bağımsız hakem model olarak `GPT-OSS 120B` kullanılmıştır. Hakem modele üretici model adı verilmemiş; her soru için yalnızca içerik tabanlı kör değerlendirme istemleri sunulmuştur. Değerlendirme dört ayrı metrik üzerinden yürütülmüş; soru kalitesi, cevap doğruluğu, çeldirici kalitesi ve cevap ilgisi bağımsız olarak puanlanmıştır.

Hakem istemleri kısa rubrikler içerecek biçimde tasarlanmış, modelden yalnızca sayısal skor üretmesi istenmiştir. Böylece sonuçların yapılandırılmış, karşılaştırılabilir ve model kimliğinden arındırılmış biçimde elde edilmesi sağlanmıştır. Kullanılan ayrıntılı judge promptları metodoloji raporunda ayrı başlık altında sunulmuştur.

## 3. Model Karşılaştırma Tablosu

| Sıra | Model | Parametre | Soru Kalitesi | Cevap Doğruluğu | Seçenek Kalitesi | Cevap İlgisi | Genel |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | LLaMA 3.3 70B | 70B | 0.896 | 0.925 | 0.375 | 0.985 | 0.795 |
| 2 | LLaMA 4 Scout | 17B MoE | 0.883 | 0.935 | 0.378 | 0.978 | 0.793 |
| 3 | Qwen 3 32B | 32B | 0.832 | 0.930 | 0.360 | 0.968 | 0.773 |
| 4 | LLaMA 3.1 8B | 8B | 0.836 | 0.873 | 0.408 | 0.899 | 0.754 |

Genel skor, dört ana metriğin eşit ağırlıklı ortalaması alınarak hesaplanmıştır.

## 4. Metrik Bazlı Bulgular

| Metrik | En Yüksek Skor | Model |
|---|---:|---|
| Question Quality | 0.896 | LLaMA 3.3 70B |
| Answer Correctness | 0.935 | LLaMA 4 Scout |
| Distractor Quality | 0.408 | LLaMA 3.1 8B |
| Answer Relevancy | 0.985 | LLaMA 3.3 70B |

Metrik bazlı dağılım incelendiğinde, özellikle **cevap doğruluğu** ve **cevap ilgisi** ölçütlerinde tüm modellerin yüksek değerlere ulaştığı görülmektedir. Buna karşılık **seçenek kalitesi (distractor quality)** metriği tüm modeller için belirgin biçimde düşük kalmıştır. Bu durum, yanlış fakat ikna edici çeldirici üretiminin, soru gövdesi oluşturma ya da doğru cevabı belirleme süreçlerine göre daha zor bir problem olduğunu göstermektedir.

## 5. Modeller Arası Farkların Yorumu

| Model | Genel Skor | En İyi Modele Fark |
|---|---:|---:|
| LLaMA 3.3 70B | 0.795 | 0.000 |
| LLaMA 4 Scout | 0.793 | -0.002 |
| Qwen 3 32B | 0.773 | -0.023 |
| LLaMA 3.1 8B | 0.754 | -0.041 |

Tablo incelendiğinde ilk iki model arasındaki farkın yalnızca `0.002` olduğu görülmektedir. Bu nedenle sonuçlar, LLaMA 3.3 70B modelinin küçük bir ortalama üstünlük sergilediğini, ancak LLaMA 4 Scout modelinin de pratik olarak benzer düzeyde performans sunduğunu göstermektedir. Qwen 3 32B modeli orta düzeyde rekabetçi bir sonuç verirken, LLaMA 3.1 8B modeli daha küçük parametre boyutunun etkisiyle genel sıralamada son sırada yer almıştır.

Bununla birlikte, daha küçük parametreli LLaMA 3.1 8B modelinin **distractor quality** metriğinde en yüksek skora ulaşmış olması dikkat çekicidir. Bu bulgu, model kapasitesi ile tüm alt görevlerde doğrusal bir üstünlük ilişkisi bulunmadığını, bazı alt görevlerde daha küçük modellerin de rekabetçi davranabildiğini göstermektedir.

## 6. İstatistiksel Gözlemler

Sonuç dosyalarında yer alan dağılımlar incelendiğinde, `question_quality`, `answer_correctness` ve `answer_relevancy` metriklerinde medyan değerlerin çoğu model için `0.9` ile `1.0` aralığında toplandığı görülmektedir. Buna karşılık `distractor_quality` metriğinde standart sapmanın yüksek olması, çeldirici üretim başarısının soru örnekleri arasında daha değişken olduğunu göstermektedir.

Bu görünüm, sistemin doğru cevabı ve konu uyumunu çoğu durumda başarılı biçimde kurabildiğini; ancak yanlış seçeneklerin kalite düzeyinin soru bazında daha kırılgan kaldığını düşündürmektedir.

## 7. Akademik Değerlendirme

Bu deneyin en güçlü yönü, tüm modellerin aynı donmuş bağlamlar üzerinde sınanmış olmasıdır. Böylece sonuçların retrieval farklılıklarından arındırılmış biçimde yorumlanabilmesi mümkün hale gelmiştir. Bu çerçevede elde edilen bulgular, soru üretim performansı açısından büyük modellerin genel olarak avantajlı olduğunu, ancak bu avantajın her metrikte aynı ölçüde ortaya çıkmadığını göstermektedir.

Özellikle genel skorların birbirine yakın seyretmesi, model seçiminin yalnızca toplam puan üzerinden değil, alt görevlerin doğasına göre de yapılması gerektiğine işaret etmektedir. Eğer öncelik doğru cevap üretimi ve yüksek konu ilgisi ise daha büyük modeller öne çıkmaktadır. Buna karşılık çeldirici üretiminin güçlendirilmesi hedefleniyorsa, bu bileşenin ayrıca iyileştirilmesi veya özel olarak optimize edilmesi gerekmektedir.

## 8. Geçerlilik Notu

Bu rapor yalnızca `shared_contexts+production_mcq_generator` üretim yoluna sahip ve tüm metrikleri `100/100` tamamlanmış deney dosyalarından üretilmiştir. Dolayısıyla sonuçlar, konu-başlıklı fallback üretimlerden, modelden modele değişen retrieval akışlarından veya eksik judge çıktılarından etkilenmemektedir.

Bununla birlikte puanlamanın tek bir LLM judge ile yapılmış olması, sonuçların mutlak insan değerlendirmesi yerine tutarlı ve standartlaştırılmış bir otomatik değerlendirme olarak yorumlanmasını gerektirmektedir. Buna rağmen tüm modellerin aynı judge ve aynı istem çerçevesi ile puanlanmış olması, göreli sıralamanın akademik açıdan anlamlı bir karşılaştırma sunduğunu göstermektedir.
