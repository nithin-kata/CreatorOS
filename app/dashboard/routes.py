from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from app.models import db, Goal, Content, Activity
from app.services.opportunity_service import get_todays_opportunity, get_opportunity_alerts, refresh_niche_opportunities

dashboard = Blueprint('dashboard', __name__)

def calculate_streak(user_id):
    """
    Calculates the consecutive active day streak for a user.
    """
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.activity_date.desc()).all()
    if not activities:
        return 0
        
    unique_dates = sorted(list(set([act.activity_date for act in activities])), reverse=True)
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # If the user hasn't been active today or yesterday, the streak is broken
    if unique_dates[0] < yesterday:
        return 0
        
    streak = 0
    current_check_date = unique_dates[0]
    
    for act_date in unique_dates:
        if act_date == current_check_date:
            streak += 1
            current_check_date -= timedelta(days=1)
        elif act_date < current_check_date:
            # Gaps in history
            break
            
    return streak

def get_monthly_post_count(user_id):
    """
    Gets the count of posts saved by the user in the current calendar month.
    """
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = Content.query.filter(
        Content.user_id == user_id,
        Content.created_at >= start_of_month
    ).count()
    return count

def log_activity(user_id):
    """
    Logs today's activity if it hasn't been logged yet.
    """
    today = date.today()
    existing = Activity.query.filter_by(user_id=user_id, activity_date=today).first()
    if not existing:
        new_activity = Activity(user_id=user_id, activity_date=today)
        db.session.add(new_activity)
        db.session.commit()

def get_weekly_post_count(user_id):
    """
    Gets the count of posts saved by the user in the current calendar week starting Monday.
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_datetime = datetime.combine(start_of_week, datetime.min.time())
    count = Content.query.filter(
        Content.user_id == user_id,
        Content.created_at >= start_datetime
    ).count()
    return count

def generate_insights_and_reminders(goal_obj, weekly_posts, streak):
    reminders = []
    insights = []
    
    # 1. Weekly Target Commitment Reminder
    target = goal_obj.weekly_commitment or 3
    if weekly_posts >= target:
        reminders.append(f"🎉 Goal Achieved! You have published {weekly_posts} posts this week, meeting your weekly target of {target}. Keep it up!")
    else:
        diff = target - weekly_posts
        reminders.append(f"📈 Consistency Check: You've created {weekly_posts} of your target {target} posts this week. Draft {diff} more to keep your promise!")
        
    # 2. Streak reminder
    if streak == 0:
        reminders.append("🔥 Wake up call: Your streak is currently at 0. Start a fresh thread or LinkedIn post draft to rebuild momentum!")
    elif streak > 0:
        insights.append(f"🔥 Active Streak: Your {streak}-day active streak shows excellent commitment. Compounding consistency is the secret to brand reach.")

    # 3. Audience/Goal strategy insights
    goal_str = goal_obj.goal
    audience_str = goal_obj.target_audience or "your audience"
    creator_type_str = goal_obj.creator_type or "creator"
    niche_words = [n.strip() for n in goal_obj.niche.split(",")]
    primary_niche = niche_words[0] if niche_words else "your niche"
    
    if "Job" in goal_str:
        insights.append(f"💡 Recruiter Tip: Recruiters looking for a {creator_type_str} value hands-on proof. Write a post summarizing a recent project challenge and how you solved it.")
        insights.append(f"🎯 Audience Alignment: Since you target '{audience_str}', focus on educational content showcasing technical proficiency in '{primary_niche}'.")
    elif "Brand" in goal_str:
        insights.append(f"💡 Thought Leadership: Post a counter-intuitive opinion or a lesson learned from failure in '{primary_niche}' to initiate discussion.")
        insights.append(f"🎯 Network Tip: To build authority with '{audience_str}', comment on 3 major industry players' posts before you publish your draft.")
    elif "Followers" in goal_str:
        insights.append(f"💡 Scale Advice: X threads or Instagram visuals detailing tools or step-by-step guides receive 3x more bookmark saves and shares.")
        insights.append(f"🎯 Growth Angle: Make your CTAs conversational to encourage '{audience_str}' to leave comments and boost algorithm favorability.")
    elif "Startup" in goal_str:
        insights.append(f"💡 Build in Public: Share growth statistics, feature rollouts, or design decisions for your startup. Transparency builds direct user trust.")
        insights.append(f"🎯 Conversion Focus: In your post drafts, use storytelling to highlight a problem your target audience ('{audience_str}') experiences, then introduce your product as the solution.")
        
    return reminders, insights

@dashboard.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    if current_user.goal:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        goal_val = request.form.get('goal')
        creator_type_val = request.form.get('creator_type')
        target_audience_val = request.form.get('target_audience')
        weekly_commitment_val = int(request.form.get('weekly_commitment', 3))
        niche_list = request.form.getlist('niche')  # checkboxes
        custom_niche = request.form.get('custom_niche', '').strip()
        niche_details_val = request.form.get('niche_details', '').strip()
        platform_val = request.form.get('platform')
        tone_val = request.form.get('tone')
        
        # Merge niches
        all_niches = [n for n in niche_list if n]
        if custom_niche:
            all_niches.extend([c.strip() for c in custom_niche.split(',') if c.strip()])
            
        niche_str = ", ".join(all_niches)
        
        if not goal_val or not niche_str or not platform_val or not tone_val or not creator_type_val or not target_audience_val:
            flash('Please answer all questions to build your workspace.', 'warning')
            return redirect(url_for('dashboard.onboarding'))
            
        new_goal = Goal(
            user_id=current_user.id,
            goal=goal_val,
            niche=niche_str,
            platform=platform_val,
            tone=tone_val,
            creator_type=creator_type_val,
            target_audience=target_audience_val,
            weekly_commitment=weekly_commitment_val,
            niche_details=niche_details_val
        )
        
        db.session.add(new_goal)
        log_activity(current_user.id) # Log onboarding as activity
        db.session.commit()
        
        flash('Welcome to CreatorOS! Your personalized canvas is ready.', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('dashboard/onboarding.html')

@dashboard.route('/dashboard')
@login_required
def index():
    if not current_user.goal:
        return redirect(url_for('dashboard.onboarding'))
        
    # Log today's active visit
    log_activity(current_user.id)
    
    # Calculate Streak & Consistency stats
    streak = calculate_streak(current_user.id)
    monthly_posts = get_monthly_post_count(current_user.id)
    weekly_posts = get_weekly_post_count(current_user.id)
    
    # Get last activity date text
    last_activity_text = "Never"
    last_act = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.activity_date.desc()).first()
    if last_act:
        if last_act.activity_date == date.today():
            last_activity_text = "Today"
        elif last_act.activity_date == date.today() - timedelta(days=1):
            last_activity_text = "Yesterday"
        else:
            last_activity_text = last_act.activity_date.strftime('%B %d, %Y')
            
    # Fetch trending items & today's opportunity
    user_goal = current_user.goal
    todays_opp = get_todays_opportunity(user_goal.goal, user_goal.niche)
    alerts = get_opportunity_alerts(user_goal.goal, user_goal.niche)
    
    # Fetch saved drafts
    saved_drafts = Content.query.filter_by(user_id=current_user.id).order_by(Content.created_at.desc()).limit(5).all()
    
    # Generate personalized insights and reminders
    reminders, insights = generate_insights_and_reminders(user_goal, weekly_posts, streak)
    
    return render_template(
        'dashboard/index.html',
        goal=user_goal,
        streak=streak,
        monthly_posts=monthly_posts,
        weekly_posts=weekly_posts,
        last_activity=last_activity_text,
        opportunity=todays_opp,
        alerts=alerts,
        drafts=saved_drafts,
        reminders=reminders,
        insights=insights
    )

@dashboard.route('/refresh-opportunities', methods=['POST'])
@login_required
def refresh_opportunities():
    user_goal = current_user.goal
    if not user_goal:
        return jsonify({"success": False, "error": "No goal configured."}), 400
        
    refreshed = refresh_niche_opportunities(
        goal=user_goal.goal,
        niche_str=user_goal.niche,
        creator_type=user_goal.creator_type,
        target_audience=user_goal.target_audience
    )
    
    return jsonify({
        "success": True,
        "alerts": refreshed
    })

@dashboard.route('/calendar')
@login_required
def calendar():
    import calendar
    import json
    
    if not current_user.goal:
        return redirect(url_for('dashboard.onboarding'))
        
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # Validate month/year bounds
    if month < 1 or month > 12:
        month = today.month
    if year < 2000 or year > 2100:
        year = today.year
        
    # Get standard calendar grid
    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_days = cal.monthdayscalendar(year, month)
    
    # Retrieve scheduled drafts for this month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
        
    scheduled_drafts = Content.query.filter(
        Content.user_id == current_user.id,
        Content.scheduled_date >= start_date,
        Content.scheduled_date < end_date
    ).all()
    
    # Retrieve all unscheduled drafts
    unscheduled_drafts = Content.query.filter(
        Content.user_id == current_user.id,
        Content.scheduled_date.is_(None)
    ).all()
    
    # Group scheduled drafts by day
    scheduled_by_day = {}
    for d in scheduled_drafts:
        day = d.scheduled_date.day
        if day not in scheduled_by_day:
            scheduled_by_day[day] = []
        try:
            parsed = json.loads(d.content)
        except Exception:
            parsed = {"body": d.content}
        scheduled_by_day[day].append({
            "id": d.id,
            "topic": d.topic,
            "platform": d.platform,
            "parsed_content": parsed
        })
        
    # Parse unscheduled drafts
    unscheduled_list = []
    for d in unscheduled_drafts:
        try:
            parsed = json.loads(d.content)
        except Exception:
            parsed = {"body": d.content}
        unscheduled_list.append({
            "id": d.id,
            "topic": d.topic,
            "platform": d.platform,
            "parsed_content": parsed
        })
        
    # Prev/Next navigation
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
        
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
        
    month_name = calendar.month_name[month]
    
    return render_template(
        'dashboard/calendar.html',
        year=year,
        month=month,
        month_days=month_days,
        scheduled_by_day=scheduled_by_day,
        unscheduled_drafts=unscheduled_list,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        month_name=month_name,
        today=today
    )

@dashboard.route('/schedule-post', methods=['POST'])
@login_required
def schedule_post():
    post_id = request.form.get('post_id', type=int)
    date_str = request.form.get('date')
    
    if not post_id or not date_str:
        return jsonify({"success": False, "error": "Missing post ID or date."}), 400
        
    try:
        scheduled_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."}), 400
        
    draft = Content.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not draft:
        return jsonify({"success": False, "error": "Draft not found or unauthorized."}), 404
        
    draft.scheduled_date = scheduled_date
    db.session.commit()
    
    return jsonify({"success": True, "message": "Draft scheduled successfully."})

@dashboard.route('/unschedule-post', methods=['POST'])
@login_required
def unschedule_post():
    post_id = request.form.get('post_id', type=int)
    
    if not post_id:
        return jsonify({"success": False, "error": "Missing post ID."}), 400
        
    draft = Content.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not draft:
        return jsonify({"success": False, "error": "Draft not found or unauthorized."}), 404
        
    draft.scheduled_date = None
    db.session.commit()
    
    return jsonify({"success": True, "message": "Draft unscheduled successfully."})

@dashboard.route('/chat', methods=['POST'])
@login_required
def chat():
    import requests
    from app.services import groq_service
    
    # Accept JSON or form data
    user_msg = None
    if request.is_json:
        user_msg = request.json.get('message')
    else:
        user_msg = request.form.get('message')
        
    if not user_msg:
        return jsonify({"success": False, "error": "Missing message content."}), 400
        
    goal_info = ""
    if current_user.goal:
        goal_info = (
            f"User Profile context:\n"
            f"- Name: {current_user.name}\n"
            f"- Goal: {current_user.goal.goal}\n"
            f"- Niche: {current_user.goal.niche}\n"
            f"- Preferred Platform: {current_user.goal.platform}\n"
            f"- Writing Tone: {current_user.goal.tone}\n"
            f"- Creator Type: {current_user.goal.creator_type or 'General'}\n"
            f"- Target Audience: {current_user.goal.target_audience or 'General'}\n"
        )
        
    # Build personalized system prompt
    system_prompt = (
        "You are CreatorOS Co-Pilot, the friendly, intelligent AI assistant built into the CreatorOS Workspace.\n"
        "CreatorOS is an AI-powered personal brand companion designed to help creators, students, professionals, and entrepreneurs maintain post consistency and grow their brand.\n"
        "Here is the core information about CreatorOS features and how users can navigate them:\n"
        "1. Onboarding: Configures the user's goal, niche, preferred platforms (LinkedIn, X, Instagram, Blog), tone (Casual, Storytelling, Professional, Educational), and commitment frequency.\n"
        "2. Dashboard (Index): Tracks streaks (compounding active days), monthly/weekly post counts, targets, personalized strategy insights, and daily opportunities.\n"
        "3. AI Content Generator: Transforms topics and trend opportunities into platform-specific drafts. It features Canvas Co-Pilot refinement (to make text punchier/shorter/etc.), an Impression Forecaster (scoring drafts 0-100 against hook length, paragraph spacing, clichés, CTA, and value lists), and a High-Fidelity Feed Preview Simulator for LinkedIn, X (Twitter), Instagram, and Blog.\n"
        "4. Content Calendar: A visual monthly grid showing scheduled and unscheduled drafts. Allows HTML5 drag-and-drop to schedule, reschedule, or unschedule posts. Clicking drafts opens preview modals.\n"
        "5. Saved Drafts: Historical library where users can find, copy, edit, or delete saved drafts.\n"
        "6. Settings: Allows users to update goals, niche topics, commitments, creator type, and custom details.\n\n"
        f"{goal_info}\n"
        "Answer the user's questions in a warm, helpful, conversational, and direct manner. You can reference specific pages (like dashboard, content generator, content calendar, saved drafts, settings) or guide them step-by-step. Keep responses concise, clear, and action-oriented. Never break character."
    )
    
    headers = groq_service.get_groq_client_headers()
    reply = None
    
    if headers:
        try:
            payload = {
                "model": groq_service.DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.7
            }
            response = requests.post(groq_service.GROQ_API_URL, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Chat API call failed: {e}")
            
    if not reply:
        # Local fallback replies
        msg_lower = user_msg.lower()
        if "calendar" in msg_lower or "schedule" in msg_lower:
            reply = f"Hi {current_user.name}! You can schedule posts by going to the Content Calendar page. Drag unscheduled cards from the drawer onto calendar cells, or move tags between days. To unschedule, drag the tag back to the drawer area or click the 'x'."
        elif "generator" in msg_lower or "create" in msg_lower or "write" in msg_lower:
            reply = f"Go to the AI Content Generator. Enter a topic, configure the platform and tone, and click Generate. You can then refine the text using Co-Pilot or toggle Feed Previews."
        elif "saved" in msg_lower or "draft" in msg_lower:
            reply = "All saved posts are cataloged in your Saved Drafts library. You can copy text, view feed simulations, or delete posts from there."
        else:
            reply = f"Hello {current_user.name}! I am the CreatorOS Co-Pilot. You can navigate CreatorOS using the sidebar: go to the Dashboard to review active streaks, Content Generator to draft posts, Content Calendar to schedule content via drag-and-drop, and Settings to change niches. Let me know if you need help with a specific tool!"
            
    return jsonify({"success": True, "reply": reply})


