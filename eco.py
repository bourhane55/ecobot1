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

# ========= BOT COMMANDS =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data = get_user(uid)
    user_data["step"] = 1
    user_data["causes_dict"] = {}
    user_data["counter"] = 1
    user_data["why5_list"] = []
    save_user(uid, user_data)
    
    await update.message.reply_text(
        "Welcome to the Advanced Quality Analysis Bot! 🤖\n\n"
        "I will help you analyze quality problems using:\n"
        "📊 Pareto Analysis\n"
        "🔍 5 Why Analysis\n"
        "📈 MTBF & MTTR Metrics\n\n"
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
            # Step 5.0: Total operating time
            if "total" not in user_data:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["total"] = float(clean_text)
                    user_data["step"] = 5.1
                    save_user(uid, user_data)
                    await update.message.reply_text("⏸️ What is the planned stop time (in hours)?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number (example: 100 or 100.5)")
                return
            
            # Step 5.1: Planned stops
            if "stops" not in user_data:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["stops"] = float(clean_text)
                    user_data["step"] = 5.2
                    save_user(uid, user_data)
                    await update.message.reply_text("🔧 How many failures?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number")
                return
            
            # Step 5.2: Number of failures
            if "fail" not in user_data:
                try:
                    clean_text = text.replace(',', '.').strip()
                    user_data["fail"] = float(clean_text)
                    user_data["step"] = 5.3
                    save_user(uid, user_data)
                    await update.message.reply_text("🛠️ What is the total repair time (in hours)?")
                except ValueError:
                    await update.message.reply_text("❌ Please enter a valid number")
                return
            
            # Step 5.3: Total repair time
            if "repair" not in user_data:
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
                    
                    user_data["step"] = 6
                    user_data["why5_list"] = []
                    save_user(uid, user_data)
                    
                    await update.message.reply_text(f"🔍 **5 Why Analysis**\n\nWhy ({user_data['problem']})?")
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {e}")
                    user_data["step"] = 5
                    save_user(uid, user_data)
                return
        
        # Step 6: 5 Why Analysis
        if step == 6:
            user_data["why5_list"].append(text)
            
            if len(user_data["why5_list"]) < 5:
                save_user(uid, user_data)
                prev_why = user_data["why5_list"][-1]
                await update.message.reply_text(f"❓ Why ({prev_why})?")
            else:
                causes_dict = user_data["causes_dict"]
                counts = {k: sum(v) for k, v in causes_dict.items()}
                sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_causes = [x[0] for x in sorted_items[:2]]
                
                metrics = user_data.get("metrics", {})
                mtbf = metrics.get("mtbf", 0)
                mttr = metrics.get("mttr", 0)
                
                last_why = user_data["why5_list"][-1].lower() if user_data["why5_list"] else ""
                
                maintenance_keywords = ["maintenance", "صيانة", "réparation"]
                human_keywords = ["operator", "human", "worker", "عامل", "مستخدم", "training"]
                material_keywords = ["material", "materials", "مواد", "matière", "quality"]
                machine_keywords = ["machine", "equipment", "آلة", "device"]
                management_keywords = ["management", "إدارة", "supervision"]
                
                if any(word in last_why for word in maintenance_keywords):
                    root_cause = "Lack of preventive maintenance program"
                    recommendation = "Implement preventive maintenance system, schedule regular inspections"
                elif any(word in last_why for word in human_keywords):
                    root_cause = "Insufficient skills or human error"
                    recommendation = "Provide intensive training programs, document procedures"
                elif any(word in last_why for word in material_keywords):
                    root_cause = "Poor material quality or non-conforming materials"
                    recommendation = "Evaluate suppliers, inspect incoming materials"
                elif any(word in last_why for word in machine_keywords):
                    root_cause = "Frequent equipment failures"
                    recommendation = "Implement predictive maintenance, upgrade old equipment"
                elif any(word in last_why for word in management_keywords):
                    root_cause = "Weak management and supervision"
                    recommendation = "Improve monitoring system, define KPIs"
                else:
                    root_cause = f"Multiple factors: {top_causes[0] if top_causes else 'Unknown'}"
                    recommendation = "Detailed analysis of identified causes, implement corrective actions"
                
                img4 = why5_table(user_data["problem"], user_data["why5_list"])
                await update.message.reply_photo(img4, caption="🔍 **5 Why Analysis**", parse_mode='Markdown')
                
                final_report = f"""
🎯 **Final Quality Analysis Report**

📝 **Problem:** {user_data['problem']}
🏭 **Department:** {user_data.get('department', 'Not specified')}

📊 **Top Causes (Pareto):**
{', '.join(top_causes)}

📈 **Metrics:**
• MTBF: {mtbf:.2f} hours
• MTTR: {mttr:.2f} hours
• Availability: {metrics.get('av', 0):.2f}%

🔍 **Root Cause:**
{root_cause}

💡 **Recommendations:**
{recommendation}

✅ Analysis completed by Quality Analysis Bot
"""
                
                await update.message.reply_text(final_report, parse_mode='Markdown')
                
                summary = "📋 **Summary of Entered Causes:**\n\n"
                for cause, values in causes_dict.items():
                    summary += f"• **{cause}**: {len(values)} cause(s) (values: {values})\n"
                await update.message.reply_text(summary, parse_mode='Markdown')
                
                user_data["step"] = 7
                save_user(uid, user_data)
                
                await update.message.reply_text(
                    "🎉 **Analysis Completed!**\n\n"
                    "For a new analysis, send /reset then /start"
                )
        
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

if __name__ == "__main__":
    main()
