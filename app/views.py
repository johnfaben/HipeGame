import string
from random import choice

from app import app, db, lm
from flask import render_template, flash, redirect, session, url_for, request, g
from .forms import EditForm, AnswerForm
from flask_login import login_user, logout_user, current_user, login_required
from .models import User, Hipe, Answer, random_hipe
from datetime import datetime
from config import POSTS_PER_PAGE
from app.oauth import OAuthSignIn
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.email import follower_notification, send_magic_link


def _guest_has_solved(hipe):
    """Check if the current guest (not logged in) has solved a hipe via session."""
    return hipe.id in session.get('solved_hipes', [])


def _guest_solve(hipe):
    """Record a hipe as solved in the guest's session."""
    solved = session.get('solved_hipes', [])
    if hipe.id not in solved:
        solved.append(hipe.id)
        session['solved_hipes'] = solved


def _mark_solved(hipe):
    """Mark a hipe as solved for the current user (DB) or guest (session)."""
    if g.user.is_authenticated:
        if hipe not in g.user.solved:
            db.session.add(g.user.solve(hipe))
            db.session.commit()
    else:
        _guest_solve(hipe)


def _transfer_guest_progress(user):
    """Transfer guest solved hipes from session to user account."""
    guest_solved = session.pop('solved_hipes', [])
    if guest_solved:
        for hipe_id in guest_solved:
            hipe = Hipe.query.get(hipe_id)
            if hipe and not user.has_solved(hipe):
                user.solve(hipe)
        db.session.commit()


def _mask_answer(word, letters):
    """Mask an answer word, showing only the hipe letters and *s for the rest."""
    idx = word.lower().find(letters.lower())
    return '*' * idx + letters.lower() + '*' * (len(word) - idx - len(letters))


def compute_achievements(solved_letters, solved_count, total_hipes):
    """Compute achievement status from solved hipe data.

    Args:
        solved_letters: set of hipe letter-strings the user has solved
        solved_count: number of hipes solved
        total_hipes: total number of hipes available

    Returns:
        list of achievement dicts with keys: name, description, unlocked, progress (optional)
    """
    vowels = set('aeiou')
    all_chars = set()
    starting_chars = set()
    lengths = set()
    has_palindrome = False
    has_all_vowel = False
    for letters in solved_letters:
        low = letters.lower()
        all_chars.update(low)
        if low:
            starting_chars.add(low[0])
        lengths.add(len(low))
        if len(low) >= 2 and low == low[::-1]:
            has_palindrome = True
        if all(c in vowels for c in low):
            has_all_vowel = True

    alphabet = set(string.ascii_lowercase)
    az_count = len(all_chars & alphabet)
    start_count = len(starting_chars & alphabet)

    return [
        {
            'name': 'First Steps',
            'description': 'Solve your first hipe',
            'unlocked': solved_count >= 1,
        },
        {
            'name': 'Double Digits',
            'description': 'Solve 10 hipes',
            'unlocked': solved_count >= 10,
        },
        {
            'name': 'Half Century',
            'description': 'Solve 50 hipes',
            'unlocked': solved_count >= 50,
        },
        {
            'name': 'Century',
            'description': 'Solve 100 hipes',
            'unlocked': solved_count >= 100,
        },
        {
            'name': 'Halfway',
            'description': 'Solve 50% of all hipes',
            'unlocked': total_hipes > 0 and solved_count >= total_hipes / 2,
        },
        {
            'name': 'Completionist',
            'description': 'Solve every hipe',
            'unlocked': total_hipes > 0 and solved_count >= total_hipes,
        },
        {
            'name': 'Alphabet Soup',
            'description': 'Solve hipes containing every letter',
            'unlocked': az_count >= 26,
            'progress': '%d/26' % az_count,
        },
        {
            'name': 'A to Z',
            'description': 'Solve hipes starting with every letter',
            'unlocked': start_count >= 26,
            'progress': '%d/26' % start_count,
        },
        {
            'name': 'Short & Sweet',
            'description': 'Solve a 2-letter hipe',
            'unlocked': 2 in lengths,
        },
        {
            'name': 'Long Haul',
            'description': 'Solve a 4-letter hipe',
            'unlocked': 4 in lengths,
        },
        {
            'name': 'Mirror Mirror',
            'description': 'Solve a palindrome hipe',
            'unlocked': has_palindrome,
        },
        {
            'name': 'Vowel Movement',
            'description': 'Solve an all-vowel hipe',
            'unlocked': has_all_vowel,
        },
    ]


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@app.route('/static')
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
def index(page=1):
    return render_template('index.html',
            title='Home',
            current_page='index')

@app.route('/login')
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html',
            title='Sign In',
            providers=['google'])

@app.route('/logout')
def logout():
    flash('You were successfully logged out.')
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/<username>')
@app.route('/user/<username>/<int:page>')
@login_required
def user(username, page=1):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    hipes = user.solved.paginate(page=page, per_page=50, error_out=False)
    solved_count = user.solved.count()
    total_hipes = Hipe.query.count()
    solved_letters = {h.letters for h in user.solved.all()}
    achievements = compute_achievements(solved_letters, solved_count, total_hipes)
    return render_template('user.html',
            user=user,
            hipes=hipes,
            solved_count=solved_count,
            total_hipes=total_hipes,
            achievements=achievements,
            current_page='user')

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == g.user:
        flash('Stop following yourself!')
        return redirect(url_for('user', username=username))

    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow %s right now. Are you already following them?' % username)
        return redirect(url_for('user', username=username))
    db.session.add(u)
    db.session.commit()
    follower_notification(user, g.user)
    flash('You are now following %s!' % username)
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You cannot unfollow yourself.')
        return redirect(url_for('user', username=username))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow %s right now. Are you sure you are following them?' % username)
        return redirect(url_for('user', username=g.user.username))
    db.session.add(u)
    db.session.commit()
    flash('You are no longer following %s!' % username)
    return redirect(url_for('user', username=username))

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    welcome = request.values.get('welcome') == '1'
    form = EditForm(g.user.display_name)
    if form.validate_on_submit():
        g.user.display_name = form.display_name.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        if welcome:
            flash('Welcome aboard, %s!' % form.display_name.data)
        else:
            flash('Thanks %s, your changes were saved.' % form.display_name.data)
        return redirect(url_for('user', username=g.user.username))
    else:
        form.display_name.data = g.user.display_name
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form, welcome=welcome)

@app.route('/hipe/<letters>', methods=['GET', 'POST'])
def hipe(letters):
    hipe = Hipe.query.filter_by(letters=letters.lower()).first()
    if hipe is None:
        flash('We do not have %s as a HIPE at the moment. <a href="mailto:jdfaben+hipegame@gmail.com?subject=HIPE suggestion: %s">Should we?</a>' % (letters, letters))
        return redirect(url_for('index'))

    form = AnswerForm(hipe)
    # Retrieve any existing hint/giveup state for this puzzle
    hipe_state = session.get('hipe_state', {})
    state = hipe_state.get(letters.lower(), {})
    hint_text = state.get('hint')
    show_giveup = state.get('show_giveup', False)

    if request.method == 'POST':
        action = request.form.get('action', 'submit')

        if action == 'hint':
            answers = hipe.answers.all()
            if answers:
                word = choice(answers).answer
                hint_text = _mask_answer(word, letters.lower())
                state['hint'] = hint_text
                state['show_giveup'] = True
                show_giveup = True
                hipe_state[letters.lower()] = state
                session['hipe_state'] = hipe_state

        elif action == 'giveup':
            # Clean up hint state
            hipe_state.pop(letters.lower(), None)
            session['hipe_state'] = hipe_state
            # Flag this hipe so the answer page lets them through
            gave_up = session.get('gave_up', [])
            if letters.lower() not in gave_up:
                gave_up.append(letters.lower())
                session['gave_up'] = gave_up
            return redirect(url_for('answer', letters=letters))

        else:  # submit
            if form.validate_on_submit():
                newly_solved = g.user.is_authenticated and not g.user.has_solved(hipe)
                if newly_solved:
                    solved_ltrs = {h.letters for h in g.user.solved.all()}
                    count = len(solved_ltrs)
                    total = Hipe.query.count()
                    before = compute_achievements(solved_ltrs, count, total)
                _mark_solved(hipe)
                if newly_solved:
                    solved_ltrs.add(hipe.letters)
                    after = compute_achievements(solved_ltrs, count + 1, total)
                    profile_url = url_for('user', username=g.user.username)
                    for b, a in zip(before, after):
                        if not b['unlocked'] and a['unlocked']:
                            flash('Achievement unlocked: %s! <a href="%s">View profile</a>' % (a['name'], profile_url))
                hipe_state.pop(letters.lower(), None)
                session['hipe_state'] = hipe_state
                return redirect(url_for('answer', letters=letters, solved=1))
            # Wrong answer — show give up button
            state['show_giveup'] = True
            show_giveup = True
            hipe_state[letters.lower()] = state
            session['hipe_state'] = hipe_state

    return render_template('hipe.html',
            form=form,
            hipe=hipe,
            hint_text=hint_text,
            show_giveup=show_giveup)

@app.route('/answer/<letters>', methods=['GET', 'POST'])
def answer(letters):
    hipe = Hipe.query.filter_by(letters=letters.lower()).first()
    if hipe is None:
        flash('We do not have %s as a HIPE at the moment. <a href="mailto:jdfaben+hipegame@gmail.com?subject=HIPE suggestion: %s">Should we?</a>' % (letters, letters))
        return redirect(url_for('index'))
    gave_up = letters.lower() in session.get('gave_up', [])
    if not gave_up:
        if g.user.is_authenticated:
            if not g.user.has_solved(hipe):
                flash('You have not solved that HIPE yet. No peeking!')
                return redirect(url_for('hipe', letters=letters))
        else:
            if not _guest_has_solved(hipe):
                flash('You have not solved that HIPE yet. No peeking!')
                return redirect(url_for('hipe', letters=letters))
    answers = Answer.query.filter_by(hipe_id=hipe.id)
    return render_template('answer.html',
            hipe=hipe,
            answers=answers)

@app.route('/random')
def random():
    total_hipes = Hipe.query.count()
    if g.user.is_authenticated:
        if g.user.solved.count() >= total_hipes:
            flash('You have solved all our HIPEs, well done!')
            return redirect(url_for('user', username=g.user.username))
        hipe = random_hipe()
        while g.user.has_solved(hipe):
            hipe = random_hipe()
    else:
        solved_ids = session.get('solved_hipes', [])
        if len(solved_ids) >= total_hipes:
            flash('You have solved all our HIPEs, well done!')
            return redirect(url_for('index'))
        hipe = random_hipe()
        while hipe.id in solved_ids:
            hipe = random_hipe()
    return redirect(url_for('hipe', letters=hipe.letters))

@app.route('/magic-link', methods=['POST'])
def magic_link_request():
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    email = request.form.get('email', '').strip().lower()
    if email:
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        token = s.dumps(email, salt='magic-link')
        send_magic_link(email, token)
    flash('Check your inbox! We\'ve sent a login link to %s.' % email)
    return redirect(url_for('login'))


@app.route('/magic-link/<token>')
def magic_link_verify(token):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='magic-link', max_age=900)  # 15 minutes
    except (SignatureExpired, BadSignature):
        flash('That login link is invalid or has expired. Please request a new one.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=email).first()
    is_new = user is None
    if is_new:
        username = email.split('@')[0]
        unique_username = User.make_unique_username(username)
        user = User(username=unique_username, email=email, display_name=unique_username)
        db.session.add(user)
        db.session.commit()
    _transfer_guest_progress(user)
    login_user(user, True)
    if is_new:
        return redirect(url_for('edit', welcome=1))
    flash('You\'re logged in!')
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    username, email, display_name = oauth.callback()
    if email is None and username is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(email=email).first()
    is_new = user is None
    if is_new:
        unique_username = User.make_unique_username(username)
        user = User(username=unique_username, email=email, display_name=display_name)
        db.session.add(user)
        db.session.commit()
    _transfer_guest_progress(user)
    login_user(user, True)
    if is_new:
        return redirect(url_for('edit', welcome=1))
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
