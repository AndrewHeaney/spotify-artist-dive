import os
from flask import Flask, session, request, redirect
from flask_session import Session
from flask import render_template
import spotipy
import uuid
from dataclasses import dataclass

dir = os.getcwd()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(dir, '/tmp/.flask_session/')
Session(app)

caches_folder = os.path.join(dir, '/tmp/.spotify_caches/')
if not os.path.exists(caches_folder):
  os.makedirs(caches_folder)

def session_cache_path():
  return caches_folder + session.get('uuid')
  
# Any classes needed for representing data here:
@dataclass
class Artist:
  name: str
  artist_id: str
  artist_image_url: str

@app.route('/')
def index():
  if not session.get('uuid'):
    # Step 1. Visitor is unknown, give random ID
    session['uuid'] = str(uuid.uuid4())

  cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
  auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-follow-read',
                        cache_handler=cache_handler, 
                        show_dialog=True)

  if request.args.get("code"):
    # Step 3. Being redirected from Spotify auth page
    auth_manager.get_access_token(request.args.get("code"))
    return redirect('/')

  if not auth_manager.validate_token(cache_handler.get_cached_token()):
    auth_url = auth_manager.get_authorize_url()
    # return f'<h2><a href="{auth_url}">Sign in</a></h2>'
    return render_template('index.html', auth_url=auth_url)

  # Step 4. Signed in, display data
  spotify = spotipy.Spotify(auth_manager=auth_manager)
  # return f'<h2>Hi {spotify.me()["display_name"]}, ' \
  #      f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
  #      f'<a href="/following">Following</a> | ' \
  # should redirect to /following here
  # return render_template('explore.html')
  return redirect("/following", code=302)

@app.route('/sign_out')
def sign_out():
  try:
    # Remove the CACHE file (.cache-test) so that a new user can authorize.
    os.remove(session_cache_path())
    session.clear()
  except OSError as e:
    print ("Error: %s - %s." % (e.filename, e.strerror))
  return redirect('/')

def get_user_followed_artists(response):
  artist_info = []
  response_data = {}

  for _, item in enumerate(response['artists']['items']):
    artist_name = item['name']
    artist_id = item['uri']
    artist_image_url = item['images'][1]['url']

    artist = Artist(artist_name, artist_id, artist_image_url)
    artist_info.append(artist)
  response_data['data'] = artist_info
  return response_data
    
@app.route('/following')
def current_user():
  cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
  auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
  if not auth_manager.validate_token(cache_handler.get_cached_token()):
    return redirect('/')
  spotify = spotipy.Spotify(auth_manager=auth_manager)
  response = spotify.current_user_followed_artists()
  # return get_user_followed_artists(response)
  data = get_user_followed_artists(response)

  return render_template(
    'artists.html',
    data=data,
    length=len(data['data'])
  )

@app.route('/recommended-artists', )
def recommended_artists():
  original_artist_id = request.args.get('artistID')
  original_artist_name = request.args.get('artistName')

  cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
  auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
  if not auth_manager.validate_token(cache_handler.get_cached_token()):
    return redirect('/')
  spotify = spotipy.Spotify(auth_manager=auth_manager)

  artist_recommended = []

  data = spotify.recommendations([original_artist_id], None, None, 5)
  for id, track in enumerate(data['tracks']):
    artist = track['album']['artists'][0]

    artist_name = artist['name']
    artist_id = artist['id']
    artist_image_url = track['album']['images'][1]['url']

    artist = Artist(artist_name, artist_id, artist_image_url)
    artist_recommended.append(artist)

  # return {'data': artist_recommended}
  return render_template(
    'explore.html',
    data=artist_recommended,
    artist_name=original_artist_name,
    length=len(artist_recommended)
  )
  
if __name__ == '__main__':
  app.run(threaded=True, port=int(
      os.environ.get("PORT",
      os.environ.get("SPOTIPY_REDIRECT_URI", 8000).split(":")[-1])
    )
  )