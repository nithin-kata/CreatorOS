from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Goal
from app.dashboard.routes import log_activity

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    if not current_user.goal:
        return redirect(url_for('dashboard.onboarding'))
        
    user_goal = current_user.goal
    
    if request.method == 'POST':
        goal_val = request.form.get('goal')
        creator_type_val = request.form.get('creator_type')
        target_audience_val = request.form.get('target_audience')
        weekly_commitment_val = int(request.form.get('weekly_commitment', 3))
        niche_val = request.form.get('niche')
        niche_details_val = request.form.get('niche_details', '').strip()
        platform_val = request.form.get('platform')
        tone_val = request.form.get('tone')
        
        if not goal_val or not niche_val or not platform_val or not tone_val or not creator_type_val or not target_audience_val:
            flash('All settings fields are required.', 'warning')
            return redirect(url_for('settings.index'))
            
        user_goal.goal = goal_val
        user_goal.creator_type = creator_type_val
        user_goal.target_audience = target_audience_val
        user_goal.weekly_commitment = weekly_commitment_val
        user_goal.niche = niche_val
        user_goal.niche_details = niche_details_val
        user_goal.platform = platform_val
        user_goal.tone = tone_val
        
        log_activity(current_user.id)
        db.session.commit()
        
        flash('Workspace settings updated successfully.', 'success')
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', goal=user_goal)
