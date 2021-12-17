import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred
import pprint
import requests
import time
import math

pp = pprint.PrettyPrinter()

#%%
scope = "playlist-read-private playlist-modify-public user-read-private user-top-read user-library-read"
auth_manager=SpotifyOAuth(client_id=cred.client_id, client_secret=cred.client_secret, redirect_uri=cred.redirect_url, scope=scope)
sp = spotipy.Spotify(auth_manager=auth_manager)

user_id = sp.current_user()['id']
user_country = sp.current_user()['country']

#%%

def get_user_playlist_urls():
    playlists_lst =[]
    ids = []
    offset = 0
    while True:
        playlists = sp.current_user_playlists(offset=offset)
        if len(playlists['items']) == 0:
            break
        for playlist in playlists['items']:
            playlists_lst.append(playlist)
        offset = offset + len(playlists['items'])
        time.sleep(0.1) 
    
    for playlist in playlists_lst:
        ids.append(playlist['id'])
    return ids, playlists_lst

def playlist_names(playlists):
    names = []
    for playlist in playlists:
        name = playlist['name']
        names.append(name)
    return names

def song_ids_from_playlists(user, playlist_urls):
    ids = []
    t1 = time.time()
    for i in range(len(playlist_urls)):
        offset = 0
        print(f'I\'m starting playlist number {i+1} out of {len(playlist_urls)}')
        while True:
            track_ids = sp.user_playlist_tracks(user=user, playlist_id=playlist_urls[i], offset=offset, fields ='items.track.id')
            #print(track_ids)
            #print(len(track_ids['items']))
            if len(track_ids['items']) == 0:
                break
            for track in track_ids['items']:
                if track['track'] == None:
                    continue
                else:
                    ids.append(track['track']['id'])
            offset = offset + len(track_ids['items'])
            time.sleep(0.1)
    t2 = time.time()
    print(f'Getting song ids from all those playlists took {t2-t1} seconds!\n')
    return list(set(ids))
    
def recc_id(list_seed_tracks, country):
    print('Starting to collect recommendation ids.')
    if len(list_seed_tracks) > 150:
        print(f'Wow! I have {len(list_seed_tracks)} to make. This may take a while.\n')
    recc_ids = []
    #raw_recs = []
    t1 = time.time()
    for seed in list_seed_tracks:
        seed_to_use = []
        seed_to_use.append(seed)
        recs = sp.recommendations(seed_tracks=seed_to_use, limit=1, country=country)
        #raw_recs.append(recs)
        #print(recs)
        if len(recs['tracks']) == 0:
               track_id = recs['seeds'][0]['id']
        else:
            track_id = recs['tracks'][0]['uri']
        recc_ids.append(track_id)
        #print(len(recc_ids))
    set_ids = set(recc_ids) 
    t2 = time.time()
    print(f'Making and saving all of those recommendations took {t2-t1} seconds.\n')
    return list(set_ids)

def preview_url(track_ids):
    previews = []
    groups = 10
    approx_sizes = len(track_ids)/groups 
    groups_cont = [track_ids[int(i*approx_sizes):int((i+1)*approx_sizes)] 
                   for i in range(groups)]
    for chunk in groups_cont:
        for url in chunk:
            results = sp.track(track_id=url)
            previews.append(results['preview_url'])
    audio_objects = []
    for preview in previews:
        audio_object = requests.get(str(preview))
        audio_objects.append(audio_object)
    return audio_objects
    
def create_playlist(recommended_ids):
    
    print('Creating a playlist now!\n')
    groups = math.ceil(len(recommended_ids) / 95)
    approx_sizes = len(recommended_ids)/groups 
    groups_cont = [recommended_ids[int(i*approx_sizes):int((i+1)*approx_sizes)] 
                   for i in range(groups)]
    
    sp.user_playlist_create(user=user_id, name='Your Recommended Songs!!', description='yay! new songs!')
    playlist_ids, y = get_user_playlist_urls()
    new_id = playlist_ids[0]
    for group in groups_cont:
        if len(group) == 0:
            continue
        elif len(group) > 100:
            group1 = group[0:99]
            group2 = group[100:]
            sp.user_playlist_add_tracks(user=user_id, playlist_id=new_id, tracks=group1)
            sp.user_playlist_add_tracks(user=user_id, playlist_id=new_id, tracks=group2)
        else:
            sp.user_playlist_add_tracks(user=user_id, playlist_id=new_id, tracks=group)
    
def get_saved_tracks():
    ids = []
    print('I\'m starting to look at the user\'s saved tracks!!')
    offset = 0
    t1 = time.time()
    while True:
        track_ids = sp.current_user_saved_tracks(offset=offset)
        if len(track_ids['items']) == 0:
            break
        for track in track_ids['items']:
            if track['track'] == None:
                continue
            else:
                ids.append(track['track']['id'])
        offset = offset + len(track_ids['items'])
        time.sleep(0.1)
    t2 = time.time()
    print(f'Hmmm... getting the liked tracks took {t2-t1} seconds!\n')
    return list(set(ids))


#%%
try:
    playlist_ids, raw_playlists = get_user_playlist_urls()
except:
    playlist_ids, raw_playlists = get_user_playlist_urls()
test_list = playlist_ids[2:]
#test_list2 = playlist_ids[0]

playlist_song_ids = song_ids_from_playlists(user_id, test_list)
#song_ids = song_ids_from_playlists(user_id, playlist_ids)
#print(song_ids[0])

saved_song_ids = get_saved_tracks()
song_ids = playlist_song_ids + saved_song_ids

rec_ids = recc_id(song_ids, user_country)
#print(len(rec_ids))


for song in rec_ids:
    if song in song_ids:
        rec_ids.remove(song)
    else:
        continue
#print(len(rec_ids))

create_playlist(rec_ids)

#preview_audio = preview_url(rec_ids)

#%%

top_artists = sp.current_user_top_artists(time_range='long_term', limit=30)
topartists = []
for i, item in enumerate(top_artists['items']):
    topartists.append(item['name'])
    print(i + 1, item['name'])
   
print('\n')
top_tracks = sp.current_user_top_tracks(time_range='long_term', limit=30)
toptracks = []
for i, item in enumerate(top_tracks['items']):
    toptracks.append(item['name'])
    print(i + 1, item['name'], '//', item['artists'][0]['name'])
    
artist_popularities = []
for i in range(len(top_artists['items'])):
    artist_popularities.append(top_artists['items'][i]['popularity'])
    
track_popularities = []
for i in range(len(top_tracks['items'])):
    track_popularities.append(top_tracks['items'][i]['popularity'])
    
print(sum(artist_popularities)/len(artist_popularities))
print(sum(track_popularities)/len(track_popularities))


