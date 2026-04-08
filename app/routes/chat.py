from flask import Blueprint, render_template
from flask_login import login_required

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# kesobb lesz a full AI chat implementacio
@chat_bp.route('/')
@login_required
def chat_page():
    return render_template('chat/index.html')
