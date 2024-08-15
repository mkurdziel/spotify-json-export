import os
import json
import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def prune_available_markets(item):
    """Recursively remove 'available_markets' from a dictionary or list."""
    if isinstance(item, dict):
        item.pop('available_markets', None)
        for key, value in item.items():
            prune_available_markets(value)
    elif isinstance(item, list):
        for i in item:
            prune_available_markets(i)

def save_json(data, path):
    prune_available_markets(data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Saved to {path}")

def export_playlists(sp, output_dir):
    playlists_dir = os.path.join(output_dir, 'playlists')
    os.makedirs(playlists_dir, exist_ok=True)

    # Get all playlists for the current user
    playlists = sp.user_playlists(sp.current_user()['id'])

    # Export each playlist to a JSON file
    for playlist in playlists['items']:
        playlist_id = playlist['id']
        playlist_name = playlist['name']

        # Fetch playlist tracks
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']

        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        # Prepare data for JSON
        playlist_data = {
            'name': playlist_name,
            'description': playlist.get('description'),
            'tracks': [
                {
                    'name': item['track']['name'],
                    'artist': item['track']['artists'][0]['name'] if item['track']['artists'] else 'Unknown',
                    'album': item['track']['album']['name'] if item['track']['album'] else 'Unknown',
                    'track_id': item['track']['id'],
                    'uri': item['track']['uri'],
                    'is_playable': item['track'].get('is_playable', False)
                } for item in tracks if item['track']
            ]
        }

        # Save the playlist to a JSON file
        file_name = f"{playlist_name.replace('/', '_').replace(' ', '_')}.json"
        save_json(playlist_data, os.path.join(playlists_dir, file_name))

    # Export Liked Songs as a special playlist
    export_liked_songs(sp, playlists_dir)

def export_liked_songs(sp, playlists_dir):
    # Fetch saved tracks (Liked Songs)
    results = sp.current_user_saved_tracks()
    tracks = results['items']

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Prepare data for JSON
    liked_songs_data = {
        'name': 'Liked Songs',
        'tracks': [
            {
                'name': item['track']['name'],
                'artist': item['track']['artists'][0]['name'] if item['track']['artists'] else 'Unknown',
                'album': item['track']['album']['name'] if item['track']['album'] else 'Unknown',
                'track_id': item['track']['id'],
                'uri': item['track']['uri'],
                'is_playable': item['track'].get('is_playable', False)
            } for item in tracks if item['track']
        ]
    }

    # Save the liked songs to a JSON file
    save_json(liked_songs_data, os.path.join(playlists_dir, "liked_songs.json"))

def export_top_items(sp, output_dir):
    top_dir = os.path.join(output_dir, 'top')
    os.makedirs(top_dir, exist_ok=True)

    # Export top artists
    top_artists = sp.current_user_top_artists(limit=50)
    save_json(top_artists['items'], os.path.join(top_dir, 'top_artists.json'))

    # Export top tracks
    top_tracks = sp.current_user_top_tracks(limit=50)
    save_json(top_tracks['items'], os.path.join(top_dir, 'top_tracks.json'))

def export_saved_items(sp, output_dir):
    # Albums
    albums_dir = os.path.join(output_dir, 'albums')
    os.makedirs(albums_dir, exist_ok=True)
    saved_albums = sp.current_user_saved_albums()
    save_json([album['album'] for album in saved_albums['items']], os.path.join(albums_dir, 'saved_albums.json'))

    # Shows
    shows_dir = os.path.join(output_dir, 'shows')
    os.makedirs(shows_dir, exist_ok=True)
    saved_shows = sp.current_user_saved_shows()
    save_json([show['show'] for show in saved_shows['items']], os.path.join(shows_dir, 'saved_shows.json'))

    # Episodes
    episodes_dir = os.path.join(output_dir, 'episodes')
    os.makedirs(episodes_dir, exist_ok=True)
    saved_episodes = sp.current_user_saved_episodes()
    save_json([episode['episode'] for episode in saved_episodes['items']], os.path.join(episodes_dir, 'saved_episodes.json'))

def export_followed(sp, output_dir):
    followed_dir = os.path.join(output_dir, 'followed')
    os.makedirs(followed_dir, exist_ok=True)

    # Followed artists
    followed_artists = sp.current_user_followed_artists(limit=50)['artists']['items']
    save_json(followed_artists, os.path.join(followed_dir, 'followed_artists.json'))

    # Followed podcasts
    followed_podcasts = sp.current_user_saved_shows()['items']
    save_json([show['show'] for show in followed_podcasts], os.path.join(followed_dir, 'followed_podcasts.json'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export Spotify data to JSON files.')
    parser.add_argument('--client_id', help='Your Spotify Client ID')
    parser.add_argument('--client_secret', help='Your Spotify Client Secret')
    parser.add_argument('--redirect_uri', help='Your Spotify Redirect URI')
    parser.add_argument('--output_dir', help='Directory to save the exported data')

    args = parser.parse_args()

    client_id = args.client_id or os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = args.client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = args.redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI')
    output_dir = args.output_dir or os.getenv('SPOTIFY_OUTPUT_DIR')

    if not client_id or not client_secret or not redirect_uri or not output_dir:
        raise ValueError("You must provide all required credentials and the output directory either as arguments or environment variables.")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=redirect_uri,
                                                   scope='playlist-read-private user-library-read user-top-read user-follow-read'))

    export_playlists(sp, output_dir)
    export_top_items(sp, output_dir)
    export_saved_items(sp, output_dir)
    export_followed(sp, output_dir)
