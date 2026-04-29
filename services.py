import json
import secrets
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from flask import url_for
from werkzeug.utils import secure_filename

from config import ALLOWED_AUDIO, ALLOWED_IMAGES, BASE_DIR, UPLOAD_COVERS, UPLOAD_PREVIEWS
from extensions import db
from models import Beat, User


def allowed_audio(filename):
    return _allowed_file(filename, ALLOWED_AUDIO)


def allowed_image(filename):
    return _allowed_file(filename, ALLOWED_IMAGES)


def _allowed_file(filename, variants):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in variants


def save_uploaded_file(file_obj, upload_dir: Path):
    if not file_obj or not file_obj.filename:
        return None

    filename = secure_filename(file_obj.filename)

    # Если пользователь выбрал файл без расширения или браузер передал пустое имя,
    # файл не сохраняем, чтобы приложение не падало с IndexError.
    if not filename or '.' not in filename:
        return None

    ext = filename.rsplit('.', 1)[1].lower()
    new_name = f'{secrets.token_hex(8)}.{ext}'
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_obj.save(upload_dir / new_name)
    return new_name


def create_default_cover():
    cover_path = BASE_DIR / 'static' / 'default-cover.jpg'
    if cover_path.exists():
        return

    try:
        from PIL import Image

        logo_path = BASE_DIR / 'static' / 'logo.png'
        canvas = Image.new('RGB', (1200, 1200), 'black')

        if logo_path.exists():
            logo = Image.open(logo_path).convert('RGBA')
            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)
            logo.thumbnail((744, 744), Image.LANCZOS)
            layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
            pos = ((canvas.width - logo.width) // 2, (canvas.height - logo.height) // 2)
            layer.alpha_composite(logo, dest=pos)
            canvas = Image.alpha_composite(canvas.convert('RGBA'), layer).convert('RGB')

        canvas.save(cover_path, quality=95)
    except Exception:
        pass


def seed_data():
    create_default_cover()

    if User.query.count() == 0:
        admin = User(username='admin', email='admin@audiowaves.local', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    if Beat.query.count() == 0:
        sample_beats = [
            Beat(
                title='Night Pulse',
                category='Trap',
                mood='Dark',
                bpm=140,
                beat_key='Fm',
                price=2699,
                description='Плотный темный бит с атмосферным синтом.',
                preview_file='sample-preview.mp3',
                cover_file='default-cover.jpg',
                is_featured=True,
            ),
            Beat(
                title='Sky Motion',
                category='Drill',
                mood='Aggressive',
                bpm=145,
                beat_key='Gm',
                price=3599,
                description='Жесткий драйвовый drill c жирным низом.',
                preview_file='sample-preview.mp3',
                cover_file='default-cover.jpg',
                is_featured=True,
            ),
            Beat(
                title='Ocean Glow',
                category='Melodic',
                mood='Dreamy',
                bpm=128,
                beat_key='Am',
                price=2199,
                description='Легкая мелодичная работа для спокойного вайба.',
                preview_file='sample-preview.mp3',
                cover_file='default-cover.jpg',
                is_featured=False,
            ),
        ]
        db.session.add_all(sample_beats)

    sample_preview = UPLOAD_PREVIEWS / 'sample-preview.mp3'
    if not sample_preview.exists():
        sample_preview.write_bytes(b'')

    db.session.commit()


def beat_to_dict(beat):
    cover_filename = f'uploads/covers/{beat.cover_file}' if beat.cover_file != 'default-cover.jpg' else 'default-cover.jpg'
    return {
        'id': beat.id,
        'title': beat.title,
        'category': beat.category,
        'mood': beat.mood,
        'bpm': beat.bpm,
        'beat_key': beat.beat_key,
        'price': beat.price,
        'price_rub': round(beat.price),
        'description': beat.description,
        'preview_url': url_for('static', filename=f'uploads/previews/{beat.preview_file}', _external=False),
        'cover_url': url_for('static', filename=cover_filename, _external=False),
        'is_featured': beat.is_featured,
        'created_at': beat.created_at.isoformat(),
    }


def search_itunes(term, limit=6):
    term = term.strip()
    if not term:
        return []

    params = urlencode({
        'term': term,
        'media': 'music',
        'entity': 'song',
        'country': 'US',
        'limit': limit,
    })
    url = f'https://itunes.apple.com/search?{params}'

    try:
        with urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return []

    results = []
    for item in payload.get('results', []):
        results.append({
            'track_name': item.get('trackName', 'Без названия'),
            'artist_name': item.get('artistName', 'Неизвестный артист'),
            'collection_name': item.get('collectionName', 'Без альбома'),
            'genre': item.get('primaryGenreName', 'Music'),
            'artwork_url': item.get('artworkUrl100', ''),
            'track_url': item.get('trackViewUrl', ''),
            'preview_url': item.get('previewUrl', ''),
        })
    return results
