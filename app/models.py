"""Database models.

Authentication is backed by a real ``User`` table with salted/hashed
passwords (via Werkzeug's ``generate_password_hash`` / ``check_password_hash``
- never plaintext). The marketplace data (editor listings, orders, payments,
saved editors, chat messages) is also modeled properly instead of being
hardcoded in the templates, so the dashboard pages read from the database.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """A REELO account. A user is either a content creator or a video editor."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="creator")  # 'creator' or 'editor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Profile fields
    bio = db.Column(db.String(280))
    location = db.Column(db.String(120))
    avatar_url = db.Column(db.String(500))
    website = db.Column(db.String(255))

    # Editor-specific fields (only relevant when role == 'editor')
    editing_style = db.Column(db.String(120))
    price_per_short = db.Column(db.Integer)
    delivery_time = db.Column(db.String(60))
    categories = db.Column(db.String(255))  # comma separated tags used for search/filter
    rating = db.Column(db.Float, default=5.0)
    reviews_count = db.Column(db.Integer, default=0)

    samples = db.relationship("VideoSample", backref="editor", lazy="dynamic",
                               cascade="all, delete-orphan")
    orders_as_creator = db.relationship("Order", foreign_keys="Order.creator_id",
                                         backref="creator", lazy="dynamic")
    orders_as_editor = db.relationship("Order", foreign_keys="Order.editor_id",
                                        backref="editor", lazy="dynamic")

    # -- password helpers -------------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def is_editor(self) -> bool:
        return self.role == "editor"

    def category_list(self):
        return [c.strip() for c in (self.categories or "").split(",") if c.strip()]

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class VideoSample(db.Model):
    """A work-sample thumbnail/video an editor shows on their listing card."""

    __tablename__ = "video_samples"

    id = db.Column(db.Integer, primary_key=True)
    editor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=False)
    views = db.Column(db.String(20))
    likes = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SavedEditor(db.Model):
    """A creator bookmarking an editor for quick hiring later."""

    __tablename__ = "saved_editors"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[creator_id])
    saved_editor = db.relationship("User", foreign_keys=[editor_id])

    __table_args__ = (db.UniqueConstraint("creator_id", "editor_id", name="uq_saved_editor"),)


class Order(db.Model):
    """A hire contract between a creator and an editor for N short videos."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    instructions = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="deposit_held")  # deposit_held / in_review / completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment = db.relationship("Payment", backref="order", uselist=False,
                               cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return self.quantity * self.unit_price


class Payment(db.Model):
    """A payment record tied 1:1 to an order."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    txn_reference = db.Column(db.String(40), unique=True, nullable=False)
    method = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="deposit_held")  # deposit_held / paid_to_editor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    """A single chat message between a creator and an editor."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])
