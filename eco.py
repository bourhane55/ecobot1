from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import json
import os
from datetime import datetime

# ========= SETTINGS =========
TOKEN = '8299170161:AAHCsVWMp4aiGGTj_R9O2iaL7NmYPWWoT_s'
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

# ========= HELPER FUNCTIONS =========
def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "step": 1,
            "causes_dict": {},
            "counter": 1,
            "why5_list": [],
            "created_at": datetime.now().isoformat()
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

# ========= CHART FUNCTIONS =========
def metrics_table(aot, mttr, mtbf, av):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')

    mtbf_note = "✅ Good" if mtbf >= 100 else "⚠️ Low"
    mttr_note = "✅ Good" if mttr <= 2 else "⚠️ High"
    av_note = "✅ Excellent" if av >= 95 else "⚠️ Average" if av >= 85 else "❌ Low"

    data = [
        ["Actual Operating Time", f"{aot:.2f} h", ""],
        ["MTTR (Mean Time To Repair)", f"{mttr:.2f} h", mttr_note],
        ["MTBF (Mean Time Between Failures)", f"{mtbf:.2f} h", mtbf_note],
        ["Availability", f"{av:.2f} %", av_note]
    ]

    table = ax.table(cellText=data, colLabels=["Metric", "Value", "Observation"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def pareto_table(causes_dict):
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

    table = ax.table(cellText=rows, colLabels=["Main Cause", "Count", "%", "Cumulative %"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def pareto_chart(causes_dict):
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
    ax1.set_ylabel("Percentage (%)", fontsize=12)
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(labels, cumulative, marker='o', color='red', linewidth=2, markersize=8)
    ax2.set_ylabel("Cumulative %", fontsize=12)
    ax2.set_ylim(0, 105)
    ax2.axhline(80, linestyle='--', color='gray', alpha=0.7, label='80% Line')

    plt.title("Pareto Chart - Cause Analysis", fontsize=14, pad=20)
    plt.tight_layout()

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

def why5_table(problem, why_list):
    fig, ax = plt.subplots(figsize=(10, len(why_list)*0.8+2))
    ax.axis('off')

    rows = [[f"Why {i+1}", why] for i, why in enumerate(why_list)]
    table = ax.table(cellText=rows, colLabels=["Level", f"5 Why Analysis: {problem}"], loc="center")
    table.scale(1, 2)
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight", dpi=150)
    bio.seek(0)
    plt.close()
    return bio

# ========= SMART ROOT CAUSE ANALYSIS =========
def smart_analysis(causes_dict, metrics, why5_list, problem):
    """
    تحليل ذكي احترافي يجمع بين:
    - Pareto (أهم الأسباب)
    - MTBF & MTTR (المقاييس)
    - 5 Why (التحليل العميق)
    """

    # 1. Pareto Analysis - identify top causes
    counts = {k: sum(v) for k, v in causes_dict.items()}
    sorted_causes = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_causes = [x[0] for x in sorted_causes[:2]] if sorted_causes else ["Unknown"]
    top_cause = top_causes[0]

    # 2. Metrics Analysis
    mtbf = metrics.get('mtbf', 0)
    mttr = metrics.get('mttr', 0)
    availability = metrics.get('av', 0)

    # Determine primary issue based on metrics
    if mtbf < 50:
        metrics_issue = "reliability"
        metrics_root = f"Low MTBF ({mtbf:.1f}h) indicates frequent failures"
    elif mttr > 3:
        metrics_issue = "maintainability"
        metrics_root = f"High MTTR ({mttr:.1f}h) indicates slow repair process"
    elif availability < 85:
        metrics_issue = "overall performance"
        metrics_root = f"Low availability ({availability:.1f}%) indicates combined reliability and maintainability issues"
    else:
        metrics_issue = "process"
        metrics_root = "Metrics within acceptable range, focus on process optimization"

    # 3. 5 Why Analysis - extract root cause chain
    why5_chain = why5_list if why5_list else ["No 5 Why analysis completed"]

    # Analyze keywords in 5 Why responses
    last_why = why5_list[-1].lower() if why5_list else ""

    # Keyword mapping for root cause identification
    keywords = {
        'maintenance': ['maintenance', 'صيانة', 'repair', 'fix', 'breakdown', 'preventive'],
        'training': ['training', 'skill', 'competence', 'operator', 'worker', 'عامل', 'تدريب'],
        'material': ['material', 'supplier', 'quality', 'مواد', 'جودة', 'specification'],
        'machine': ['machine', 'equipment', 'آلة', 'معدة', 'device', 'asset'],
        'process': ['process', 'procedure', 'method', 'طريقة', 'إجراء', 'workflow'],
        'management': ['management', 'supervision', 'leadership', 'إدارة', 'إشراف', 'planning']
    }

    detected_categories = []
    for category, words in keywords.items():
        if any(word in last_why for word in words):
            detected_categories.append(category)

    # 4. Combine all insights to determine root cause
    if 'maintenance' in detected_categories or metrics_issue == 'reliability':
        root_cause_type = "maintenance"
        root_cause = f"The root cause is inadequate maintenance strategy. {metrics_root}. The 5 Why analysis reveals maintenance-related issues: '{last_why[:100]}'"
        recommendation = """• Implement a preventive maintenance program
• Schedule regular equipment inspections
• Develop maintenance checklists and procedures
• Train maintenance staff on predictive techniques
• Establish spare parts inventory management
• Monitor MTBF trends weekly"""

    elif 'training' in detected_categories or 'human' in top_cause.lower() or metrics_issue == 'maintainability':
        root_cause_type = "human"
        root_cause = f"The root cause is insufficient operator skills and training. {metrics_root}. The analysis indicates: '{last_why[:100]}'"
        recommendation = """• Develop comprehensive training programs
• Create and document standard operating procedures
• Implement a mentoring system
• Conduct regular competency assessments
• Establish clear work instructions
• Monitor MTTR trends and training effectiveness"""

    elif 'material' in detected_categories or 'Materials' in top_cause:
        root_cause_type = "material"
        root_cause = f"The root cause is material quality issues. {metrics_root}. The 5 Why analysis reveals: '{last_why[:100]}'"
        recommendation = """• Evaluate and audit suppliers
• Implement incoming material inspection
• Establish material specifications
• Work with suppliers on quality improvement
• Implement traceability system
• Monitor defect rates by supplier"""

    elif 'machine' in detected_categories or 'Machine' in top_cause:
        root_cause_type = "machine"
        root_cause = f"The root cause is equipment degradation. {metrics_root}. The analysis shows: '{last_why[:100]}'"
        recommendation = """• Implement predictive maintenance
• Upgrade critical equipment
• Monitor equipment condition in real-time
• Establish equipment replacement strategy
• Implement condition-based monitoring
• Track MTBF by equipment type"""

    elif 'process' in detected_categories or 'Method' in top_cause:
        root_cause_type = "process"
        root_cause = f"The root cause is process inefficiency. {metrics_root}. The analysis indicates: '{last_why[:100]}'"
        recommendation = """• Map and analyze current process
• Identify bottlenecks and waste
• Implement process improvements
• Standardize work methods
• Conduct time and motion studies
• Monitor process KPIs"""

    elif 'management' in detected_categories:
        root_cause_type = "management"
        root_cause = f"The root cause is management system gaps. {metrics_root}. The analysis reveals: '{last_why[:100]}'"
        recommendation = """• Implement performance management system
• Establish clear roles and responsibilities
• Conduct regular management reviews
• Improve communication channels
• Define and track KPIs
• Implement continuous improvement culture"""

    else:
        root_cause_type = "combined"
        root_cause = f"The root cause involves multiple factors. Primary factor: {top_cause}. {metrics_root}. Key insight: '{last_why[:100]}'"
        recommendation = f"""• Focus improvement on {top_cause} related processes
• Conduct detailed analysis of contributing factors
• Implement corrective actions based on findings
• Monitor all identified metrics
• Establish regular review meetings
• Document lessons learned"""

    # 5. Add specific metrics-driven insights
    if mtbf < 50:
        root_cause += f" Critical reliability issue: MTBF is {mtbf:.1f}h (target >100h)."
    if mttr > 3:
        root_cause += f" Maintainability concern: MTTR is {mttr:.1f}h (target <2h)."
    if availability < 85:
        root_cause += f" Overall performance impacted: Availability at {availability:.1f}% (target >95%)."

    return root_cause, recommendation, top_causes

# ========= PROFESSIONAL ROOT CAUSE ANALYSIS WITH RECOMMENDATION =========
def professional_root_cause_with_recommendation(why5_list, top_causes, mtbf, mttr, availability, primary_cause):
    """
    Professional analysis of all 5 Why answers
    Provides detailed root cause + practical recommendation
    """

    # Analyze all answers
    why_chain = ""
    for i, answer in enumerate(why5_list, 1):
        why_chain += f"- Why {i}: \"{answer}\" → "
        if i == 1:
            why_chain += "initial symptom\n"
        elif i == 2:
            why_chain += "immediate cause\n"
        elif i == 3:
            why_chain += "underlying factor\n"
        elif i == 4:
            why_chain += "systemic gap\n"
        else:
            why_chain += "root cause level\n"

    # Extract keywords from all answers
    full_text = " ".join(why5_list).lower()

    # Determine category and recommendation
    if any(word in full_text for word in ["maintenance", "صيانة", "program", "schedule", "repair"]):
        category = "Maintenance System"
        root = "The organization lacks a structured preventive maintenance system, from management planning down to execution level."
        impact = f"This leads to frequent equipment failures (MTBF: {mtbf:.1f}h), extended repair times (MTTR: {mttr:.1f}h), and reduced availability ({availability:.1f}%)."
        recommendation = f"""📋 **RECOMMENDATION:**

1. **Establish Preventive Maintenance Program:** Create a regular inspection schedule for all equipment based on manufacturer recommendations.
2. **Assign Maintenance Responsibility:** Dedicate a specialized maintenance team with clear roles and responsibilities.
3. **Develop Tracking System:** Create an electronic maintenance log to track failures and repairs.
4. **Train Maintenance Team:** Provide training on predictive and preventive maintenance techniques.
5. **Regular Review:** Conduct weekly meetings to review performance indicators (MTBF, MTTR).

**Target:** Increase MTBF from {mtbf:.1f}h to over 100h within 3 months."""

    elif any(word in full_text for word in ["training", "تدريب", "skill", "operator", "worker", "error"]):
        category = "Training & Skills Gap"
        root = "Insufficient operator training and skill development programs exist, resulting in improper equipment handling and operational errors."
        impact = f"This contributes to human errors, increased repair time (MTTR: {mttr:.1f}h), and quality issues."
        recommendation = f"""📋 **RECOMMENDATION:**

1. **Develop Training Program:** Create a comprehensive training plan for all operators.
2. **Document Procedures:** Write Standard Operating Procedures (SOP) and train workers on them.
3. **Mentorship System:** Assign experienced supervisors to guide new workers.
4. **Skill Assessment:** Conduct regular tests to measure worker competency.
5. **Performance Rewards:** Reward workers who excel in performance and procedure adherence.

**Target:** Reduce MTTR from {mttr:.1f}h to under 2 hours within 2 months."""

    elif any(word in full_text for word in ["material", "مادة", "quality", "supplier", "raw"]):
        category = "Material Quality Control"
        root = "Weak incoming material inspection and supplier quality management allow substandard materials to enter production."
        impact = f"This causes frequent defects and process instability, affecting MTBF ({mtbf:.1f}h) and product quality."
        recommendation = f"""📋 **RECOMMENDATION:**

1. **Evaluate Suppliers:** Review current supplier performance and classify them by quality.
2. **Inspect Incoming Materials:** Establish inspection system for materials before accepting into inventory.
3. **Define Specifications:** Document precise technical specifications for each raw material.
4. **Contract Certified Suppliers:** Select suppliers with recognized quality certifications.
5. **Monitor Performance:** Track defect rates related to materials and provide monthly reports.

**Target:** Reduce material-related defects by 50% within 3 months."""

    elif any(word in full_text for word in ["management", "إدارة", "planning", "supervision", "organization"]):
        category = "Management System"
        root = "Inadequate planning, supervision, and performance monitoring systems fail to establish clear accountability."
        impact = f"This creates gaps across all operational levels, reflected in poor reliability metrics (MTBF: {mtbf:.1f}h)."
        recommendation = f"""📋 **RECOMMENDATION:**

1. **Define KPIs:** Establish clear Key Performance Indicators for each department.
2. **Regular Review Meetings:** Conduct weekly meetings to review performance and analyze deviations.
3. **Document Responsibilities:** Create detailed job descriptions with clear authorities.
4. **Tracking System:** Implement an electronic system to monitor task execution.
5. **Continuous Improvement Culture:** Encourage employees to submit improvement suggestions and reward them.

**Target:** Achieve 20% improvement in all performance indicators within 6 months."""

    else:
        category = primary_cause
        root = f"The primary issue centers on {primary_cause}, with contributing factors identified through the 5 Why analysis."
        impact = f"This affects equipment reliability (MTBF: {mtbf:.1f}h) and repair efficiency (MTTR: {mttr:.1f}h)."
        recommendation = f"""📋 **RECOMMENDATION:**

1. **Detailed Analysis:** Conduct in-depth study of {primary_cause} to identify weaknesses precisely.
2. **Implement Corrective Actions:** Develop action plan to address identified causes.
3. **Monitor Indicators:** Track MTBF and MTTR weekly.
4. **Review Results:** Evaluate effectiveness of actions 30 days after implementation.
5. **Expand Improvements:** Apply lessons learned to other departments.

**Target:** Increase availability to over 90% within 3 months."""

    # Build final result
    result = f"""
🔍 **ROOT CAUSE ANALYSIS**

After analyzing the 5 Why chain, the following root cause has been identified:

**Primary Factor:** {category}
**Contributing Elements:** {root.split('.')[0]}

**Evidence from 5 Why:**
{why_chain}

**Conclusion:**
{root}

**Impact on Metrics:**
- MTBF: {mtbf:.1f}h {"(below target)" if mtbf < 100 else "(acceptable)"}
- MTTR: {mttr:.1f}h {"(above target)" if mttr > 2 else "(acceptable)"}
- Availability: {availability:.1f}%
- Top Pareto Cause: {primary_cause}

**Root Cause Statement:**
{root} {impact}

{recommendation}
"""
    return result

# ========= BOT COMMANDS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data = get_user(uid)
    user_data["step"] = 1
    user_data["causes_dict"] = {}
    user_data["counter"] = 1
    user_data["why5_list"] = []
    if "step_5_sub" in user_data:
        del user_data["step_5_sub"]
    save_user(uid, user_data)

    await update.message.reply_text(
        "Welcome to the Advanced Quality Analysis Bot! 🤖\n\n"
        "I will help you analyze quality problems using:\n"
        "📊 Pareto Analysis\n"
        "🔍 5 Why Analysis\n"
        "📈 MTBF & MTTR Metrics\n"
        "🧠 Smart Root Cause Analysis\n\n"
        "📝 What is the problem you are facing?"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    delete_user(uid)
    await update.message.reply_text(
        "✅ Reset completed successfully!\n"
        "Send /start to begin a new analysis"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data = get_user(uid)

    step = user_data.get("step", 1)
    problem = user_data.get("problem", "Not set")

    status_text = f"📊 **Analysis Status**\n\n"
    status_text += f"📝 Problem: {problem}\n"
    status_text += f"🔢 Step: {step}/7\n"

    if user_data.get("causes_dict"):
        total_causes = sum(len(v) for v in user_data["causes_dict"].values())
        status_text += f"📋 Causes entered: {total_causes}\n"

    if user_data.get("why5_list"):
        status_text += f"❓ 5 Why Analysis: {len(user_data['why5_list'])}/5\n"

    await update.message.reply_text(status_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **Quality Analysis Bot Help**

**Available Commands:**
/start - Start a new analysis
/reset - Reset current session
/status - Show current analysis status
/help - Show this help message

**How to Use:**
1️⃣ Enter the problem
2️⃣ Enter the department
3️⃣ Select the main cause
4️⃣ Enter sub-causes with numbers (example: 'corrosion 1')
5️⃣ Use 'NEXT' to change main cause
6️⃣ Use 'FINISH' to finish entering causes
7️⃣ Enter operating parameters
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ========= MESSAGE HANDLER =========
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    try:
        user_data = get_user(uid)
        step = user_data.get("step", 1)

        # Step 1: Problem
        if step == 1:
            user_data["problem"] = text
            user_data["step"] = 2
            save_user(uid, user_data)
            await update.message.reply_text("🏭 What is the department? (e.g., Production, Maintenance, Quality)")
            return

        # Step 2: Department
        if step == 2:
            user_data["department"] = text
            user_data["step"] = 3
            save_user(uid, user_data)

            keyboard = [[cause] for cause in main_causes]
            await update.message.reply_text(
                "🔍 Select the main cause:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

        # Step 3: Main cause selection
        if step == 3:
            if text not in main_causes:
                await update.message.reply_text("❌ Please choose a cause from the buttons")
                return

            user_data["current_main"] = text
            if text not in user_data["causes_dict"]:
                user_data["causes_dict"][text] = []
            user_data["counter"] = 1
            user_data["step"] = 4
            save_user(uid, user_data)

            await update.message.reply_text(
                f"📝 Enter sub-causes for {text}\n"
                f"Format: 'cause number' (example: corrosion 1)\n\n"
                f"🔁 Type 'NEXT' to change main cause\n"
                f"✅ Type 'FINISH' to finish input",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # Step 4: Sub-causes input
        if step == 4:
            if text.upper() == "NEXT":
                user_data["step"] = 3
                save_user(uid, user_data)
                keyboard = [[cause] for cause in main_causes]
                await update.message.reply_text(
                    "🔄 Select another main cause:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text.upper() == "FINISH":
                total_causes = sum(len(v) for v in user_data["causes_dict"].values())
                if total_causes == 0:
                    await update.message.reply_text("❌ Please enter at least one cause")
                    return
                user_data["step"] = 5
                if "step_5_sub" in user_data:
                    del user_data["step_5_sub"]
                save_user(uid, user_data)
                await update.message.reply_text("⏱️ What is the total operating time (in hours)?")
                return

            parts = text.strip().split()
            if len(parts) < 2:
                await update.message.reply_text("❌ Wrong format!\nCorrect example: 'corrosion 1'")
                return

            cause_name = " ".join(parts[:-1])
            try:
                cause_value = int(parts[-1])
            except ValueError:
                await update.message.reply_text("❌ The last part must be a number")
                return

            main = user_data["current_main"]
            user_data["causes_dict"][main].append(cause_value)
            user_data["counter"] += 1
            save_user(uid, user_data)

            await update.message.reply_text(
                f"✅ Added! ({user_data['counter']-1} cause(s))\n"
                f"Enter next cause, or 'FINISH' to finish"
            )
            return

        # Step 5: Operating parameters
        if step == 5:
            if "step_5_sub" not in user_data:
                user_data["step_5_sub"] = 0

            if user_data["step_5_sub"] == 0:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["total"] = float(clean_text)
                    user_data["step_5_sub"] = 1
                    save_user(uid, user_data)
                    await update.message.reply_text("⏸️ What is the planned stop time (in hours)?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number")
                return

            if user_data["step_5_sub"] == 1:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["stops"] = float(clean_text)
                    user_data["step_5_sub"] = 2
                    save_user(uid, user_data)
                    await update.message.reply_text("🔧 How many failures?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number")
                return

            if user_data["step_5_sub"] == 2:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["fail"] = float(clean_text)
                    user_data["step_5_sub"] = 3
                    save_user(uid, user_data)
                    await update.message.reply_text("🛠️ What is the total repair time (in hours)?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number")
                return

            if user_data["step_5_sub"] == 3:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["repair"] = float(clean_text)

                    total = user_data["total"]
                    stops = user_data["stops"]
                    fail = user_data["fail"]
                    repair = user_data["repair"]

                    aot = total - stops
                    mttr = repair / fail if fail > 0 else 0
                    mtbf = aot / fail if fail > 0 else aot
                    av = mtbf / (mtbf + mttr) * 100 if (mtbf + mttr) > 0 else 0

                    user_data["metrics"] = {"aot": aot, "mttr": mttr, "mtbf": mtbf, "av": av}

                    await update.message.reply_text("📊 Generating reports...")

                    img1 = metrics_table(aot, mttr, mtbf, av)
                    await update.message.reply_photo(img1, caption="📈 **Performance Metrics**", parse_mode='Markdown')

                    img2 = pareto_table(user_data["causes_dict"])
                    await update.message.reply_photo(img2, caption="📊 **Pareto Analysis Table**", parse_mode='Markdown')

                    img3 = pareto_chart(user_data["causes_dict"])
                    await update.message.reply_photo(img3, caption="📉 **Pareto Chart**", parse_mode='Markdown')

                    del user_data["step_5_sub"]
                    user_data["step"] = 6
                    user_data["why5_list"] = []
                    save_user(uid, user_data)

                    await update.message.reply_text(f"🔍 **5 Why Analysis**\n\nWhy ({user_data['problem']})?")

                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {e}")
                    user_data["step_5_sub"] = 0
                    save_user(uid, user_data)
                return

        # Step 6: 5 Why Analysis
        if step == 6:
            user_data["why5_list"].append(text)

            if len(user_data["why5_list"]) < 5:
                save_user(uid, user_data)
                prev_why = user_data["why5_list"][-1]
                await update.message.reply_text(f"❓ Why ({prev_why})?")
                return

            # ===== جمع البيانات للتحليل =====
            causes_dict = user_data["causes_dict"]
            counts = {k: sum(v) for k, v in causes_dict.items()}
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top_causes = [x[0] for x in sorted_items[:2]]

            metrics = user_data.get("metrics", {})
            mtbf = metrics.get("mtbf", 0)
            mttr = metrics.get("mttr", 0)
            availability = metrics.get("av", 0)

            # ===== عرض جدول 5 لماذا =====
            img4 = why5_table(user_data["problem"], user_data["why5_list"])
            await update.message.reply_photo(img4, caption="🔍 **5 Why Analysis**", parse_mode='Markdown')

            # ===== استدعاء الدالة الجديدة =====
            result = professional_root_cause_with_recommendation(
                why5_list=user_data["why5_list"],
                top_causes=top_causes,
                mtbf=mtbf,
                mttr=mttr,
                availability=availability,
                primary_cause=top_causes[0] if top_causes else "Unknown"
            )

            # ===== إرسال التحليل =====
            await update.message.reply_text(result)

            # ===== ملخص الأسباب =====
            summary = "📋 **Summary of Entered Causes:**\n\n"
            for cause, values in user_data["causes_dict"].items():
                summary += f"• **{cause}**: {len(values)} cause(s) (values: {values})\n"
            await update.message.reply_text(summary, parse_mode='Markdown')

            user_data["step"] = 7
            save_user(uid, user_data)

            await update.message.reply_text(
                "🎉 **Analysis Completed!**\n\n"
                "For a new analysis, send /reset then /start"
            )
            return

        # Step 7: Completed
        if step == 7:
            await update.message.reply_text(
                "✅ Analysis already completed!\n"
                "Send /reset to start a new analysis"
            )
            return

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\nPlease try again or use /reset")
        print(f"Error: {e}")

# ========= RUN BOT =========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot is running...")
    app.run_polling()
from flask import Flask, request
import requests

# ========= إعداد Flask =========
app = Flask(name)
TOKEN = '8299170161:AAHCsVWMp4aiGGTj_R9O2iaL7NmYPWWoT_s'

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data and 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')

            # رد بسيط للاختبار
            reply = f"تم استلام: {text}"

            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': reply})
    except Exception as e:
        print(f"Error: {e}")
    return 'OK', 200

@app.route('/')
def index():
    return "Bot is running on PythonAnywhere!"
if __name__ == "__main__":
    main()











