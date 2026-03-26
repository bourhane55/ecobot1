from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib.pyplot as plt
import io
import json
import os
from datetime import datetime

# ========= الإعدادات =========
TOKEN = '8299170161:AAHCsVWMp4aiGGTj_R9O2iaL7NmYPWWoT_s'
DATA_FILE = 'user_data.json'

# ========= إدارة البيانات =========
def load_data():
    """تحميل البيانات من الملف"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """حفظ البيانات في الملف"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# تحميل البيانات عند بدء التشغيل
users = load_data()

# ========= قوائم ثابتة =========
main_causes = ["Method", "Materials", "Measurement", "Human", "Machine", "Environment"]
main_causes_ar = ["الطريقة", "المواد", "القياس", "العامل", "الآلة", "البيئة"]
cause_map = dict(zip(main_causes_ar, main_causes))

# ========= دوال المساعدة =========
def get_user(uid):
    """الحصول على بيانات المستخدم أو إنشاء جديدة"""
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "step": 1,
            "causes_dict": {},
            "counter": 1,
            "why5_list": [],
            "language": "ar",
            "created_at": datetime.now().isoformat()
        }
        save_data(users)
    return users[uid]

def save_user(uid, data):
    """حفظ بيانات مستخدم معين"""
    users[str(uid)] = data
    save_data(users)

def delete_user(uid):
    """حذف بيانات مستخدم"""
    uid = str(uid)
    if uid in users:
        del users[uid]
        save_data(users)

# ========= دوال الرسوم البيانية =========
def metrics_table(aot, mttr, mtbf, av):
    """جدول المعايير"""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')
    
    mtbf_note = "✅ جيد" if mtbf >= 100 else "⚠️ منخفض"
    mttr_note = "✅ جيد" if mttr <= 2 else "⚠️ مرتفع"
    av_note = "✅ ممتاز" if av >= 95 else "⚠️ متوسط" if av >= 85 else "❌ منخفض"
    
    data = [
        ["وقت التشغيل الفعلي", f"{aot:.2f} ساعة", ""],
        ["MTTR (متوسط وقت الإصلاح)", f"{mttr:.2f} ساعة", mttr_note],
        ["MTBF (متوسط الوقت بين الأعطال)", f"{mtbf:.2f} ساعة", mtbf_note],
        ["التوفر", f"{av:.2f} %", av_note]
    ]
    
    table = ax.table(cellText=data, colLabels=["المقياس", "القيمة", "الملاحظة"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def pareto_table(causes_dict):
    """جدول باريتو"""
    counts = {k: sum(v) for k, v in causes_dict.items()}
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    total = sum(counts.values())
    rows = []
    cumulative = 0
    
    for cause, num in sorted_items:
        percent = (num / total) * 100 if total != 0 else 0
        cumulative += percent
        rows.append([cause, num, f"{percent:.1f}%", f"{cumulative:.1f}%"])
    
    fig, ax = plt.subplots(figsize=(10, len(rows)*0.5+2))
    ax.axis('off')
    
    table = ax.table(cellText=rows, colLabels=["السبب الرئيسي", "العدد", "النسبة", "النسبة التراكمية"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def pareto_chart(causes_dict):
    """مخطط باريتو"""
    counts = {k: sum(v) for k, v in causes_dict.items()}
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    labels = [x[0] for x in sorted_items]
    values = [x[1] for x in sorted_items]
    total = sum(values)
    
    cumulative = []
    cumsum = 0
    for v in values:
        cumsum += v
        cumulative.append((cumsum / total) * 100 if total != 0 else 0)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    percent_values = [(v / total) * 100 if total != 0 else 0 for v in values]
    bars = ax1.bar(labels, percent_values, color='steelblue', alpha=0.7)
    ax1.set_ylabel("النسبة المئوية (%)", fontsize=12)
    ax1.tick_params(axis='x', rotation=45)
    
    ax2 = ax1.twinx()
    ax2.plot(labels, cumulative, marker='o', color='red', linewidth=2, markersize=8)
    ax2.set_ylabel("النسبة التراكمية (%)", fontsize=12)
    ax2.set_ylim(0, 105)
    ax2.axhline(80, linestyle='--', color='gray', alpha=0.7, label='خط 80%')
    
    plt.title("مخطط باريتو - تحليل الأسباب", fontsize=14, pad=20)
    plt.tight_layout()
    
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def why5_table(problem, why_list):
    """جدول تحليل 5 لماذا"""
    fig, ax = plt.subplots(figsize=(10, len(why_list)*0.8+2))
    ax.axis('off')
    
    rows = [[f"لماذا {i+1}", why] for i, why in enumerate(why_list)]
    table = ax.table(cellText=rows, colLabels=["المستوى", f"تحليل المشكلة: {problem}"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

# ========= دوال التحليل الذكي =========
def analyze_root_cause(why_list, top_causes, metrics):
    """تحليل ذكي للسبب الجذري"""
    last_why = why_list[-1].lower() if why_list else ""
    
    # كلمات مفتاحية للتحليل
    keywords = {
        "maintenance": ["maintenance", "صيانة", "réparation", "صيانة"],
        "human": ["operator", "human", "worker", "عامل", "مستخدم", "تدريب"],
        "material": ["material", "materials", "مواد", "matière", "جودة"],
        "machine": ["machine", "equipment", "آلة", "معدات", "جهاز"],
        "management": ["management", "إدارة", "supervision", "إشراف"]
    }
    
    # تحليل النص
    for category, words in keywords.items():
        if any(word in last_why for word in words):
            return category, last_why
    
    return "other", last_why

def generate_recommendation(root_cause, top_causes, metrics):
    """توليد توصيات ذكية"""
    recommendations = {
        "maintenance": {
            "root": "ضعف برنامج الصيانة الوقائية",
            "recommendation": "تطبيق نظام صيانة وقائية، جدولة الأعمال الدورية، تدريب فريق الصيانة"
        },
        "human": {
            "root": "ضعف المهارات أو الأخطاء البشرية",
            "recommendation": "برامج تدريب مكثفة، توثيق الإجراءات، تحسين بيئة العمل"
        },
        "material": {
            "root": "جودة المواد غير مطابقة",
            "recommendation": "تقييم الموردين، فحص المواد الواردة، توحيد المواصفات"
        },
        "machine": {
            "root": "أعطال متكررة في المعدات",
            "recommendation": "تطبيق الصيانة التنبؤية، مراقبة الحالة، تحديث المعدات القديمة"
        },
        "management": {
            "root": "ضعف الإدارة والإشراف",
            "recommendation": "تحسين نظام المتابعة، تحديد مؤشرات الأداء، تعزيز ثقافة الجودة"
        },
        "other": {
            "root": f"عوامل متعددة: {top_causes[0] if top_causes else 'غير محدد'}",
            "recommendation": "تحليل مفصل للأسباب المحددة، تطبيق إجراءات تصحيحية فورية"
        }
    }
    
    return recommendations.get(root_cause, recommendations["other"])

# ========= أوامر البوت =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة"""
    uid = update.effective_user.id
    user_data = get_user(uid)
    user_data["step"] = 1
    user_data["causes_dict"] = {}
    user_data["counter"] = 1
    user_data["why5_list"] = []
    save_user(uid, user_data)
    
    await update.message.reply_text(
        "مرحباً بك في بوت تحليل الجودة المتطور! 🤖\n\n"
        "سأساعدك في تحليل مشكلات الجودة باستخدام:\n"
        "📊 تحليل باريتو\n"
        "🔍 تحليل 5 لماذا\n"
        "📈 مقاييس MTBF و MTTR\n\n"
        "📝 ما هي المشكلة التي تواجهها؟"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تعيين الجلسة"""
    uid = update.effective_user.id
    delete_user(uid)
    await update.message.reply_text(
        "✅ تم إعادة التعيين بنجاح!\n"
        "أرسل /start لبدء تحليل جديد"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة المستخدم"""
    uid = update.effective_user.id
    user_data = get_user(uid)
    
    step = user_data.get("step", 1)
    problem = user_data.get("problem", "غير محدد")
    
    status_text = f"📊 **حالة التحليل**\n\n"
    status_text += f"📝 المشكلة: {problem}\n"
    status_text += f"🔢 المرحلة: {step}/7\n"
    
    if user_data.get("causes_dict"):
        total_causes = sum(len(v) for v in user_data["causes_dict"].values())
        status_text += f"📋 عدد الأسباب المدخلة: {total_causes}\n"
    
    if user_data.get("why5_list"):
        status_text += f"❓ تحليل 5 لماذا: {len(user_data['why5_list'])}/5\n"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المساعدة"""
    help_text = """
🤖 **مساعدة بوت تحليل الجودة**

**الأوامر المتاحة:**
/start - بدء تحليل جديد
/reset - إعادة تعيين الجلسة
/status - عرض حالة التحليل الحالي
/help - عرض هذه المساعدة

**كيفية الاستخدام:**
1️⃣ اكتب المشكلة
2️⃣ اختر القسم
3️⃣ اختر السبب الرئيسي
4️⃣ أدخل الأسباب الفرعية مع أرقام (مثال: 'فساد 1')
5️⃣ استخدم 'NEXT' لتغيير السبب الرئيسي
6️⃣ استخدم 'FINISH' لإنهاء إدخال الأسباب
7️⃣ أدخل معطيات التشغيل

**نصائح:**
• أدخل الأسباب بالصيغة: 'السبب الرقم'
• يمكنك إدخال عدة أسباب لكل فئة
• التحليل يعتمد على MTBF و MTTR
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ========= معالجة الرسائل =========
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل"""
    uid = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        user_data = get_user(uid)
        step = user_data.get("step", 1)
        
        # ===== المرحلة 1: المشكلة =====
        if step == 1:
            user_data["problem"] = text
            user_data["step"] = 2
            save_user(uid, user_data)
            await update.message.reply_text("🏭 ما هو القسم؟ (مثال: إنتاج، صيانة، جودة)")
            return
        
        # ===== المرحلة 2: القسم =====
        if step == 2:
            user_data["department"] = text
            user_data["step"] = 3
            save_user(uid, user_data)
            
            keyboard = [[ar] for ar in main_causes_ar]
            await update.message.reply_text(
                "🔍 اختر السبب الرئيسي:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return
        
        # ===== المرحلة 3: السبب الرئيسي =====
        if step == 3:
            if text not in main_causes_ar:
                await update.message.reply_text("❌ الرجاء اختيار سبب من الأزرار")
                return
            
            main_en = cause_map[text]
            user_data["current_main"] = main_en
            if main_en not in user_data["causes_dict"]:
                user_data["causes_dict"][main_en] = []
            user_data["counter"] = 1
            user_data["step"] = 4
            save_user(uid, user_data)
            
            await update.message.reply_text(
                f"📝 أدخل الأسباب الفرعية لـ {text}\n"
                f"الصيغة: 'السبب الرقم' (مثال: فساد 1)\n\n"
                f"🔁 اكتب 'NEXT' لتغيير السبب الرئيسي\n"
                f"✅ اكتب 'FINISH' لإنهاء الإدخال",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # ===== المرحلة 4: إدخال الأسباب =====
        if step == 4:
            if text.upper() == "NEXT":
                user_data["step"] = 3
                save_user(uid, user_data)
                keyboard = [[ar] for ar in main_causes_ar]
                await update.message.reply_text(
                    "🔄 اختر سبباً رئيسياً آخر:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return
            
            if text.upper() == "FINISH":
                total_causes = sum(len(v) for v in user_data["causes_dict"].values())
                if total_causes == 0:
                    await update.message.reply_text("❌ الرجاء إدخال سبب واحد على الأقل")
                    return
                user_data["step"] = 5
                save_user(uid, user_data)
                await update.message.reply_text("⏱️ ما هو وقت التشغيل الكلي (بالساعات)؟")
                return
            
            # إضافة سبب جديد
            parts = text.strip().split()
            if len(parts) < 2:
                await update.message.reply_text("❌ الصيغة خاطئة!\nمثال صحيح: 'فساد 1'")
                return
            
            cause_name = " ".join(parts[:-1])
            try:
                cause_value = int(parts[-1])
            except ValueError:
                await update.message.reply_text("❌ الرقم يجب أن يكون صحيحاً")
                return
            
            main = user_data["current_main"]
            user_data["causes_dict"][main].append(cause_value)
            user_data["counter"] += 1
            save_user(uid, user_data)
            
            await update.message.reply_text(
                f"✅ تم الإضافة! ({user_data['counter']-1} سبب)\n"
                f"أدخل السبب التالي، أو 'FINISH' لإنهاء"
            )
            return
        
        # ===== المرحلة 5: إدخال المعطيات =====
        if step == 5:
            if "total" not in user_data:
                try:
                    user_data["total"] = float(text)
                    user_data["step"] = 5.1
                    save_user(uid, user_data)
                    await update.message.reply_text("⏸️ ما هو وقت التوقف المخطط (بالساعات)؟")
                except ValueError:
                    await update.message.reply_text("❌ الرجاء إدخال رقم صحيح")
                return
            
            if user_data.get("step") == 5.1:
                try:
                    user_data["stops"] = float(text)
                    user_data["step"] = 5.2
                    save_user(uid, user_data)
                    await update.message.reply_text("🔧 كم عدد الأعطال؟")
                except ValueError:
                    await update.message.reply_text("❌ الرجاء إدخال رقم صحيح")
                return
            
            if user_data.get("step") == 5.2:
                try:
                    user_data["fail"] = float(text)
                    user_data["step"] = 5.3
                    save_user(uid, user_data)
                    await update.message.reply_text("🛠️ ما هو وقت الإصلاح الكلي (بالساعات)؟")
                except ValueError:
                    await update.message.reply_text("❌ الرجاء إدخال رقم صحيح")
                return
            
            if user_data.get("step") == 5.3:
                try:
                    user_data["repair"] = float(text)
                    
                    # حساب المعايير
                    total = user_data["total"]
                    stops = user_data["stops"]
                    fail = user_data["fail"]
                    repair = user_data["repair"]
                    
                    aot = total - stops
                    mttr = repair / fail if fail > 0 else 0
                    mtbf = aot / fail if fail > 0 else aot
                    av = mtbf / (mtbf + mttr) * 100 if (mtbf + mttr) > 0 else 0
                    
                    # حفظ المعايير
                    user_data["metrics"] = {"aot": aot, "mttr": mttr, "mtbf": mtbf, "av": av}
                    
                    # إرسال الرسوم البيانية
                    await update.message.reply_text("📊 جاري إنشاء التقارير...")
                    
                    img1 = metrics_table(aot, mttr, mtbf, av)
                    await update.message.reply_photo(img1, caption="📈 **مقاييس الأداء**", parse_mode='Markdown')
                    
                    img2 = pareto_table(user_data["causes_dict"])
                    await update.message.reply_photo(img2, caption="📊 **جدول تحليل باريتو**", parse_mode='Markdown')
                    
                    img3 = pareto_chart(user_data["causes_dict"])
                    await update.message.reply_photo(img3, caption="📉 **مخطط باريتو**", parse_mode='Markdown')
                    
                    user_data["step"] = 6
                    user_data["why5_list"] = []
                    save_user(uid, user_data)
                    
                    await update.message.reply_text(f"🔍 **تحليل 5 لماذا**\n\nلماذا ({user_data['problem']})؟")
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ خطأ: {e}")
                    user_data["step"] = 5
                    save_user(uid, user_data)
                return
        
        # ===== المرحلة 6: تحليل 5 لماذا =====
        if step == 6:
            user_data["why5_list"].append(text)
            
            if len(user_data["why5_list"]) < 5:
                save_user(uid, user_data)
                prev_why = user_data["why5_list"][-1]
                await update.message.reply_text(f"❓ لماذا ({prev_why})؟")
            else:
                # تحليل نهائي
                causes_dict = user_data["causes_dict"]
                counts = {k: sum(v) for k, v in causes_dict.items()}
                sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_causes = [x[0] for x in sorted_items[:2]]
                
                metrics = user_data.get("metrics", {})
                mtbf = metrics.get("mtbf", 0)
                mttr = metrics.get("mttr", 0)
                
                # تحليل ذكي
                root_type, root_text = analyze_root_cause(
                    user_data["why5_list"],
                    top_causes,
                    metrics
                )
                
                recommendation = generate_recommendation(root_type, top_causes, metrics)
                
                # إرسال جدول 5 لماذا
                img4 = why5_table(user_data["problem"], user_data["why5_list"])
                await update.message.reply_photo(img4, caption="🔍 **تحليل 5 لماذا**", parse_mode='Markdown')
                
                # تقرير نهائي
                final_report = f"""
🎯 **التقرير النهائي لتحليل الجودة**

📝 **المشكلة:** {user_data['problem']}
🏭 **القسم:** {user_data.get('department', 'غير محدد')}

📊 **أهم الأسباب (باريتو):**
{', '.join(top_causes)}

📈 **المقاييس:**
• MTBF: {mtbf:.2f} ساعة
• MTTR: {mttr:.2f} ساعة
• التوفر: {metrics.get('av', 0):.2f}%

🔍 **السبب الجذري:**
{recommendation['root']}

💡 **التوصيات:**
{recommendation['recommendation']}

📌 **الإجراءات المقترحة:**
1. تطبيق التوصيات المذكورة أعلاه
2. متابعة المؤشرات أسبوعياً
3. إعادة التقييم بعد 30 يوماً

✅ تم التحليل بواسطة بوت تحليل الجودة الذكي
"""
                
                await update.message.reply_text(final_report, parse_mode='Markdown')
                
                # جدول ملخص الأسباب
                summary = "📋 **ملخص الأسباب المدخلة:**\n\n"
                for cause, values in causes_dict.items():
                    summary += f"• **{cause}**: {len(values)} سبب (القيم: {values})\n"
                await update.message.reply_text(summary, parse_mode='Markdown')
                
                user_data["step"] = 7
                save_user(uid, user_data)
                
                await update.message.reply_text(
                    "🎉 **اكتمل التحليل!**\n\n"
                    "لتحليل جديد، أرسل /reset ثم /start"
                )
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}\nالرجاء المحاولة مرة أخرى أو استخدام /reset")
        pri

                     
