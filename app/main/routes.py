import random
import string
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.main import main_bp
from app.models import Message, Order, Payment, SavedEditor, User, VideoSample

CATEGORY_CHOICES = [
    ("All", "All Types"),
    ("Talking Head", "Talking Head / Podcast"),
    ("Cinematic", "Cinematic Reels"),
    ("Gaming", "Gaming Shorts"),
    ("Anime", "Anime / AMV"),
    ("Motion Graphics", "Motion Graphics"),
    ("Vlogs", "Vlogs & Travel"),
]


def _generate_txn_reference() -> str:
    return "TXN-" + "".join(random.choices(string.digits, k=4))


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    query = User.query.filter_by(role="editor")

    category = request.args.get("category", "All")
    if category and category != "All":
        query = query.filter(User.categories.ilike(f"%{category}%"))

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.name.ilike(like), User.editing_style.ilike(like),
                                     User.categories.ilike(like)))

    sort = request.args.get("sort", "rating")
    if sort == "price":
        query = query.order_by(User.price_per_short.asc())
    else:
        query = query.order_by(User.rating.desc())

    editors = query.all()
    saved_ids = set()
    if current_user.role == "creator":
        saved_ids = {s.editor_id for s in SavedEditor.query.filter_by(creator_id=current_user.id)}

    return render_template(
        "main/dashboard.html",
        editors=editors,
        categories=CATEGORY_CHOICES,
        active_category=category,
        search=search,
        saved_ids=saved_ids,
    )


@main_bp.route("/profile")
@login_required
def profile():
    if current_user.role == "editor":
        samples = current_user.samples.order_by(VideoSample.created_at.desc()).all()
        return render_template("main/profile.html", samples=samples)

    projects_posted = current_user.orders_as_creator.count()
    editors_hired = (
        db.session.query(Order.editor_id)
        .filter_by(creator_id=current_user.id)
        .distinct()
        .count()
    )
    total_spent = (
        db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.creator_id == current_user.id)
        .scalar()
    )
    return render_template(
        "main/profile.html",
        projects_posted=projects_posted,
        editors_hired=editors_hired,
        total_spent=total_spent,
    )


@main_bp.route("/projects")
@login_required
def projects():
    if current_user.role == "editor":
        orders = current_user.orders_as_editor.order_by(Order.created_at.desc()).all()
    else:
        orders = current_user.orders_as_creator.order_by(Order.created_at.desc()).all()
    return render_template("main/projects.html", orders=orders)


@main_bp.route("/payments")
@login_required
def payments():
    payments_q = (
        Payment.query.join(Order, Payment.order_id == Order.id)
        .filter(Order.creator_id == current_user.id)
        .order_by(Payment.created_at.desc())
    )
    all_payments = payments_q.all()

    total_spent = sum(p.amount for p in all_payments)
    deposit_held = sum(p.amount for p in all_payments if p.status == "deposit_held")
    paid_out = sum(p.amount for p in all_payments if p.status == "paid_to_editor")

    return render_template(
        "main/payments.html",
        payments=all_payments,
        total_spent=total_spent,
        deposit_held=deposit_held,
        paid_out=paid_out,
    )


@main_bp.route("/saved")
@login_required
def saved():
    saved_rows = SavedEditor.query.filter_by(creator_id=current_user.id).all()
    return render_template("main/saved.html", saved_rows=saved_rows)


@main_bp.route("/save/<int:editor_id>", methods=["POST"])
@login_required
def toggle_save(editor_id):
    existing = SavedEditor.query.filter_by(creator_id=current_user.id, editor_id=editor_id).first()
    if existing:
        db.session.delete(existing)
        flash("Removed from saved editors.", "info")
    else:
        db.session.add(SavedEditor(creator_id=current_user.id, editor_id=editor_id))
        flash("Editor saved for quick hiring.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("main.dashboard"))


@main_bp.route("/messages")
@main_bp.route("/messages/<int:partner_id>")
@login_required
def messages(partner_id=None):
    sent = db.session.query(Message.recipient_id).filter_by(sender_id=current_user.id)
    received = db.session.query(Message.sender_id).filter_by(recipient_id=current_user.id)
    partner_ids = {row[0] for row in sent.union(received).all()}
    partners = User.query.filter(User.id.in_(partner_ids)).all() if partner_ids else []

    active_partner = None
    thread = []
    if partner_id:
        active_partner = db.session.get(User, partner_id)
    elif partners:
        active_partner = partners[0]

    if active_partner:
        thread = (
            Message.query.filter(
                db.or_(
                    db.and_(Message.sender_id == current_user.id, Message.recipient_id == active_partner.id),
                    db.and_(Message.sender_id == active_partner.id, Message.recipient_id == current_user.id),
                )
            )
            .order_by(Message.created_at.asc())
            .all()
        )

    return render_template(
        "main/messages.html", partners=partners, active_partner=active_partner, thread=thread
    )


@main_bp.route("/messages/<int:partner_id>/send", methods=["POST"])
@login_required
def send_message(partner_id):
    body = request.form.get("body", "").strip()
    if body:
        db.session.add(Message(sender_id=current_user.id, recipient_id=partner_id, body=body))
        db.session.commit()
    return redirect(url_for("main.messages", partner_id=partner_id))


@main_bp.route("/editor-studio", methods=["GET", "POST"])
@login_required
def editor_studio():
    if request.method == "POST":
        current_user.role = "editor"
        current_user.name = request.form.get("name", current_user.name).strip()
        current_user.price_per_short = int(request.form.get("price_per_short") or 0)
        current_user.editing_style = request.form.get("editing_style", current_user.editing_style)
        current_user.categories = current_user.editing_style

        sample_link = request.form.get("sample_link", "").strip()
        if sample_link:
            db.session.add(
                VideoSample(
                    editor_id=current_user.id,
                    title=f"{current_user.name} sample",
                    thumbnail_url=sample_link,
                    views="0",
                    likes="0",
                )
            )
        db.session.commit()
        flash("Profile saved successfully!", "success")
        return redirect(url_for("main.editor_studio"))

    return render_template("main/editor_studio.html")


@main_bp.route("/hire/<int:editor_id>", methods=["POST"])
@login_required
def hire(editor_id):
    editor = db.session.get(User, editor_id)
    if editor is None or editor.role != "editor":
        flash("That editor could not be found.", "error")
        return redirect(url_for("main.dashboard"))

    title = request.form.get("title", "Custom Short Order").strip() or "Custom Short Order"
    quantity = max(1, int(request.form.get("quantity") or 1))
    method = request.form.get("payment_method", "UPI / GPay / PhonePe")
    instructions = request.form.get("instructions", "").strip()

    order = Order(
        creator_id=current_user.id,
        editor_id=editor.id,
        title=title,
        instructions=instructions,
        quantity=quantity,
        unit_price=editor.price_per_short or 0,
        status="deposit_held",
    )
    db.session.add(order)
    db.session.flush()  # get order.id before creating the payment

    payment = Payment(
        order_id=order.id,
        txn_reference=_generate_txn_reference(),
        method=method,
        amount=order.total_amount,
        status="deposit_held",
    )
    db.session.add(payment)
    db.session.commit()

    flash(
        f"Successfully hired {editor.name}! \u20b9{order.total_amount:,} kept safe in deposit.",
        "success",
    )
    return redirect(url_for("main.payments"))
