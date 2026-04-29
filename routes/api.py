from flask import jsonify, request

from extensions import db
from models import Beat
from services import beat_to_dict, search_itunes


def register_api_routes(app):
    @app.route('/api/beats')
    def api_beats():
        beats = Beat.query.filter_by(status='approved').order_by(Beat.created_at.desc()).all()
        return jsonify({
            'count': len(beats),
            'items': [beat_to_dict(beat) for beat in beats],
        })

    @app.route('/api/beats/<int:beat_id>')
    def api_beat_detail(beat_id):
        beat = db.session.get(Beat, beat_id)
        if not beat or beat.status != 'approved':
            return jsonify({'error': 'Beat not found'}), 404
        return jsonify(beat_to_dict(beat))

    @app.route('/api/music/search')
    def api_music_search():
        term = request.args.get('term', '').strip()
        if not term:
            return jsonify({'count': 0, 'items': []})

        items = search_itunes(term, limit=6)
        return jsonify({'count': len(items), 'items': items})
