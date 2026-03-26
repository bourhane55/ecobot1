from telegram import Update, ReplyKeyboardMarkup, InputFile, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib.pyplot as plt
import io

TOKEN = '8299170161:AAHCsVWMp4aiGGTj_R9O2iaL7NmYPWWoT_s'

users = {}
main_causes = ["Method", "Materials", "Measurement", "Human", "Machine", "Environment"]

# ========= ???? ???????? =========
def metrics_table(aot, mttr, mtbf, av):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.axis('off')
    mtbf_note = "Good" if mtbf >= 100 else "Low"
    mttr_note = "Good" if mttr <= 2 else "High"
    av_note = "Excellent" if av >= 95 else "Average" if av >= 85 else "Low"
    data = [
        ["Actual Operating Time", f"{aot:.2f} h", ""],
        ["MTTR", f"{mttr:.2f} h", mttr_note],
        ["MTBF", f"{mtbf:.2f} h", mtbf_note],
        ["Availability", f"{av:.2f} %", av_note]
    ]
    table = ax.table(cellText=data, colLabels=["Metric", "Value", "Observation"], loc="center")
    table.scale(1, 2)
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight")
    bio.seek(0)
    plt.close()
    return bio

# ========= Pareto Table =========
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
    fig, ax = plt.subplots(figsize=(6, len(rows)*0.5+1))
    ax.axis('off')
    table = ax.table(cellText=rows, colLabels=["Main Cause", "Count", "%", "Cumulative %"], loc="center")
    table.scale(1, 2)
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight")
    bio.seek(0)
    plt.close()
    return bio

# ========= Pareto Chart (?? ??????) =========
def pareto_chart(causes_dict):
    counts = {k: len(v) for k, v in causes_dict.items()}
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    labels = [x[0] for x in sorted_items]
    values = [x[1] for x in sorted_items]

    total = sum(values)
    cumulative = []
    cumsum = 0

    for v in values:
        cumsum += v
        cumulative.append((cumsum / total) * 100 if total != 0 else 0)

    fig, ax1 = plt.subplots()

    # ????? ????? ??? ??? ????? ??? ???

    total = sum([x[1] for x in sorted_items])
    percent_values = [(v / total) * 100 if total != 0 else 0 for v in [x[1] for x in sorted_items]]

    ax1.bar(labels, percent_values)
    ax1.set_ylabel("Percentage %")
    # ???????
    ax2 = ax1.twinx()
    ax2.plot(labels, cumulative, marker='o')
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 100)

    # ?? 80% (??????? ??? ???)
    ax2.axhline(80, linestyle='--')

    plt.title("Pareto Chart")

    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight")
    bio.seek(0)
    plt.close()

    return bio

# ========= 5 Why Table =========
def why5_table(problem, why_list):
    fig, ax = plt.subplots(figsize=(8, len(why_list)*0.6+1))
    ax.axis('off')
    rows = [[f"Why {i+1}", why] for i, why in enumerate(why_list)]
    table = ax.table(cellText=rows, colLabels=["Step", f"{problem} 5 Why Analysis"], loc="center")
    table.scale(1, 2)
    bio = io.BytesIO()
    plt.savefig(bio, bbox_inches="tight")
    bio.seek(0)
    plt.close()
    return bio

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users[uid] = {"step": 1, "causes_dict": {}, "counter": 1, "why5_list": []}
    await update.message.reply_text("? What is your problem?")

# ========= RESET =========
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in users:
        del users[uid]
    await update.message.reply_text("?? Reset done. Send /start to begin again.")

# ========= HANDLE =========
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if uid not in users:
        users[uid] = {"step": 1, "causes_dict": {}, "counter": 1, "why5_list": []}

    step = users[uid]["step"]

    # 1?? Problem
    if step == 1:
        users[uid]["problem"] = text
        users[uid]["step"] = 2
        await update.message.reply_text("?? Department?")
        return

    # 2?? Department
    if step == 2:
        users[uid]["department"] = text
        users[uid]["step"] = 3
        keyboard = [
            ["Method", "Materials"],
            ["Measurement", "Human"],
            ["Machine", "Environment"]
        ]
        await update.message.reply_text(
            "Select main cause:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # 3?? Main cause
    if step == 3:
        if text not in main_causes:
            await update.message.reply_text("Choose from buttons")
            return
        users[uid]["current_main"] = text
        if text not in users[uid]["causes_dict"]:
            users[uid]["causes_dict"][text] = []
        users[uid]["counter"] = 1
        users[uid]["step"] = 4
        await update.message.reply_text(
            f"1?? Enter causes inside {text}\nNEXT ? other main cause\nFINISH ? end",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # 4️⃣ Causes input
    if step == 4:
        # حدد الكيبورد قبل أي استخدام
        keyboard = [
            ["Method", "Materials"],
            ["Measurement", "Human"],
            ["Machine", "Environment"]
    ]

        # إذا المستخدم بغى يبدل السبب الرئيسي
        if text.lower() == "next":
            users[uid]["step"] = 3
            await update.message.reply_text(
                "Select another main cause:",
    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
            return

        # إذا المستخدم بغى يكمل ويمشي للحسابات
        if text.lower() == "finish":
            if len(users[uid]["causes_dict"]) == 0:
                await update.message.reply_text("Enter at least one cause")
                return
            users[uid]["step"] = 5
            await update.message.reply_text("Total Operating Time?")
            return

        # الآن ناخدو السبب + الرقم
        main = users[uid]["current_main"]
        try:
            parts = text.strip().split()
            if len(parts) < 2:
                await update.message.reply_text(
                "❌ Enter cause name followed by number, e.g., 'فساد 1'"
            )
                return
            cause_name = " ".join(parts[:-1])
            cause_value = int(parts[-1])

            # نجمع الرقم فقط في causes_dict
            users[uid]["causes_dict"][main].append(cause_value)
            users[uid]["counter"] += 1
            await update.message.reply_text(f"{users[uid]['counter']} Next cause:")

        except ValueError:
            await update.message.reply_text(
            "❌ Last part must be a number, e.g., 'فساد 1'"
        )
        return
    # 5?? Calculations
    if step == 5:
        try:
            if "total" not in users[uid]:
                users[uid]["total"] = float(text)
                await update.message.reply_text("Planned Stops?")
                return

            if "stops" not in users[uid]:
                users[uid]["stops"] = float(text)
                await update.message.reply_text("Failures?")
                return

            if "fail" not in users[uid]:
                users[uid]["fail"] = float(text)
                await update.message.reply_text("Repair Time?")
                return

            if "repair" not in users[uid]:
                users[uid]["repair"] = float(text)

                aot = users[uid]["total"] - users[uid]["stops"]
                mttr = users[uid]["repair"] / users[uid]["fail"] if users[uid]["fail"] else 0
                mtbf = aot / users[uid]["fail"] if users[uid]["fail"] else aot
                av = mtbf / (mtbf + mttr) * 100 if (mtbf + mttr) != 0 else 0

                # Metrics
                img1 = metrics_table(aot, mttr, mtbf, av)
                await update.message.reply_photo(InputFile(img1, "metrics.png"))

                # Pareto Table
                img2 = pareto_table(users[uid]["causes_dict"])
                await update.message.reply_photo(InputFile(img2, "pareto.png"))

                # ?? Pareto Chart (??????)
                img_chart = pareto_chart(users[uid]["causes_dict"])
                await update.message.reply_photo(InputFile(img_chart, "pareto_chart.png"))

                # 5 Why
                users[uid]["step"] = 6
                await update.message.reply_text(f"Why ({users[uid]['problem']})?")
        except:
            await update.message.reply_text("Enter numbers only")
        return

    # 6?? 5 Why
    if step == 6:
        users[uid]["why5_list"].append(text)
        if len(users[uid]["why5_list"]) < 5:
            await update.message.reply_text(f"Why ({users[uid]['why5_list'][-1]})?")
        else:
            try:
            # ========= FINAL PROFESSIONAL ANALYSIS =========

            # Pareto
                counts = {k: sum(v) for k, v in users[uid]["causes_dict"].items()}
                sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_causes = [x[0] for x in sorted_items[:2]]

            # Metrics
                aot = users[uid]["total"] - users[uid]["stops"]
                mttr = users[uid]["repair"] / users[uid]["fail"] if users[uid]["fail"] else 0
                mtbf = aot / users[uid]["fail"] if users[uid]["fail"] else aot
                av = mtbf / (mtbf + mttr) * 100 if (mtbf + mttr) != 0 else 0

            # Decision
                if mtbf < 50 and "Machine" in top_causes:
                    selected = "Machine"
                    reason_metrics = "frequent failures (low MTBF)"
                elif mttr > 3 and "Human" in top_causes:
                    selected = "Human"
                    reason_metrics = "high repair time (high MTTR)"
                else:
                    selected = top_causes[0]
                    reason_metrics = "highest impact from Pareto"

        # 5 Why (آمن)
                last_why = users[uid]["why5_list"][-1].lower()

                maintenance_keywords = ["maintenance", "صيانة", "réparation"]
                human_keywords = ["operator", "human", "worker", "عامل", "مستخدم"]
                material_keywords = ["material", "materials", "مواد", "matière"]
                machine_keywords = ["machine", "equipment", "آلة"]
                management_keywords = ["management", "إدارة"]

                if any(word in last_why for word in maintenance_keywords):
                    final_cause = "Lack of preventive maintenance program"

                elif any(word in last_why for word in human_keywords):
                    final_cause = "Insufficient operator training or human error"

                elif any(word in last_why for word in material_keywords):
                    final_cause = "Poor material quality or unsuitable materials"

                elif any(word in last_why for word in machine_keywords):
                    final_cause = "Equipment malfunction due to inadequate maintenance"

                elif any(word in last_why for word in management_keywords):
                    final_cause = "Ineffective management or lack of supervision"

                elif len(last_why.split()) <= 2:
                    final_cause = f"Unclear root cause, likely related to {selected} process inefficiency"

                else:
                    final_cause = f"Root cause identified as: {last_why}"
                    # ========= SMART RECOMMENDATION (ADVANCED) =========

                lw = last_why.strip().lower()

                if any(word in lw for word in maintenance_keywords):
                    root_cause = "The issue is driven by an ineffective maintenance strategy impacting system reliability."

                    recommendation = (
        "It is recommended to transition toward a proactive maintenance approach, "
        "focusing on preventive planning, scheduling interventions, "
        "and integrating maintenance into operational priorities."
    )

                elif any(word in lw for word in human_keywords):
                    root_cause = "The problem is influenced by human performance variability."

                    recommendation = (
        "Improving human performance requires structured training programs, "
        "clear procedures, and continuous performance monitoring."
    )

                elif any(word in lw for word in material_keywords):
                    root_cause = "The instability is caused by inconsistencies in material quality."

                    recommendation = (
        "Strengthening material control through supplier evaluation and quality checks "
        "is essential to ensure process stability."
    )

                elif any(word in lw for word in machine_keywords):
                    root_cause = "Equipment reliability issues are degrading overall system performance."

                    recommendation = (
        "Implementing predictive maintenance and real-time condition monitoring "
        "will help reduce failures and improve equipment efficiency."
    )

                elif any(word in lw for word in management_keywords):
                    root_cause = "The issue is linked to gaps in management and supervision."

                    recommendation = (
        "Enhancing management practices through better planning, supervision, "
        "and performance tracking is necessary."
    )

                else:
                    root_cause = f"The root cause is associated with underlying factors related to: {last_why}."

                    recommendation = (
        "A detailed analysis of this factor is required, followed by corrective actions "
        "and continuous improvement measures to ensure long-term stability."
    )

        # ========= FINAL TEXT =========
                final_text = (
                    f"🎯 FINAL ROOT CAUSE ANALYSIS\n\n"
                    f"Top Causes: {', '.join(top_causes)}\n"
                    f"Selected Cause: {selected}\n"
                    f"Root Cause: {root_cause}\n\n"
                    f"Metrics:\n"
                    f"MTBF: {mtbf:.2f} h\n"
                    f"MTTR: {mttr:.2f} h\n"
                    f"Availability: {av:.2f}%\n\n"
                    f"Conclusion:\n"
                    f"The main issue is related to {selected} due to {reason_metrics}. "
                    f"The root cause identified is {root_cause}.\n\nRecommendation:\n{recommendation}"
        )

                await update.message.reply_text(final_text)
                users[uid]["step"] = 7

            except Exception as e:
                await update.message.reply_text(f"Error: {e}")
            

# ========= RUN =========
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Eco Analyzer with Pareto Chart Running...")
app.run_polling()

