"""Seed the database with HIPE puzzles and their answers from list_of_hipes.txt."""

import os
from app import app, db
from app.models import Hipe, Answer

HIPE_FILE = os.path.join(os.path.dirname(__file__), 'list_of_hipes.txt')

with app.app_context():
    db.create_all()

    with open(HIPE_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            letters = parts[0].strip().lower()
            words = [w.strip().lower() for w in parts[1:] if w.strip()]

            hipe = Hipe.query.filter_by(letters=letters).first()
            if not hipe:
                hipe = Hipe(letters)
                db.session.add(hipe)
                db.session.flush()

            for word in words:
                existing = Answer.query.filter_by(answer=word, hipe_id=hipe.id).first()
                if not existing:
                    answer = Answer(word)
                    answer.hipe_id = hipe.id
                    db.session.add(answer)

    db.session.commit()

    hipe_count = Hipe.query.count()
    answer_count = Answer.query.count()
    print(f'Database seeded: {hipe_count} puzzles, {answer_count} answers.')
