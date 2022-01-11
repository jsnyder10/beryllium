from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, \
    MessageForm
from app.models import User, Post, Message, Notification
from app.translate import translate
from app.main import bp
import os

import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy.ext.automap import automap_base


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


def upload_excel(name):
    path=current_app.config['BASEDIR']
    path=path+'/app/static/upload/'

    df=pd.read_excel(path+name)
    df.to_sql(name,con=db.engine)
    engine.table_names()

    from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
    from sqlalchemy.ext.automap import automap_base
    #engine = create_engine("sqlite:///mydatabase.db")

    metadata = MetaData()
    metadata.reflect(engine, only=['user', 'address'])
    # we can then produce a set of mappings from this MetaData.
    Base = automap_base(metadata=metadata)
    Base.prepare()

    # mapped classes are ready
    User, Address, Order = Base.classes.user, Base.classes.address,\
    Base.classes.user_order

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    path=current_app.config['BASEDIR']
    path=path+'/app/static/upload'
    files=os.listdir(path)
    #Clean Random Files out
    for file in files:
        if "Identifier" in file:
            files.remove(file)
    unuploaded=files
    tables=db.engine.table_names()
    uploaded=[]
    for file in files:
        for table in tables:
            if file==table:
                uploaded.append(file)
    for upload in uploaded:
        for file in files:
            if file==upload:
                unuploaded.remove(file)
    return render_template('upload.html', title=_('Upload'), tables=tables, uploaded=uploaded, unuploaded=unuploaded)

@bp.route('/start_upload', methods=['GET', 'POST'])
@login_required
def start_upload():
    path=current_app.config['BASEDIR']
    path=path+'/app/static/upload/'
    files=os.listdir(path)
    #Clean Random Files out
    for file in files:
        if "Identifier" in file:
            files.remove(file)
    unuploaded=files
    tables=db.engine.table_names()
    uploaded=[]
    for file in files:
        for table in tables:
            if file==table:
                uploaded.append(file)
    for upload in uploaded:
        for file in files:
            if file==upload:
                unuploaded.remove(file)
    for unupload in unuploaded:
        if ".xls" in unupload:
            name=unupload[:-4]
            print(name)
            df=pd.read_excel(path+unupload)
            df.to_sql(name, con=db.engine)
            metadata = MetaData()
            metadata.reflect(db.engine, only=[name])
            Base = automap_base(metadata=metadata)
            Base.prepare()
        elif ".csv" in unuploaded:
            name=unupload[:-4]
            print(name)
            df=pd.read_csv(path+unupload)
            metadata = MetaData()
            metadata.reflect(db.engine, only=[name])
            Base = automap_base(metadata=metadata)
            Base.prepare()
    return render_template('upload.html', title=_('Upload'), tables=tables, uploaded=uploaded, unuploaded=unuploaded)


@bp.route('/data', methods=['GET', 'POST'])
@login_required
def data():
    path=current_app.config['BASEDIR']
    path=path+'/app/static/upload'
    files=os.listdir(path)
    #Clean Random Files out
    for file in files:
        if "Identifier" in file:
            files.remove(file)
    unuploaded=files
    tables=db.engine.table_names()
    uploaded=[]
    for file in files:
        for table in tables:
            if file==table:
                uploaded.append(file)
    for upload in uploaded:
        for file in files:
            if file==upload:
                unuploaded.remove(file)
    tables=[]
    '''
    #Query table/column from mapped
    db.session.query(Base.metadata.tables['1']).filter_by(last_name='Erm').all()
    #Pull column keys from table
    Base.metadata.tables['1'].columns.keys()
    '''
    for table in uploaded:
        metadata = MetaData()
        metadata.reflect(db.engine, only=[table])
        Base = automap_base(metadata=metadata)
        Base.prepare()
        name=table
        columns=Base.metadata.tables[name].columns.keys()
        tables.append({'name': name, 'columns': columns})
    return render_template('data.html', title=_('Data'), tables=tables)



@bp.route('/undersea', methods=['GET', 'POST'])
@login_required
def undersea():
    return render_template('undersea.html', title=_('Undersea'))

@bp.route('/basic', methods=['GET', 'POST'])
@login_required
def basic():
    return render_template('basic.html', title=_('Basic'))

@bp.route('/ark_links', methods=['GET', 'POST'])
@login_required
def ark_links():
    return render_template('ark_links.html', title=_('Ark Links'))


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
