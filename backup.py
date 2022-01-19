import spotipy
from spotipy.oauth2 import SpotifyOAuth
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
  client_id=os.getenv('CLIENT_ID'),
  client_secret=os.getenv('CLIENT_SECRET'),
  redirect_uri=os.getenv('REDIRECT_URI'),
  scope="user-library-read, user-follow-read",
  )
)

results = sp.current_user_followed_artists()
# print(results)

# I want:
# - artistId
# - image url
# - Artist Name
def get_user_artists():
  artist_info = {}

  for idx, item in enumerate(results['artists']['items']):
    artist_name = item['name']
    artist_id = item['uri']
    artist_info[artist_id] = artist_name
    # artist_ids.append(artist_id.split('artist:')[1])

    album_cover_url = item['images'][1]['url']
    # print(idx, ': ',artist_name,',',artist_id,',',album_cover_url, '\n\n')
  return artist_info

def get_recommended_artists():
  artist_ids = get_user_artists()

  response_data = []
  for idx, (artist_id, artist_name) in enumerate(artist_ids.items()):
    artist_recommended = {}
    artist_names = []

    data = sp.recommendations([artist_id], None, None, 5)
    for id, track in enumerate(data['tracks']):
      artist = track['album']['artists'][0]
      artist_names.append(artist['name'])
    artist_recommended[artist_name] = artist_names
    response_data.append(artist_recommended)
  
  return response_data

app = FastAPI()

@app.get("/")
def hello():
    artists = get_recommended_artists()
    return artists

# @app.get('callback')
#   def callback(code):
    
