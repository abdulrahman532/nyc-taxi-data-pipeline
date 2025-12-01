# 🔍 تقرير الأخطاء والإصلاحات - NYC Taxi Data Pipeline

> تاريخ التقرير: 1 ديسمبر 2025

---

## 📋 جدول المحتويات

1. [أخطاء ملفات SQL](#-أخطاء-ملفات-sql)
2. [مشاكل Docker و التشغيل](#-مشاكل-docker-والتشغيل)
3. [دليل التشغيل الكامل](#-دليل-التشغيل-الكامل)

---

## 🗄️ أخطاء ملفات SQL

### ❌ خطأ 1: خطأ في Syntax - ملف `insight_zone_heatmap.sql`

**الملف:** `nyc_taxi_dbt/models/marts/insights/insight_zone_heatmap.sql`

**المشكلة:** قوس مفقود في الـ `CASE WHEN` statement في السطر 28

```sql
-- ❌ الكود الخاطئ:
case
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.95 then 'Very Hot'
    when percent_rank() over (order by coalesce(p.pickup_count, 0) >= 0.80 then 'Hot'  -- ← قوس مفقود هنا!
    when percent_rank() over (order by coalesce(p.pickup_count, 0)) >= 0.50 then 'Warm'
    else 'Cold'
end as heat_level,
```

**الإصلاح:**
```sql
-- ✅ الكود الصحيح:
case
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.95 then 'Very Hot'
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.80 then 'Hot'  -- ← تم إضافة `) desc`
    when percent_rank() over (order by coalesce(p.pickup_count, 0) desc) >= 0.50 then 'Warm'  -- ← تم إضافة `desc`
    else 'Cold'
end as heat_level,
```

**السبب:** القوس المغلق مفقود بعد `pickup_count, 0)` وكلمة `desc` مفقودة أيضاً

---

### ⚠️ خطأ 2: مشكلة Logic - ملف `stg_trips.sql`

**الملف:** `nyc_taxi_dbt/models/staging/stg_trips.sql`

**المشكلة:** عدم تطابق أنواع البيانات بين `pickup_datetime_raw` و `dropoff_datetime_raw`

```sql
-- ❌ الكود الحالي:
left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::bigint as pickup_datetime_raw,
tpep_dropoff_datetime as dropoff_datetime_raw,  -- ← هذا timestamp وليس bigint!
```

**المشكلة:** 
- `pickup_datetime_raw` يتم تحويله إلى `bigint` (epoch nanoseconds)
- `dropoff_datetime_raw` يبقى كـ `timestamp` 

هذا يسبب مشكلة في `int_trips_validated.sql` حيث يتم استخدام:
```sql
to_timestamp(pickup_datetime_raw / 1000000) as pickup_datetime,
to_timestamp(dropoff_datetime_raw / 1000000) as dropoff_datetime,  -- ← سيفشل!
```

**الإصلاح:**
```sql
-- ✅ الكود الصحيح:
left(date_part(epoch_nanosecond, tpep_pickup_datetime)::varchar, 16)::bigint as pickup_datetime_raw,
left(date_part(epoch_nanosecond, tpep_dropoff_datetime)::varchar, 16)::bigint as dropoff_datetime_raw,
```

---

### ⚠️ خطأ 3: مشكلة Logic - ملف `int_trips_validated.sql`

**الملف:** `nyc_taxi_dbt/models/intermediate/int_trips_validated.sql`

**المشكلة 1:** استخدام `pickup_datetime` و `dropoff_datetime` قبل تعريفهم في الـ WHERE clause

```sql
-- ❌ الكود الخاطئ:
from source
where pickup_datetime is not null  -- ← هذه الأعمدة لم تُعرف بعد في هذه المرحلة!
  and dropoff_datetime is not null
  and dropoff_datetime >= pickup_datetime
```

**الإصلاح:**
```sql
-- ✅ الكود الصحيح:
from source
where pickup_datetime_raw is not null
  and dropoff_datetime_raw is not null
  and dropoff_datetime_raw >= pickup_datetime_raw
```

**المشكلة 2:** استخدام `trip_duration_minutes` قبل تعريفه في الـ `enhanced` CTE

```sql
-- ❌ الكود الخاطئ (في enhanced CTE):
case when trip_duration_minutes > 0  -- ← لم يُعرف بعد في نفس SELECT!
     then trip_distance / (trip_duration_minutes / 60.0) 
     end as speed_mph,
```

**الإصلاح:** يجب نقل حساب `speed_mph` إلى CTE منفصل أو استخدام الحساب المباشر:

```sql
-- ✅ الكود الصحيح:
case when datediff('minute', pickup_datetime, dropoff_datetime) > 0 
     then trip_distance / (datediff('minute', pickup_datetime, dropoff_datetime) / 60.0) 
     end as speed_mph,
```

---

### ⚠️ خطأ 4: مشكلة Logic - ملف `obt_trips.sql`

**الملف:** `nyc_taxi_dbt/models/marts/core/obt_trips.sql`

**المشكلة:** الـ view يستخدم أعمدة غير موجودة في `fct_trips`

```sql
-- ❌ الأعمدة المستخدمة ولكن غير موجودة في fct_trips:
f.is_suspicious_zero_distance
f.is_zero_distance_high_fare
f.is_refund
f.is_extreme_speed
f.tip_percentage
```

هذه الأعمدة موجودة في `int_trips_validated` ولكن لم يتم نقلها إلى `fct_trips`.

**الإصلاح:** إضافة الأعمدة المفقودة إلى `fct_trips.sql`:

```sql
-- ✅ إضافة في fct_trips.sql:
select
    trip_id,
    -- ... الأعمدة الحالية ...
    tip_percentage,
    time_of_day,
    day_type,
    is_suspicious_zero_distance,
    is_zero_distance_high_fare,
    is_refund,
    is_extreme_fare,
    is_extreme_speed,
    speed_mph,
    fare_per_mile
from trips
```

---

### ⚠️ خطأ 5: مشكلة Logic - ملف `agg_yearly.sql`

**الملف:** `nyc_taxi_dbt/models/marts/aggregations/agg_yearly.sql`

**المشكلة:** العمود `airport_trips` مفقود لكن `insight_airport_lifeline.sql` يستخدمه

```sql
-- في insight_airport_lifeline.sql:
airport_trips,  -- ← هذا العمود غير موجود في agg_yearly!
```

**الإصلاح:** إضافة العمود في `agg_yearly.sql`:

```sql
-- ✅ الكود الصحيح:
select
    pickup_year,
    sum(total_trips) as total_trips,
    sum(airport_trips) as airport_trips,  -- ← إضافة هذا السطر
    -- ... باقي الأعمدة ...
```

---

### ⚠️ خطأ 6: مشكلة Logic - ملف `agg_yearly.sql`

**الملف:** `nyc_taxi_dbt/models/marts/aggregations/agg_yearly.sql`

**المشكلة:** العمود `trips_yoy_pct` مفقود لكن `insight_industry_evolution.sql` يستخدمه

```sql
-- في insight_industry_evolution.sql:
trips_yoy_pct,  -- ← هذا العمود غير موجود في agg_yearly!
```

**الإصلاح:** إضافة العمود في `agg_yearly.sql`:

```sql
-- ✅ إضافة حساب Year-over-Year:
select
    pickup_year,
    sum(total_trips) as total_trips,
    round(
        (sum(total_trips) - lag(sum(total_trips)) over (order by pickup_year)) 
        * 100.0 / nullif(lag(sum(total_trips)) over (order by pickup_year), 0), 
        2
    ) as trips_yoy_pct,
    -- ... باقي الأعمدة ...
```

---

### ⚠️ خطأ 7: مشكلة Logic - ملف `agg_monthly.sql`

**الملف:** `nyc_taxi_dbt/models/marts/aggregations/agg_monthly.sql`

**المشكلة:** الأعمدة التالية مطلوبة في `insight_fee_impact.sql` لكنها مفقودة:
- `congestion_revenue`
- `airport_fee_revenue`
- `cbd_fee_revenue`

**الإصلاح:** إضافة الأعمدة في `agg_monthly.sql`:

```sql
-- ✅ إضافة:
round(sum(congestion_surcharge), 2) as congestion_revenue,
round(sum(airport_fee), 2) as airport_fee_revenue,
round(sum(cbd_congestion_fee), 2) as cbd_fee_revenue,
```

---

### ⚠️ خطأ 8: مشكلة Logic - ملف `dim_date.sql`

**الملف:** `nyc_taxi_dbt/models/marts/core/dim_date.sql`

**المشكلة:** استخدام دالة `dayofweek()` مع قيم غير صحيحة

```sql
-- ❌ الكود الخاطئ:
case when dayofweek(date_id) in (0, 6) then false else true end as is_weekday,
case when dayofweek(date_id) in (0, 6) then true else false end as is_weekend,
```

**ملاحظة:** في Snowflake، `dayofweek()` ترجع:
- 0 = الأحد (Sunday)
- 1 = الاثنين (Monday)
- ...
- 6 = السبت (Saturday)

لكن في بعض أنظمة SQL الأخرى، القيم مختلفة. تأكد من توافق القيم مع Snowflake.

---

### ⚠️ خطأ 9: مشكلة Logic - ملف `assert_positive_fares.sql`

**الملف:** `nyc_taxi_dbt/tests/assert_positive_fares.sql`

**المشكلة:** اسم الـ test مضلل - يقول "positive fares" لكن يسمح بقيم حتى -100

```sql
-- ❌ الكود الحالي:
where fare_amount < -100  -- ← يسمح بقيم سالبة حتى -100!
```

**التوصية:** إما تغيير اسم الملف أو تغيير الـ logic:

```sql
-- ✅ الخيار 1: للتحقق من القيم الموجبة فقط:
where fare_amount < 0

-- ✅ الخيار 2: لاستثناء refunds المعقولة:
where fare_amount < -50  -- مع تغيير اسم الملف إلى assert_reasonable_fares.sql
```

---

## 🐳 مشاكل Docker والتشغيل

### ❌ مشكلة 1: ملف `taxi_zone_lookup.csv` مفقود للمستخدمين الجدد

**المشكلة:** الـ dashboard يحتاج ملف `streaming/dashboard/data/taxi_zone_lookup.csv` لكن قد لا يكون موجوداً عند clone

**الإصلاح:** التأكد من أن الملف موجود في الـ repository، أو إضافة fallback:

```python
# في zone_lookup.py - الكود الحالي جيد لكن يمكن تحسينه:
try:
    self.df = pd.read_csv(data_path)
    self.zones = dict(zip(self.df['LocationID'], self.df['Zone']))
except FileNotFoundError:
    logger.warning("taxi_zone_lookup.csv not found, using empty zone lookup")
    self.zones = {}
```

---

### ❌ مشكلة 2: Spark image build قد يفشل

**الملف:** `streaming/spark/Dockerfile`

**المشكلة:** استخدام pip3 install مباشرة قد يفشل بسبب إصدارات الـ packages

```dockerfile
# ❌ الكود الحالي:
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
    redis==7.1.0 \
    pandas==2.3.3 \
    pyarrow==22.0.0 \  # ← هذا الإصدار قد لا يكون متوفراً!
    kafka-python-ng==2.2.3
```

**الإصلاح:** استخدام إصدارات مرنة:

```dockerfile
# ✅ الكود المحسن:
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install --no-cache-dir \
    redis>=5.0.0 \
    pandas>=2.0.0 \
    pyarrow>=14.0.0 \
    kafka-python-ng>=2.2.0
```

---

### ❌ مشكلة 3: Docker Compose قد لا يعمل بدون بناء الـ images أولاً

**المشكلة:** الـ services التي تستخدم `build:` تحتاج build قبل التشغيل

**الخطوات الصحيحة:**
```bash
cd streaming/docker
docker compose build    # ← هذه الخطوة مهمة!
docker compose up -d
```

---

### ❌ مشكلة 4: Spark job قد يفشل بسبب مشكلة في الـ packages

**المشكلة:** الـ spark-submit يحتاج تنزيل packages من Maven وقد يفشل

```yaml
# في docker-compose.yml:
command: >
  /opt/spark/bin/spark-submit
  --master spark://spark-master:7077
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1  # ← قد يفشل التنزيل
```

**الإصلاح:** إضافة ivy cache مشتركة أو تنزيل الـ packages مسبقاً في الـ Dockerfile

---

### ❌ مشكلة 5: Port conflicts

**المشكلة:** المنافذ التالية قد تكون مستخدمة:
- 9092 (Kafka)
- 8000 (FastAPI) 
- 8501 (Streamlit)
- 6379 (Redis)
- 8085 (Kafka UI)

**الإصلاح:** تحقق من المنافذ المستخدمة قبل التشغيل:
```bash
# للتحقق من المنافذ المستخدمة:
sudo lsof -i -P -n | grep LISTEN | grep -E '(9092|8000|8501|6379|8085)'
```

---

### ❌ مشكلة 6: Redis data persistence

**المشكلة:** عند إعادة تشغيل الـ containers، البيانات تُحفظ في volumes لكن قد تحتاج إلى مسحها للاختبار

**الإصلاح:** لمسح البيانات:
```bash
# الطريقة 1: من Dashboard
# استخدم زر "Clear Redis Data (FLUSH)" في الصفحة الرئيسية

# الطريقة 2: من Terminal
docker exec redis redis-cli FLUSHALL

# الطريقة 3: حذف volumes كاملة
docker compose down -v
docker compose up -d
```

---

## 🚀 دليل التشغيل الكامل

### للمستخدمين الجدد (زميلتك)

#### الخطوة 1: Clone المشروع
```bash
git clone https://github.com/abdulrahman532/nyc-taxi-data-pipeline.git
cd nyc-taxi-data-pipeline
```

#### الخطوة 2: التأكد من المتطلبات
```bash
# التأكد من وجود Docker
docker --version
docker compose version

# التأكد من توفر الذاكرة (يحتاج 8GB+)
free -h
```

#### الخطوة 3: التحقق من المنافذ
```bash
# تأكد أن المنافذ التالية غير مستخدمة:
# 6379, 7077, 8000, 8080, 8081, 8082, 8085, 8501, 9092

# للتحقق:
sudo lsof -i -P -n | grep LISTEN | grep -E '(9092|8000|8501|6379|8085|8080|8081|8082|7077)'
```

#### الخطوة 4: بناء وتشغيل الخدمات
```bash
cd streaming/docker

# بناء الـ images (مهم جداً!)
docker compose build

# تشغيل جميع الخدمات
docker compose up -d

# التحقق من حالة الخدمات
docker compose ps
```

#### الخطوة 5: انتظار بدء الخدمات
```bash
# انتظر حوالي 60-90 ثانية حتى تبدأ جميع الخدمات
# يمكنك مراقبة الـ logs:
docker compose logs -f

# أو مراقبة خدمة معينة:
docker compose logs -f spark-job
```

#### الخطوة 6: التحقق من عمل الخدمات
```bash
# 1. تحقق من FastAPI
curl http://localhost:8000/health

# 2. تحقق من Redis
docker exec redis redis-cli ping

# 3. تحقق من Kafka
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

#### الخطوة 7: فتح Dashboard
```bash
# افتح المتصفح على:
# http://localhost:8501
```

#### الخطوة 8: إرسال بيانات تجريبية
```bash
# إرسال رحلة واحدة للاختبار:
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

### حل المشاكل الشائعة

#### المشكلة: "Cannot connect to Docker daemon"
```bash
# تأكد من أن Docker يعمل:
sudo systemctl start docker
sudo systemctl enable docker

# أضف المستخدم لمجموعة docker:
sudo usermod -aG docker $USER
# ثم أعد تسجيل الدخول
```

#### المشكلة: "Port already in use"
```bash
# اعثر على العملية التي تستخدم المنفذ:
sudo lsof -i :8000  # مثال للمنفذ 8000

# أوقف العملية:
sudo kill -9 <PID>
```

#### المشكلة: "Out of memory"
```bash
# قلل استخدام الذاكرة في docker-compose.yml
# أو أوقف بعض الخدمات غير الضرورية:
docker compose stop kafka-ui  # مثلاً
```

#### المشكلة: "Spark job keeps restarting"
```bash
# تحقق من logs:
docker compose logs spark-job

# المشكلة الشائعة: Kafka topic غير موجود
# الحل: انتظر حتى يبدأ Kafka أولاً
# أو أنشئ الـ topic يدوياً:
docker exec kafka /opt/kafka/bin/kafka-topics.sh \
  --create --topic nyc.taxi.trips.raw \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1
```

#### المشكلة: "Dashboard shows no data"
```bash
# 1. تأكد من إرسال بيانات:
curl -X POST http://localhost:8000/api/v1/trips ...

# 2. تحقق من Redis:
docker exec redis redis-cli keys "*"

# 3. امسح البيانات القديمة وأعد المحاولة:
docker exec redis redis-cli FLUSHALL
```

#### المشكلة: "Build failed"
```bash
# أعد بناء بدون cache:
docker compose build --no-cache

# أو ابني صورة معينة:
docker compose build --no-cache spark-job
```

---

### إيقاف المشروع

```bash
# إيقاف جميع الخدمات:
docker compose down

# إيقاف مع حذف البيانات:
docker compose down -v

# إيقاف مع حذف كل شيء (images أيضاً):
docker compose down -v --rmi all
```

---

### روابط مفيدة

| الخدمة | الرابط | الوصف |
|--------|--------|-------|
| Dashboard | http://localhost:8501 | واجهة التحليلات الرئيسية |
| API Docs | http://localhost:8000/docs | توثيق الـ API |
| API Health | http://localhost:8000/health | فحص صحة الـ API |
| Kafka UI | http://localhost:8085 | واجهة إدارة Kafka |
| Spark Master | http://localhost:8081 | واجهة Spark |

---

## ✅ ملخص الإصلاحات

### ملفات SQL تم إصلاحها: ✅

| الملف | نوع الخطأ | الحالة |
|-------|----------|--------|
| `insight_zone_heatmap.sql` | Syntax Error (قوس مفقود) | ✅ تم الإصلاح |
| `stg_trips.sql` | Logic Error (نوع البيانات) | ✅ تم الإصلاح |
| `int_trips_validated.sql` | Logic Error (WHERE clause + speed_mph) | ✅ تم الإصلاح |
| `fct_trips.sql` | Missing Columns | ✅ تم إضافة الأعمدة المفقودة |
| `agg_yearly.sql` | Missing Columns (airport_trips, trips_yoy_pct) | ✅ تم الإصلاح |
| `agg_monthly.sql` | Missing Columns (fee revenues) | ✅ تم الإصلاح |

### ملفات Docker - ملاحظات للمستخدمين الجدد:

| الملف | الملاحظة | الحل |
|-------|----------|------|
| `Dockerfile` (spark) | Package versions قد تتغير | تم التوثيق |
| `docker-compose.yml` | يحتاج build قبل up | `docker compose build` ثم `docker compose up -d` |

---

## 📝 التغييرات التي تمت

1. **إصلاح خطأ Syntax في `insight_zone_heatmap.sql`**
   - تم إضافة القوس المغلق والـ `desc` في الـ CASE statement

2. **إصلاح نوع البيانات في `stg_trips.sql`**
   - تم تحويل `dropoff_datetime_raw` إلى bigint مثل `pickup_datetime_raw`

3. **إصلاح WHERE clause في `int_trips_validated.sql`**
   - تم استخدام `pickup_datetime_raw` بدلاً من `pickup_datetime`
   - تم إصلاح حساب `speed_mph` ليستخدم الحساب المباشر

4. **إضافة أعمدة مفقودة في `fct_trips.sql`**
   - `pickup_month`, `pickup_year`, `speed_mph`, `fare_per_mile`
   - `tip_percentage`, `time_of_day`, `day_type`
   - جميع أعمدة الـ flags

5. **إصلاح `agg_yearly.sql`**
   - إضافة `airport_trips`
   - إضافة `trips_yoy_pct` (Year-over-Year)

6. **إصلاح `agg_monthly.sql`**
   - إضافة `congestion_revenue`, `airport_fee_revenue`, `cbd_fee_revenue`

---

*تم إنشاء هذا التقرير بواسطة GitHub Copilot - 1 ديسمبر 2025*
*آخر تحديث: بعد إصلاح جميع الأخطاء*
