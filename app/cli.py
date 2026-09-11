"""Custom `flask` CLI commands."""

import click

from app.extensions import db
from app.models import Order, Payment, User, VideoSample


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db():
        """Populate the database with demo accounts so the marketplace isn't empty."""
        db.create_all()

        if User.query.first():
            click.echo("Database already has data — skipping seed.")
            return

        alex = User(
            name="Alex Morgan",
            email="alex@reelo.dev",
            role="editor",
            bio="Talking-head edits with punchy captions and sound design.",
            location="Mumbai, India",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80",
            editing_style="Talking Head & Podcast",
            categories="Talking Head, Motion Graphics",
            price_per_short=2500,
            delivery_time="1 Day Delivery",
            rating=4.9,
            reviews_count=42,
        )
        alex.set_password("password123")

        liam = User(
            name="Liam Vance",
            email="liam@reelo.dev",
            role="editor",
            bio="Cinematic reels and gaming highlight edits, fast turnaround.",
            location="Bengaluru, India",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80",
            editing_style="Cinematic Reels & Vlogs",
            categories="Cinematic, Vlogs, Gaming",
            price_per_short=3500,
            delivery_time="12 Hours Delivery",
            rating=5.0,
            reviews_count=78,
        )
        liam.set_password("password123")

        creator = User(
            name="Creator Studio",
            email="creator@reelo.dev",
            role="creator",
            bio="Building high-engagement Instagram Reels & Shorts.",
            location="Pune, India",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
            website="linktr.ee/creatorstudio",
        )
        creator.set_password("password123")

        db.session.add_all([alex, liam, creator])
        db.session.flush()

        db.session.add_all([
            VideoSample(editor_id=alex.id, title="Alex Morgan Sample Video",
                        thumbnail_url="https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=800&q=80",
                        views="124K", likes="12.4K"),
            VideoSample(editor_id=liam.id, title="Liam Vance Sample Video",
                        thumbnail_url="https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80",
                        views="89K", likes="8.1K"),
        ])

        order = Order(
            creator_id=creator.id,
            editor_id=alex.id,
            title="Cricket Viral Short #1",
            instructions="Animated text & sound effects",
            quantity=2,
            unit_price=alex.price_per_short,
            status="deposit_held",
        )
        db.session.add(order)
        db.session.flush()

        db.session.add(Payment(
            order_id=order.id,
            txn_reference="TXN-9402",
            method="UPI / GPay",
            amount=order.total_amount,
            status="deposit_held",
        ))

        db.session.commit()
        click.echo("Seeded database with demo accounts (password: password123).")
