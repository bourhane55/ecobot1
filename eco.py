import json
import os
import io
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
from flask import Flask, request

app = Flask(__name__)
TOKEN = '7597693041:AAHvei9uLwhiGcQ_BeJgIrvaQZqGkn5WQ2w'
DATA_FILE = 'user_data.json'

# ========= DATA MANAGEMENT =========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_data()

# ========= CONSTANTS =========
main_causes = ["Method", "Materials", "Measurement", "Human", "Machine", "Environment"]
main_causes_ar = ["الطريقة", "المواد", "القياس", "العامل", "الآلة", "البيئة"]

# ========= HELPER FUNCTIONS =========
def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "step": 1,
            "causes_dict": {},
            "counter": 1,
            "why5_list": [],
            "created_at": datetime.now().isoformat(),
            "language": "en"
        }
        save_data(users)
    return users[uid]

def save_user(uid, data):
    users[str(uid)] = data
    save_data(users)

def delete_user(uid):
    uid = str(uid)
    if uid in users:
        del users[uid]
        save_data(users)

# ========= SEND FUNCTIONS =========
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def send_photo(chat_id, photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', photo_bytes, 'image/png')}
    data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=data, files=files, timeout=15)
    except Exception as e:
        print(f"Error sending photo: {e}")

def send_keyboard(chat_id, text, buttons):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    reply_markup = {
        "keyboard": [[b] for b in buttons],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    payload = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(reply_markup)}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending keyboard: {e}")

def remove_keyboard(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    reply_markup = {"remove_keyboard": True}
    payload = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(reply_markup)}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error removing keyboard: {e}")

# ========= CHART FUNCTIONS =========
def metrics_table(aot, mttr, mtbf, av, lang="en"):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')

    if lang == "ar":
        mtbf_note = "✅ جيد" if mtbf >= 100 else "⚠️ منخفض"
        mttr_note = "✅ جيد" if mttr <= 2 else "⚠️ مرتفع"
        av_note = "✅ ممتاز" if av >= 95 else "⚠️ متوسط" if av >= 85 else "❌ منخفض"
        data = [
            ["وقت التشغيل الفعلي", f"{aot:.2f} س", ""],
            ["MTTR (متوسط وقت الإصلاح)", f"{mttr:.2f} س", mttr_note],
            ["MTBF (متوسط الوقت بين الأعطال)", f"{mtbf:.2f} س", mtbf_note],
            ["التوفر", f"{av:.2f} %", av_note]
        ]
        colLabels = ["المقياس", "القيمة", "الملاحظة"]
    else:
        mtbf_note = "✅ Good" if mtbf >= 100 else "⚠️ Low"
        mttr_note = "✅ Good" if mttr <= 2 else "⚠️ High"
        av_note = "✅ Excellent" if av >= 95 else "⚠️ Average" if av >= 85 else "❌ Low"
        data = [
            ["Actual Operating Time", f"{aot:.2f} h", ""],
            ["MTTR (Mean Time To Repair)", f"{mttr:.2f} h", mttr_note],
            ["MTBF (Mean Time Between Failures)", f"{mtbf:.2f} h", mtbf_note],
            ["Availability", f"{av:.2f} %", av_note]
        ]
        colLabels = ["Metric", "Value", "Observation"]

    table = ax.table(cellText=data, colLabels=colLabels, loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=100)
    bio.seek(0)
    plt.close()
    return bio

def pareto_table(causes_dict, lang="en"):
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

    if lang == "ar":
        colLabels = ["السبب الرئيسي", "العدد", "%", "% التراكمي"]
    else:
        colLabels = ["Main Cause", "Count", "%", "Cumulative %"]

    table = ax.table(cellText=rows, colLabels=colLabels, loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=100)
    bio.seek(0)
    plt.close()
    return bio

def pareto_chart(causes_dict, lang="en"):
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
    ax1.bar(labels, percent_values, color='steelblue', alpha=0.7)
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(labels, cumulative, marker='o', color='red', linewidth=2, markersize=8)
    ax2.set_ylim(0, 105)
    ax2.axhline(80, linestyle='--', color='gray', alpha=0.7)

    if lang == "ar":
        ax1.set_ylabel("النسبة المئوية (%)", fontsize=12)
        ax2.set_ylabel("النسبة التراكمية (%)", fontsize=12)
        ax2.axhline(80, linestyle='--', color='gray', alpha=0.7, label='خط 80%')
        plt.title("مخطط باريتو - تحليل الأسباب", fontsize=14, pad=20)
    else:
        ax1.set_ylabel("Percentage (%)", fontsize=12)
        ax2.set_ylabel("Cumulative %", fontsize=12)
        ax2.axhline(80, linestyle='--', color='gray', alpha=0.7, label='80% Line')
        plt.title("Pareto Chart - Cause Analysis", fontsize=14, pad=20)

    plt.tight_layout()

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=100)
    bio.seek(0)
    plt.close()
    return bio

def why5_table(problem, why_list, lang="en"):
    fig, ax = plt.subplots(figsize=(10, len(why_list)*0.8+2))
    ax.axis('off')

    if lang == "ar":
        col_label = "المستوى"
        title = f"تحليل 5 لماذا: {problem}"
        rows = [[f"لماذا {i+1}", why] for i, why in enumerate(why_list)]
    else:
        col_label = "Level"
        title = f"5 Why Analysis: {problem}"
        rows = [[f"Why {i+1}", why] for i, why in enumerate(why_list)]

    table = ax.table(cellText=rows, colLabels=[col_label, title], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=100)
    bio.seek(0)
    plt.close()
    return bio

# ========= SMART ROOT CAUSE ANALYSIS =========
def smart_analysis(causes_dict, metrics, why5_list, problem):
    counts = {k: sum(v) for k, v in causes_dict.items()}
    sorted_causes = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_causes = [x[0] for x in sorted_causes[:2]] if sorted_causes else ["Unknown"]
    top_cause = top_causes[0]

    mtbf = metrics.get('mtbf', 0)
    mttr = metrics.get('mttr', 0)
    availability = metrics.get('av', 0)

    if mtbf < 50:
        metrics_issue = "reliability"
        metrics_root = f"Low MTBF ({mtbf:.1f}h) indicates frequent failures"
    elif mttr > 3:
        metrics_issue = "maintainability"
        metrics_root = f"High MTTR ({mttr:.1f}h) indicates slow repair process"
    elif availability < 85:
        metrics_issue = "overall performance"
        metrics_root = f"Low availability ({availability:.1f}%) indicates combined issues"
    else:
        metrics_issue = "process"
        metrics_root = "Metrics within acceptable range"

    last_why = why5_list[-1].lower() if why5_list else ""

    keywords = {
        'maintenance': ['maintenance', 'صيانة', 'repair', 'fix', 'breakdown', 'preventive'],
        'training': ['training', 'skill', 'operator', 'worker', 'عامل', 'تدريب'],
        'material': ['material', 'supplier', 'quality', 'مواد', 'جودة'],
        'machine': ['machine', 'equipment', 'آلة', 'معدة', 'device'],
        'process': ['process', 'procedure', 'method', 'طريقة', 'إجراء'],
        'management': ['management', 'supervision', 'إدارة', 'إشراف', 'planning']
    }

    detected_categories = []
    for category, words in keywords.items():
        if any(word in last_why for word in words):
            detected_categories.append(category)

    if 'maintenance' in detected_categories or metrics_issue == 'reliability':
        root_cause = f"The root cause is inadequate maintenance strategy. {metrics_root}. The 5 Why analysis reveals maintenance-related issues: '{last_why[:100]}'"
        recommendation = """• Implement a preventive maintenance program
• Schedule regular equipment inspections
• Develop maintenance checklists and procedures
• Train maintenance staff on predictive techniques
• Monitor MTBF trends weekly"""
    elif 'training' in detected_categories or 'human' in top_cause.lower() or metrics_issue == 'maintainability':
        root_cause = f"The root cause is insufficient operator skills and training. {metrics_root}. The analysis indicates: '{last_why[:100]}'"
        recommendation = """• Develop comprehensive training programs
• Create and document standard operating procedures
• Implement a mentoring system
• Conduct regular competency assessments
• Monitor MTTR trends and training effectiveness"""
    elif 'material' in detected_categories or 'Materials' in top_cause:
        root_cause = f"The root cause is material quality issues. {metrics_root}. The 5 Why analysis reveals: '{last_why[:100]}'"
        recommendation = """• Evaluate and audit suppliers
• Implement incoming material inspection
• Establish material specifications
• Work with suppliers on quality improvement
• Monitor defect rates by supplier"""
    elif 'machine' in detected_categories or 'Machine' in top_cause:
        root_cause = f"The root cause is equipment degradation. {metrics_root}. The analysis shows: '{last_why[:100]}'"
        recommendation = """• Implement predictive maintenance
• Upgrade critical equipment
• Monitor equipment condition in real-time
• Establish equipment replacement strategy
• Track MTBF by equipment type"""
    elif 'process' in detected_categories or 'Method' in top_cause:
        root_cause = f"The root cause is process inefficiency. {metrics_root}. The analysis indicates: '{last_why[:100]}'"
        recommendation = """• Map and analyze current process
• Identify bottlenecks and waste
• Implement process improvements
• Standardize work methods
• Monitor process KPIs"""
    elif 'management' in detected_categories:
        root_cause = f"The root cause is management system gaps. {metrics_root}. The analysis reveals: '{last_why[:100]}'"
        recommendation = """• Implement performance management system
• Establish clear roles and responsibilities
• Conduct regular management reviews
• Define and track KPIs
• Implement continuous improvement culture"""
    else:
        root_cause = f"The root cause involves multiple factors. Primary factor: {top_cause}. {metrics_root}. Key insight: '{last_why[:100]}'"
        recommendation = f"""• Focus improvement on {top_cause} related processes
• Conduct detailed analysis of contributing factors
• Implement corrective actions based on findings
• Monitor all identified metrics
• Establish regular review meetings"""

    if mtbf < 50:
        root_cause += f" Critical reliability issue: MTBF is {mtbf:.1f}h (target >100h)."
    if mttr > 3:
        root_cause += f" Maintainability concern: MTTR is {mttr:.1f}h (target <2h)."
    if availability < 85:
        root_cause += f" Overall performance impacted: Availability at {availability:.1f}% (target >95%)."

    return root_cause, recommendation, top_causes

def professional_root_cause_with_recommendation(why5_list, top_causes, mtbf, mttr, availability, primary_cause, lang="en"):
    full_text = " ".join(why5_list).lower()

    if any(word in full_text for word in ["maintenance", "صيانة", "program", "schedule", "repair"]):
        category = "نظام الصيانة" if lang == "ar" else "Maintenance System"
        root = "تفتقر المؤسسة إلى نظام صيانة وقائية منظم." if lang == "ar" else "The organization lacks a structured preventive maintenance system."
        recommendation = f"""📋 **التوصية:**\n1. إنشاء برنامج صيانة وقائية\n2. تعيين مسؤول صيانة\n3. تدريب فريق الصيانة\n4. متابعة MTBF و MTTR أسبوعياً\n\n**الهدف:** رفع MTBF من {mtbf:.1f} س إلى أكثر من 100 س خلال 3 أشهر.""" if lang == "ar" else f"""📋 **RECOMMENDATION:**\n1. Establish Preventive Maintenance Program\n2. Assign Maintenance Responsibility\n3. Train Maintenance Team\n4. Monitor MTBF & MTTR weekly\n\n**Target:** Increase MTBF from {mtbf:.1f}h to >100h in 3 months."""
    elif any(word in full_text for word in ["training", "تدريب", "skill", "operator", "worker"]):
        category = "فجوة التدريب والمهارات" if lang == "ar" else "Training & Skills Gap"
        root = "عدم وجود برامج تدريب كافية للعاملين." if lang == "ar" else "Insufficient operator training and skill development."
        recommendation = f"""📋 **التوصية:**\n1. تطوير برنامج تدريبي\n2. توثيق الإجراءات\n3. نظام التوجيه\n4. تقييم المهارات\n\n**الهدف:** خفض MTTR من {mttr:.1f} س إلى أقل من ساعتين خلال شهرين.""" if lang == "ar" else f"""📋 **RECOMMENDATION:**\n1. Develop Training Program\n2. Document Procedures\n3. Mentorship System\n4. Regular Skill Assessment\n\n**Target:** Reduce MTTR from {mttr:.1f}h to <2h in 2 months."""
    elif any(word in full_text for word in ["material", "مادة", "quality", "supplier"]):
        category = "مراقبة جودة المواد" if lang == "ar" else "Material Quality Control"
        root = "ضعف فحص المواد الواردة وإدارة الموردين." if lang == "ar" else "Weak incoming material inspection and supplier management."
        recommendation = f"""📋 **التوصية:**\n1. تقييم الموردين\n2. فحص المواد الواردة\n3. تحديد المواصفات\n4. متابعة معدلات العيوب\n\n**الهدف:** تقليل العيوب بنسبة 50% خلال 3 أشهر.""" if lang == "ar" else f"""📋 **RECOMMENDATION:**\n1. Evaluate Suppliers\n2. Inspect Incoming Materials\n3. Define Specifications\n4. Monitor Defect Rates\n\n**Target:** Reduce material-related defects by 50% in 3 months."""
    else:
        category = primary_cause
        root = f"المشكلة الأساسية تتمحور حول {primary_cause}." if lang == "ar" else f"The primary issue centers on {primary_cause}."
        recommendation = f"""📋 **التوصية:**\n1. تحليل مفصل لـ {primary_cause}\n2. تنفيذ إجراءات تصحيحية\n3. متابعة المؤشرات أسبوعياً\n4. مراجعة النتائج\n\n**الهدف:** رفع التوفر إلى أكثر من 90% خلال 3 أشهر.""" if lang == "ar" else f"""📋 **RECOMMENDATION:**\n1. Detailed Analysis of {primary_cause}\n2. Implement Corrective Actions\n3. Monitor Indicators Weekly\n4. Review Results\n\n**Target:** Increase availability to >90% in 3 months."""

    if lang == "ar":
        result = f"""
🔍 **تحليل السبب الجذري**

**العامل الرئيسي:** {category}
**الاستنتاج:** {root}

**التأثير على المؤشرات:**
- MTBF: {mtbf:.1f} ساعة
- MTTR: {mttr:.1f} ساعة
- التوفر: {availability:.1f}%
- أهم سبب في باريتو: {primary_cause}

{recommendation}
"""
    else:
        result = f"""
🔍 **ROOT CAUSE ANALYSIS**

**Primary Factor:** {category}
**Conclusion:** {root}

**Impact on Metrics:**
- MTBF: {mtbf:.1f}h
- MTTR: {mttr:.1f}h
- Availability: {availability:.1f}%
- Top Pareto Cause: {primary_cause}

{recommendation}
"""
    return result

# ========= LANGUAGE HANDLER =========
def lang_handler(chat_id, text):
    user_data = get_user(chat_id)
    if text == '/lang':
        send_keyboard(chat_id, "🌐 **Select your language / اختر لغتك:**", ["English 🇬🇧", "العربية 🇸🇦"])
        return ""
    elif text == "English 🇬🇧":
        user_data["language"] = "en"
        save_user(chat_id, user_data)
        send_message(chat_id, "✅ Language set to English. Send /start to begin.")
        return ""
    elif text == "العربية 🇸🇦":
        user_data["language"] = "ar"
        save_user(chat_id, user_data)
        send_message(chat_id, "✅ تم تعيين اللغة العربية. أرسل /start للبدء.")
        return ""
    return None

# ========= MESSAGE HANDLER =========
def handle_message(chat_id, text):
    user_data = get_user(chat_id)
    step = user_data.get("step", 1)
    lang = user_data.get("language", "en")

    # Step 1: Problem
    if step == 1:
        user_data["problem"] = text
        user_data["step"] = 2
        save_user(chat_id, user_data)
        if lang == "ar":
            return "🏭 ما هو القسم؟ (مثال: إنتاج، صيانة، جودة)"
        return "🏭 What is the department? (e.g., Production, Maintenance, Quality)"

    # Step 2: Department
    if step == 2:
        user_data["department"] = text
        user_data["step"] = 3
        save_user(chat_id, user_data)
        if lang == "ar":
            send_keyboard(chat_id, "🔍 اختر السبب الرئيسي:", main_causes_ar)
        else:
            send_keyboard(chat_id, "🔍 Select the main cause:", main_causes)
        return ""

    # Step 3: Main cause selection
    if step == 3:
        if lang == "ar":
            if text in main_causes_ar:
                cause_en = main_causes[main_causes_ar.index(text)]
                user_data["current_main"] = cause_en
                if cause_en not in user_data["causes_dict"]:
                    user_data["causes_dict"][cause_en] = []
                user_data["counter"] = 1
                user_data["step"] = 4
                save_user(chat_id, user_data)
                remove_keyboard(chat_id, f"📝 أدخل الأسباب الفرعية لـ {text}\nالصيغة: 'السبب رقم' (مثال: فساد 1)\n\n🔁 اكتب 'NEXT' لتغيير السبب\n✅ اكتب 'FINISH' لإنهاء الإدخال")
                return ""
            else:
                send_keyboard(chat_id, "❌ الرجاء اختيار سبب من الأزرار:", main_causes_ar)
                return ""
        else:
            if text in main_causes:
                user_data["current_main"] = text
                if text not in user_data["causes_dict"]:
                    user_data["causes_dict"][text] = []
                user_data["counter"] = 1
                user_data["step"] = 4
                save_user(chat_id, user_data)
                remove_keyboard(chat_id, f"📝 Enter sub-causes for {text}\nFormat: 'cause number' (example: corrosion 1)\n\n🔁 Type 'NEXT' to change main cause\n✅ Type 'FINISH' to finish input")
                return ""
            else:
                send_keyboard(chat_id, "❌ Please choose from the buttons below:", main_causes)
                return ""

    # Step 4: Sub-causes input
    if step == 4:
        if text.upper() == "NEXT":
            user_data["step"] = 3
            save_user(chat_id, user_data)
            if lang == "ar":
                send_keyboard(chat_id, "🔄 اختر سبباً رئيسياً آخر:", main_causes_ar)
            else:
                send_keyboard(chat_id, "🔄 Select another main cause:", main_causes)
            return ""

        if text.upper() == "FINISH":
            total_causes = sum(len(v) for v in user_data["causes_dict"].values())
            if total_causes == 0:
                if lang == "ar":
                    return "❌ الرجاء إدخال سبب واحد على الأقل"
                return "❌ Please enter at least one cause"
            user_data["step"] = 5
            if "step_5_sub" in user_data:
                del user_data["step_5_sub"]
            save_user(chat_id, user_data)
            if lang == "ar":
                return "⏱️ ما هو وقت التشغيل الكلي (بالساعات)؟"
            return "⏱️ What is the total operating time (in hours)?"

        parts = text.strip().split()
        if len(parts) < 2:
            if lang == "ar":
                return "❌ صيغة خاطئة!\nمثال صحيح: 'فساد 1'"
            return "❌ Wrong format!\nCorrect example: 'corrosion 1'"

        try:
            cause_value = int(parts[-1])
        except ValueError:
            if lang == "ar":
                return "❌ الرقم غير صحيح"
            return "❌ The last part must be a number"

        main = user_data["current_main"]
        if main not in user_data["causes_dict"]:
            user_data["causes_dict"][main] = []
        user_data["causes_dict"][main].append(cause_value)
        user_data["counter"] += 1
        save_user(chat_id, user_data)
        if lang == "ar":
            return f"✅ تم الإضافة! ({user_data['counter']-1} سبب)\nأدخل السبب التالي، أو 'FINISH' لإنهاء"
        return f"✅ Added! ({user_data['counter']-1} cause(s))\nEnter next cause, or 'FINISH' to finish"

    # Step 5: Operating parameters
    if step == 5:
        if "step_5_sub" not in user_data:
            user_data["step_5_sub"] = 0

        if user_data["step_5_sub"] == 0:
            try:
                user_data["total"] = float(text.replace(',', '.'))
                user_data["step_5_sub"] = 1
                save_user(chat_id, user_data)
                if lang == "ar":
                    return "⏸️ ما هو وقت التوقف المخطط (بالساعات)؟"
                return "⏸️ What is the planned stop time (in hours)?"
            except:
                if lang == "ar":
                    return "❌ الرجاء إدخال رقم صحيح"
                return "❌ Please enter a valid number"

        if user_data["step_5_sub"] == 1:
            try:
                user_data["stops"] = float(text.replace(',', '.'))
                user_data["step_5_sub"] = 2
                save_user(chat_id, user_data)
                if lang == "ar":
                    return "🔧 كم عدد الأعطال؟"
                return "🔧 How many failures?"
            except:
                if lang == "ar":
                    return "❌ الرجاء إدخال رقم صحيح"
                return "❌ Please enter a valid number"

        if user_data["step_5_sub"] == 2:
            try:
                user_data["fail"] = float(text.replace(',', '.'))
                user_data["step_5_sub"] = 3
                save_user(chat_id, user_data)
                if lang == "ar":
                    return "🛠️ ما هو وقت الإصلاح الكلي (بالساعات)؟"
                return "🛠️ What is the total repair time (in hours)?"
            except:
                if lang == "ar":
                    return "❌ الرجاء إدخال رقم صحيح"
                return "❌ Please enter a valid number"

        if user_data["step_5_sub"] == 3:
            try:
                user_data["repair"] = float(text.replace(',', '.'))

                total = user_data["total"]
                stops = user_data["stops"]
                fail = user_data["fail"]
                repair = user_data["repair"]

                aot = total - stops
                mttr = repair / fail if fail > 0 else 0
                mtbf = aot / fail if fail > 0 else aot
                av = mtbf / (mtbf + mttr) * 100 if (mtbf + mttr) > 0 else 0

                user_data["metrics"] = {"aot": aot, "mttr": mttr, "mtbf": mtbf, "av": av}

                bio1 = metrics_table(aot, mttr, mtbf, av, lang)
                caption1 = "📈 **مقاييس الأداء**" if lang == "ar" else "📈 **Performance Metrics**"
                send_photo(chat_id, bio1.getvalue(), caption1)

                bio2 = pareto_table(user_data["causes_dict"], lang)
                caption2 = "📊 **جدول تحليل باريتو**" if lang == "ar" else "📊 **Pareto Analysis Table**"
                send_photo(chat_id, bio2.getvalue(), caption2)

                bio3 = pareto_chart(user_data["causes_dict"], lang)
                caption3 = "📉 **مخطط باريتو**" if lang == "ar" else "📉 **Pareto Chart**"
                send_photo(chat_id, bio3.getvalue(), caption3)

                user_data["step"] = 6
                user_data["why5_list"] = []
                del user_data["step_5_sub"]
                save_user(chat_id, user_data)

                if lang == "ar":
                    return f"🔍 **تحليل 5 لماذا**\n\nلماذا ({user_data['problem']})؟"
                return f"🔍 **5 Why Analysis**\n\nWhy ({user_data['problem']})?"

            except Exception as e:
                return f"❌ Error: {e}"

    # Step 6: 5 Why
    if step == 6:
        user_data["why5_list"].append(text)

        if len(user_data["why5_list"]) < 5:
            save_user(chat_id, user_data)
            if lang == "ar":
                return f"❓ لماذا ({text})؟"
            return f"❓ Why ({text})?"
        else:
            causes_dict = user_data["causes_dict"]
            counts = {k: sum(v) for k, v in causes_dict.items()}
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_causes = [x[0] for x in sorted_items[:2]]

            metrics = user_data.get("metrics", {})
            mtbf = metrics.get("mtbf", 0)
            mttr = metrics.get("mttr", 0)
            availability = metrics.get("av", 0)

            bio4 = why5_table(user_data["problem"], user_data["why5_list"], lang)
            caption4 = "🔍 **تحليل 5 لماذا**" if lang == "ar" else "🔍 **5 Why Analysis**"
            send_photo(chat_id, bio4.getvalue(), caption4)

            result1 = professional_root_cause_with_recommendation(
                why5_list=user_data["why5_list"],
                top_causes=top_causes,
                mtbf=mtbf,
                mttr=mttr,
                availability=availability,
                primary_cause=top_causes[0] if top_causes else "Unknown",
                lang=lang
            )

            root_cause, recommendation, top_causes2 = smart_analysis(
                user_data["causes_dict"],
                user_data.get("metrics", {}),
                user_data["why5_list"],
                user_data["problem"]
            )

            summary = "📋 **ملخص الأسباب المدخلة:**\n\n" if lang == "ar" else "📋 **Summary of Entered Causes:**\n\n"
            for cause, values in user_data["causes_dict"].items():
                summary += f"• **{cause}**: {len(values)} سبب (القيم: {values})\n" if lang == "ar" else f"• **{cause}**: {len(values)} cause(s) (values: {values})\n"

            user_data["step"] = 7
            save_user(chat_id, user_data)

            final_message = result1 + "\n\n" + "🧠 **التحليل الذكي:**\n" + root_cause + "\n\n" + summary + "\n\n🎉 **اكتمل التحليل!**\nأرسل /reset لبدء تحليل جديد"
            if lang != "ar":
                final_message = result1 + "\n\n" + "🧠 **Smart Analysis:**\n" + root_cause + "\n\n" + summary + "\n\n🎉 **Analysis Completed!**\nSend /reset to start a new analysis"
            
            send_message(chat_id, final_message)
            return ""

    if step == 7:
        if lang == "ar":
            send_message(chat_id, "✅ التحليل مكتمل بالفعل!\nأرسل /reset لبدء تحليل جديد")
        else:
            send_message(chat_id, "✅ Analysis already completed!\nSend /reset to start a new analysis")
        return ""

    return f"✅ Received: {text}"

# ========= COMMAND HANDLERS =========
def start_handler(chat_id):
    old_lang = get_user(chat_id).get("language", "en")
    delete_user(chat_id)
    user_data = get_user(chat_id)
    user_data["language"] = old_lang
    user_data["step"] = 1
    user_data["causes_dict"] = {}
    user_data["counter"] = 1
    user_data["why5_list"] = []
    if "step_5_sub" in user_data:
        del user_data["step_5_sub"]
    save_user(chat_id, user_data)

    lang = user_data.get("language", "en")
    if lang == "ar":
        send_message(chat_id, """🤖 **مرحباً بك في بوت تحليل الجودة المتطور!**

سأساعدك في تحليل مشكلات الجودة باستخدام:
📊 تحليل باريتو
🔍 تحليل 5 لماذا
📈 مقاييس MTBF و MTTR
🧠 تحليل ذكي للسبب الجذري

📝 **ما هي المشكلة التي تواجهها؟**""")
    else:
        send_message(chat_id, """🤖 **Welcome to Quality Analysis Bot!**

I will help you analyze quality problems using:
📊 Pareto Analysis
🔍 5 Why Analysis
📈 MTBF & MTTR Metrics
🧠 Smart Root Cause Analysis

📝 **What is the problem you are facing?**""")
    return ""

def reset_handler(chat_id):
    delete_user(chat_id)
    lang = get_user(chat_id).get("language", "en")
    if lang == "ar":
        send_message(chat_id, "✅ تم إعادة التعيين!\nأرسل /start لبدء تحليل جديد")
    else:
        send_message(chat_id, "✅ Reset completed!\nSend /start to begin a new analysis")
    return ""

def status_handler(chat_id):
    user_data = get_user(chat_id)
    step = user_data.get("step", 1)
    problem = user_data.get("problem", "غير محدد" if user_data.get("language") == "ar" else "Not set")
    lang = user_data.get("language", "en")

    if lang == "ar":
        status_text = f"📊 **حالة التحليل**\n\n"
        status_text += f"📝 المشكلة: {problem}\n"
        status_text += f"🔢 المرحلة: {step}/7\n"

        if user_data.get("causes_dict"):
            total_causes = sum(len(v) for v in user_data["causes_dict"].values())
            status_text += f"📋 عدد الأسباب المدخلة: {total_causes}\n"

        if user_data.get("why5_list"):
            status_text += f"❓ تحليل 5 لماذا: {len(user_data['why5_list'])}/5\n"
    else:
        status_text = f"📊 **Analysis Status**\n\n"
        status_text += f"📝 Problem: {problem}\n"
        status_text += f"🔢 Step: {step}/7\n"

        if user_data.get("causes_dict"):
            total_causes = sum(len(v) for v in user_data["causes_dict"].values())
            status_text += f"📋 Causes entered: {total_causes}\n"

        if user_data.get("why5_list"):
            status_text += f"❓ 5 Why Analysis: {len(user_data['why5_list'])}/5\n"

    send_message(chat_id, status_text)
    return ""

def help_handler(chat_id, lang):
    if lang == "ar":
        help_text = """🤖 **مساعدة البوت**

**الأوامر:**
/start - بدء تحليل جديد
/reset - إعادة تعيين الجلسة
/status - عرض حالة التحليل الحالي
/help - عرض هذه المساعدة
/lang - تغيير اللغة

**كيفية الاستخدام:**
1️⃣ اكتب المشكلة التي تواجهها
2️⃣ اكتب اسم القسم (إنتاج، صيانة، جودة...)
3️⃣ اختر السبب الرئيسي من الأزرار
4️⃣ أدخل الأسباب الفرعية مع أرقام (مثال: 'سبب 1')
5️⃣ استخدم 'NEXT' لتغيير السبب الرئيسي
6️⃣ استخدم 'FINISH' لإنهاء إدخال الأسباب
7️⃣ أدخل بيانات التشغيل المطلوبة
8️⃣ أجب على 5 أسئلة "لماذا"
9️⃣ احصل على تقرير تحليل كامل مع رسوم بيانية

**مثال:**
- المشكلة: "توقف متكرر للآلة"
- القسم: "الإنتاج"
- سبب رئيسي: "الآلة"
- أسباب فرعية: "تآكل محمل 1"، "خلل كهربائي 2"
- بيانات التشغيل: 1000 ساعة، 50 ساعة توقف، 10 أعطال، 30 ساعة إصلاح"""
    else:
        help_text = """🤖 **Bot Help**

**Commands:**
/start - Start a new analysis
/reset - Reset current session
/status - Show current analysis status
/help - Show this help message
/lang - Change language

**How to use:**
1️⃣ Enter the problem you're facing
2️⃣ Enter the department name
3️⃣ Select the main cause from buttons
4️⃣ Enter sub-causes with numbers (example: 'cause 1')
5️⃣ Use 'NEXT' to change the main cause
6️⃣ Use 'FINISH' to finish entering causes
7️⃣ Enter the required operating parameters
8️⃣ Answer 5 "Why" questions
9️⃣ Get a complete analysis report with charts

**Example:**
- Problem: "Frequent machine stoppage"
- Department: "Production"
- Main cause: "Machine"
- Sub-causes: "Bearing wear 1", "Electrical fault 2"
- Operating data: 1000 hours, 50 hours stop, 10 failures, 30 hours repair"""
    
    send_message(chat_id, help_text)
    return ""

# ========= PROCESS MESSAGE =========
def process_message(chat_id, text):
    try:
        user_data = get_user(chat_id)
        lang = user_data.get("language", "en")
        
        if text == '/start':
            start_handler(chat_id)
        elif text == '/reset':
            reset_handler(chat_id)
        elif text == '/status':
            status_handler(chat_id)
        elif text == '/help':
            help_handler(chat_id, lang)
        elif text == '/lang' or text in ["English 🇬🇧", "العربية 🇸🇦"]:
            lang_handler(chat_id, text)
        else:
            reply = handle_message(chat_id, text)
            if reply:
                send_message(chat_id, reply)
    except Exception as e:
        send_message(chat_id, f"❌ Error: {str(e)}")

# ========= WEBHOOK =========
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data and 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')
            process_message(chat_id, text)
    except Exception as e:
        print(f"Webhook error: {e}")
    return 'OK', 200

@app.route('/')
def index():
    return """<!DOCTYPE html>
<html>
<head><title>Quality Analysis Bot</title>
<style>
body{font-family:Arial;text-align:center;padding:50px;background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;}
.container{background:rgba(255,255,255,0.1);border-radius:20px;padding:40px;max-width:500px;margin:auto;}
h1{font-size:48px;}
.status{color:#22c55e;font-size:20px;margin:20px 0;}
.bot-link{background:#1e293b;padding:10px;border-radius:10px;margin:20px 0;}
.footer{margin-top:30px;font-size:12px;opacity:0.7;}
</style>
</head>
<body>
<div class=container>
<h1>🤖📊</h1>
<h1>Quality Analysis Bot</h1>
<div class=status>🟢 ONLINE</div>
<p>تحليل الجودة باستخدام:</p>
<p>📊 Pareto | 🔍 5 Why | 📈 MTBF/MTTR</p>
<div class=bot-link>👉 <strong>@ishikawa1_bot</strong></div>
<div class=footer>Powered by Render.com</div>
</div>
</body>
</html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
