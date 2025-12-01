# 🚀 دليل التشغيل السريع - NYC Taxi Streaming Pipeline

> هذا الملف لزميلتك أو أي شخص يريد تشغيل المشروع للمرة الأولى

---

## ⚡ خطوات التشغيل (5 دقائق)

### الخطوة 1: Clone المشروع
```bash
git clone https://github.com/abdulrahman532/nyc-taxi-data-pipeline.git
cd nyc-taxi-data-pipeline/streaming/docker
```

### الخطوة 2: بناء وتشغيل Docker
```bash
# بناء الـ images (مهم جداً - لا تتخطى هذه الخطوة!)
docker compose build

# تشغيل جميع الخدمات
docker compose up -d

# التحقق من الحالة
docker compose ps
```

### الخطوة 3: انتظار البدء
```bash
# انتظر حوالي 60-90 ثانية
# يمكنك مراقبة التقدم:
docker compose logs -f
```

### الخطوة 4: الوصول للتطبيقات

| التطبيق | الرابط | الوصف |
|---------|--------|-------|
| 📊 Dashboard | http://localhost:8501 | لوحة التحكم الرئيسية |
| 📖 API Docs | http://localhost:8000/docs | توثيق الـ API |
| 📈 Kafka UI | http://localhost:8085 | واجهة إدارة Kafka |
| ⚡ Spark UI | http://localhost:8081 | واجهة Spark |

### الخطوة 5: إرسال بيانات تجريبية
```bash
curl -X POST http://localhost:8000/api/v1/trips \
  -H "Content-Type: application/json" \
  -d '{
    "VendorID": 1,
    "tpep_pickup_datetime": "2025-12-01T10:30:00",
    "tpep_dropoff_datetime": "2025-12-01T10:45:00",
    "passenger_count": 2,
    "trip_distance": 3.5,
    "PULocationID": 161,
    "DOLocationID": 234,
    "payment_type": 1,
    "fare_amount": 15.50,
    "tip_amount": 3.00,
    "total_amount": 20.30
  }'
```

---

## ❌ حل المشاكل الشائعة

### المشكلة: "Cannot connect to Docker daemon"
```bash
sudo systemctl start docker
```

### المشكلة: "Port already in use"
```bash
# اعثر على العملية:
sudo lsof -i :8000  # (أو أي منفذ آخر)

# أوقف العملية:
sudo kill -9 <PID>
```

### المشكلة: Dashboard لا يعرض بيانات
```bash
# امسح البيانات القديمة:
docker exec redis redis-cli FLUSHALL

# أو من Dashboard نفسه، اضغط على زر "Clear Redis Data"
```

### المشكلة: Spark job يفشل
```bash
# تحقق من الـ logs:
docker compose logs spark-job

# أعد تشغيل الخدمة:
docker compose restart spark-job
```

### المشكلة: Build يفشل
```bash
# أعد البناء بدون cache:
docker compose build --no-cache
```

---

## 🔧 الأوامر المفيدة

```bash
# مشاهدة logs لكل الخدمات
docker compose logs -f

# مشاهدة logs لخدمة معينة
docker compose logs -f spark-job

# إيقاف جميع الخدمات
docker compose down

# إيقاف وحذف البيانات
docker compose down -v

# إعادة تشغيل خدمة
docker compose restart <service-name>

# فحص صحة الـ API
curl http://localhost:8000/health

# فحص Redis
docker exec redis redis-cli ping
```

---

## 📋 المتطلبات

- Docker Desktop أو Docker Engine + Docker Compose
- 8GB RAM كحد أدنى
- المنافذ التالية متاحة: 6379, 7077, 8000, 8081, 8082, 8085, 8501, 9092

---

## 📚 للمزيد من التفاصيل

- [README الكامل](./README.md) - التوثيق الشامل
- [دليل الأخطاء](../docs/ERRORS_AND_FIXES.md) - تقرير الأخطاء والإصلاحات
- [توثيق Kafka KRaft](./docker/KAFKA_KRAFT_DOCUMENTATION.md) - شرح إعدادات Kafka

---

*آخر تحديث: 1 ديسمبر 2025*
