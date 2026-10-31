import discord
from discord.ext import commands
import json
import os
import math # not needed as backup
import datetime # not needed as backup
import random # not needed as backup
from dotenv import load_dotenv
import requests

load_dotenv()

lastfmKey = os.getenv("LAST_FM_KEY")

class LastFMCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        if not os.path.exists('data'):
            os.makedirs('data')

    # link lastfm account
    @commands.command()
    async def login(self, ctx, lastfm_username):
        user_id = ctx.author.id
        self.update_user_data(user_id, lastfm_username)
        embed = discord.Embed(
            title="LastFM Account Linked",
            description=f"Your LastFM account has been linked to Leurs!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    def update_user_data(self, user_id, lastfm_username):
        try: 
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        user_data[str(user_id)] = lastfm_username

        with open('data/lastfm.json', 'w') as f:
            json.dump(user_data, f)

    def get_lastfm_username(self, user_id):
        try:
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
            return user_data.get(str(user_id))
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # show lastfm profile including scrobbles, registered date, total tracks, etc.
    @commands.command(name="lastfm", aliases=["lf", "profile", "me", "p"])
    async def lastfm_stats(self, ctx):
        user_id = ctx.author.id
        lastfm_username = self.get_lastfm_username(user_id)
        
        if not lastfm_username:
            embed = discord.Embed(
                title="LastFM Not Linked",
                description="You haven't linked your LastFM account yet. Use `-login [username]` to link it!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            return

        # Get user info
        user_info_url = f"http://ws.audioscrobbler.com/2.0/?method=user.getInfo&user={lastfm_username}&api_key={lastfmKey}&format=json"
        
        try:
            response = requests.get(user_info_url)
            response.raise_for_status()
            user_info = response.json()['user']

            # Extract user information
            total_scrobbles = user_info['playcount']
            registered = int(user_info['registered']['unixtime'])
            registered_date = datetime.datetime.fromtimestamp(registered).strftime('%B %d, %Y')
            profile_url = user_info['url']
            
            # Create embed
            embed = discord.Embed(color=0x2b2d31)
            embed.set_author(name=f"Last.fm: {lastfm_username}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
                           url=profile_url)

            # Add user avatar if available
            if user_info.get('image'):
                avatar_url = user_info['image'][-1]['#text']
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)

            # Add statistics
            stats = f"**Total Scrobbles:** {total_scrobbles}\n"
            stats += f"**Account Created:** {registered_date}\n"
            
            # Get recent track count
            recent_tracks_url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"
            recent_response = requests.get(recent_tracks_url)
            if recent_response.ok:
                recent_data = recent_response.json()
                if 'recenttracks' in recent_data and '@attr' in recent_data['recenttracks']:
                    total_tracks = recent_data['recenttracks']['@attr']['total']
                    stats += f"**Total Tracks:** {total_tracks}"

            embed.description = stats
            
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch data from Last.fm API: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    def get_track_info(self, artist, track):
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={artist}&track={track}&username={self.lastfm_username}&api_key={lastfmKey}&format=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return None
     
    # show current playing track if there is one
    @commands.command()
    async def np(self, ctx):
        user_id = ctx.author.id
        lastfm_username = self.get_lastfm_username(user_id)
        
        if not lastfm_username:
            embed = discord.Embed(
                title="LastFM Not Linked",
                description="You haven't linked your LastFM account yet. Use `-login [username]` to link it!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Get current playing track
        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'recenttracks' in data and 'track' in data['recenttracks']:
                tracks = data['recenttracks']['track']
                if not tracks:
                    raise Exception("No tracks found")
                
                current_track = tracks[0]
                
                # Check if track is currently playing
                is_playing = '@attr' in current_track and current_track['@attr'].get('nowplaying') == 'true'
                
                if not is_playing:
                    embed = discord.Embed(
                        color=0x2b2d31,
                        description="No track currently playing"
                    )
                    embed.set_author(name=f"Last.fm: {lastfm_username}", 
                                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                    await ctx.send(embed=embed)
                    return
                
                artist = current_track['artist']['#text']
                song = current_track['name']
                album = current_track.get('album', {}).get('#text', 'No album info')
                image_url = current_track.get('image', [])[-1]['#text'] if current_track.get('image') else None
                
                # Get track info for playcount
                track_info_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={lastfmKey}&artist={artist}&track={song}&username={lastfm_username}&format=json"
                track_info = requests.get(track_info_url).json()
                
                playcount = track_info.get('track', {}).get('userplaycount', '0')
                
                # Get artist info for scrobble count
                artist_info_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key={lastfmKey}&artist={artist}&username={lastfm_username}&format=json"
                artist_info = requests.get(artist_info_url).json()
                artist_scrobbles = artist_info.get('artist', {}).get('stats', {}).get('userplaycount', '0')
                
                # Get album info for scrobble count
                album_info_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getInfo&api_key={lastfmKey}&artist={artist}&album={album}&username={lastfm_username}&format=json"
                album_info = requests.get(album_info_url).json()
                album_scrobbles = album_info.get('album', {}).get('userplaycount', '0')
                
                # Create embed
                embed = discord.Embed(color=0x2b2d31)  # Dark theme color
                
                # Set author with Last.fm username
                embed.set_author(name=f"Last.fm: {lastfm_username}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                
                # Format track and artist as clickable links
                artist_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}"
                track_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{song.replace(' ', '+')}"
                album_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{album.replace(' ', '+')}"

                # Add thumbnail first to ensure it doesn't affect text layout
                if image_url:
                    embed.set_thumbnail(url=image_url)
                
                # Create content with track and artist info
                left_content = "Track\n"
                left_content += f"[{song}]({track_url})\n"
                left_content += "Artist\n"
                left_content += f"[{artist}]({artist_url})\n"
                left_content += "Album\n"
                left_content += f"[{album}]({album_url})"
                
                # Add content
                embed.description = left_content
                                                
                # Add scrobble stats at the bottom (artist, album, track, total)
                total_scrobbles = data['recenttracks']['@attr']['total']
                scrobble_stats = f"{artist_scrobbles} artist scrobbles • {album_scrobbles} album scrobbles\n{playcount} track scrobbles • {total_scrobbles} total scrobbles"
                embed.add_field(name="", value=scrobble_stats, inline=False)
                
                await ctx.send(embed=embed)
            else:
                raise Exception("No track data found")
                
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch data from Last.fm API: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=["snp"])
    async def servernowplaying(self, ctx):
        try:
            # Load LastFM usernames from json
            with open('data/lastfm.json', 'r') as f:
                lastfm_data = json.load(f)
            
            if not lastfm_data:
                await ctx.send("No LastFM accounts are linked to any server members.")
                return
                
            playing_users = []
            
            # Check each linked LastFM account
            for user_id, lastfm_username in lastfm_data.items():
                # Use the same logic as the np command
                url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"
                
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'recenttracks' in data and 'track' in data['recenttracks']:
                        tracks = data['recenttracks']['track']
                        if tracks:
                            current_track = tracks[0]
                            
                            # Check if track is currently playing
                            is_playing = '@attr' in current_track and current_track['@attr'].get('nowplaying') == 'true'
                            
                            if is_playing:
                                artist = current_track['artist']['#text']
                                song = current_track['name']
                                
                                playing_users.append({
                                    'username': lastfm_username,
                                    'song': song,
                                    'artist': artist
                                })
                                
                except Exception as e:
                    print(f"Error fetching data for {lastfm_username}: {str(e)}")
                    continue
            
            # Create embed
            embed = discord.Embed(
                title="Currently Playing in Server",
                color=0x2b2d31
            )
            
            if playing_users:
                description = "\n"  # Add initial spacing after header
                for i, user in enumerate(playing_users):
                    # Create clickable links
                    artist_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}"
                    track_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}/{user['song'].replace(' ', '+')}"
                    profile_url = f"https://www.last.fm/user/{user['username']}"
                    
                    description += f"[{user['username']}]({profile_url})\n"
                    description += f"[{user['song']}]({track_url}) - [{user['artist']}]({artist_url})"
                    
                    if i < len(playing_users) - 1:
                        description += "\n\n"
                
                # Add summary line with same spacing as header
                description += "\n\n"
                description += f"Users currently listening: {len(playing_users)} - Total users with LastFM: {len(lastfm_data)}"
                embed.description = description
            else:
                embed.description = f"No one is currently listening to music\nTotal users with LastFM: {len(lastfm_data)}"
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in servernowplaying: {str(e)}")
            await ctx.send("An error occurred while fetching currently playing tracks.")

    @commands.command()
    async def logout(self, ctx):
        user_id = ctx.author.id
        try:
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
                
            if str(user_id) not in user_data:
                embed = discord.Embed(
                    title="Not Logged In",
                    description="You don't have a LastFM account linked.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}", 
                               icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.send(embed=embed)
                return
                
            # Remove the user's data
            del user_data[str(user_id)]
            
            # Save the updated data
            with open('data/lastfm.json', 'w') as f:
                json.dump(user_data, f)
                
            embed = discord.Embed(
                title="LastFM Account Unlinked",
                description="Your LastFM account has been unlinked from Leurs!",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in logout: {str(e)}")
            await ctx.send("An error occurred while trying to unlink your LastFM account.")

async def setup(client):
    try:
        await client.add_cog(LastFMCog(client))
        print("LastFM cog loaded successfully")
    except Exception as e:
        print(f"Error loading LastFM cog: {e}")

import discord
from discord.ext import commands
import json
import os
import math # not needed as backup
import datetime # not needed as backup
import random # not needed as backup
from dotenv import load_dotenv
import requests

load_dotenv()

lastfmKey = os.getenv("LAST_FM_KEY")

class LastFMCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        # Ensure data directory exists
        if not os.path.exists('data'):
            os.makedirs('data')

    # link lastfm account to bot
    @commands.command()
    async def login(self, ctx, lastfm_username):
        user_id = ctx.author.id
        self.update_user_data(user_id, lastfm_username)
        embed = discord.Embed(
            title="LastFM Account Linked",
            description=f"Your LastFM account has been linked to Leurs!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    def update_user_data(self, user_id, lastfm_username):
        try: 
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_data = {}

        user_data[str(user_id)] = lastfm_username

        with open('data/lastfm.json', 'w') as f:
            json.dump(user_data, f)

    def get_lastfm_username(self, user_id):
        try:
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
            return user_data.get(str(user_id))
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # show lastfm profile including scrobbles, registered date, total tracks, etc.
    @commands.command(name="lastfm", aliases=["lf", "profile", "me", "p"])
    async def lastfm_stats(self, ctx):
        user_id = ctx.author.id
        lastfm_username = self.get_lastfm_username(user_id)
        
        if not lastfm_username:
            embed = discord.Embed(
                title="LastFM Not Linked",
                description="You haven't linked your LastFM account yet. Use `-login [username]` to link it!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            return

        # Get user info
        user_info_url = f"http://ws.audioscrobbler.com/2.0/?method=user.getInfo&user={lastfm_username}&api_key={lastfmKey}&format=json"
        
        try:
            response = requests.get(user_info_url)
            response.raise_for_status()
            user_info = response.json()['user']

            # Extract user information
            total_scrobbles = user_info['playcount']
            registered = int(user_info['registered']['unixtime'])
            registered_date = datetime.datetime.fromtimestamp(registered).strftime('%B %d, %Y')
            profile_url = user_info['url']
            
            # Create embed
            embed = discord.Embed(color=0x2b2d31)
            embed.set_author(name=f"Last.fm: {lastfm_username}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url,
                           url=profile_url)

            # Add user avatar if available
            if user_info.get('image'):
                avatar_url = user_info['image'][-1]['#text']
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)

            # Add statistics
            stats = f"**Total Scrobbles:** {total_scrobbles}\n"
            stats += f"**Account Created:** {registered_date}\n"
            
            # Get recent track count
            recent_tracks_url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"
            recent_response = requests.get(recent_tracks_url)
            if recent_response.ok:
                recent_data = recent_response.json()
                if 'recenttracks' in recent_data and '@attr' in recent_data['recenttracks']:
                    total_tracks = recent_data['recenttracks']['@attr']['total']
                    stats += f"**Total Tracks:** {total_tracks}"

            embed.description = stats
            
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch data from Last.fm API: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    def get_track_info(self, artist, track):
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={artist}&track={track}&username={self.lastfm_username}&api_key={lastfmKey}&format=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except:
            return None
     
    # show current playing track if there is one
    @commands.command()
    async def np(self, ctx):
        user_id = ctx.author.id
        lastfm_username = self.get_lastfm_username(user_id)
        
        if not lastfm_username:
            embed = discord.Embed(
                title="LastFM Not Linked",
                description="You haven't linked your LastFM account yet. Use `-login [username]` to link it!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Get current playing track
        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'recenttracks' in data and 'track' in data['recenttracks']:
                tracks = data['recenttracks']['track']
                if not tracks:
                    raise Exception("No tracks found")
                
                current_track = tracks[0]
                
                # Check if track is currently playing
                is_playing = '@attr' in current_track and current_track['@attr'].get('nowplaying') == 'true'
                
                if not is_playing:
                    embed = discord.Embed(
                        color=0x2b2d31,
                        description="No track currently playing"
                    )
                    embed.set_author(name=f"Last.fm: {lastfm_username}", 
                                   icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                    await ctx.send(embed=embed)
                    return
                
                artist = current_track['artist']['#text']
                song = current_track['name']
                album = current_track.get('album', {}).get('#text', 'No album info')
                image_url = current_track.get('image', [])[-1]['#text'] if current_track.get('image') else None
                
                # Get track info for playcount
                track_info_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={lastfmKey}&artist={artist}&track={song}&username={lastfm_username}&format=json"
                track_info = requests.get(track_info_url).json()
                
                playcount = track_info.get('track', {}).get('userplaycount', '0')
                
                # Get artist info for scrobble count
                artist_info_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&api_key={lastfmKey}&artist={artist}&username={lastfm_username}&format=json"
                artist_info = requests.get(artist_info_url).json()
                artist_scrobbles = artist_info.get('artist', {}).get('stats', {}).get('userplaycount', '0')
                
                # Get album info for scrobble count
                album_info_url = f"http://ws.audioscrobbler.com/2.0/?method=album.getInfo&api_key={lastfmKey}&artist={artist}&album={album}&username={lastfm_username}&format=json"
                album_info = requests.get(album_info_url).json()
                album_scrobbles = album_info.get('album', {}).get('userplaycount', '0')
                
                # Create embed
                embed = discord.Embed(color=0x2b2d31)  # Dark theme color
                
                # Set author with Last.fm username
                embed.set_author(name=f"Last.fm: {lastfm_username}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                
                # Format track and artist as clickable links
                artist_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}"
                track_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{song.replace(' ', '+')}"
                album_url = f"https://www.last.fm/music/{artist.replace(' ', '+')}/{album.replace(' ', '+')}"

                # Add thumbnail first to ensure it doesn't affect text layout
                if image_url:
                    embed.set_thumbnail(url=image_url)
                
                # Create content with track and artist info
                left_content = "Track\n"
                left_content += f"[{song}]({track_url})\n"
                left_content += "Artist\n"
                left_content += f"[{artist}]({artist_url})\n"
                left_content += "Album\n"
                left_content += f"[{album}]({album_url})"
                
                # Add content
                embed.description = left_content
                                                
                # Add scrobble stats at the bottom (artist, album, track, total)
                total_scrobbles = data['recenttracks']['@attr']['total']
                scrobble_stats = f"{artist_scrobbles} artist scrobbles • {album_scrobbles} album scrobbles\n{playcount} track scrobbles • {total_scrobbles} total scrobbles"
                embed.add_field(name="", value=scrobble_stats, inline=False)
                
                await ctx.send(embed=embed)
            else:
                raise Exception("No track data found")
                
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to fetch data from Last.fm API: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=["snp"])
    async def servernowplaying(self, ctx):
        try:
            # Load LastFM usernames from json
            with open('data/lastfm.json', 'r') as f:
                lastfm_data = json.load(f)
            
            if not lastfm_data:
                await ctx.send("No LastFM accounts are linked to any server members.")
                return
                
            playing_users = []
            
            # Check each linked LastFM account
            for user_id, lastfm_username in lastfm_data.items():
                # Use the same logic as the np command
                url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={lastfm_username}&api_key={lastfmKey}&format=json&limit=1"
                
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'recenttracks' in data and 'track' in data['recenttracks']:
                        tracks = data['recenttracks']['track']
                        if tracks:
                            current_track = tracks[0]
                            
                            # Check if track is currently playing
                            is_playing = '@attr' in current_track and current_track['@attr'].get('nowplaying') == 'true'
                            
                            if is_playing:
                                artist = current_track['artist']['#text']
                                song = current_track['name']
                                
                                playing_users.append({
                                    'username': lastfm_username,
                                    'song': song,
                                    'artist': artist
                                })
                                
                except Exception as e:
                    print(f"Error fetching data for {lastfm_username}: {str(e)}")
                    continue
            
            # Create embed
            embed = discord.Embed(
                title="Currently Playing in Server",
                color=0x2b2d31
            )
            
            if playing_users:
                description = "\n"  # Add initial spacing after header
                for i, user in enumerate(playing_users):
                    # Create clickable links
                    artist_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}"
                    track_url = f"https://www.last.fm/music/{user['artist'].replace(' ', '+')}/{user['song'].replace(' ', '+')}"
                    profile_url = f"https://www.last.fm/user/{user['username']}"
                    
                    description += f"[{user['username']}]({profile_url})\n"
                    description += f"[{user['song']}]({track_url}) - [{user['artist']}]({artist_url})"
                    
                    if i < len(playing_users) - 1:
                        description += "\n\n"
                
                # Add summary line with same spacing as header
                description += "\n\n"
                description += f"Users currently listening: {len(playing_users)} - Total users with LastFM: {len(lastfm_data)}"
                embed.description = description
            else:
                embed.description = f"No one is currently listening to music\nTotal users with LastFM: {len(lastfm_data)}"
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in servernowplaying: {str(e)}")
            await ctx.send("An error occurred while fetching currently playing tracks.")

    @commands.command()
    async def logout(self, ctx):
        user_id = ctx.author.id
        try:
            with open('data/lastfm.json', 'r') as f:
                user_data = json.load(f)
                
            if str(user_id) not in user_data:
                embed = discord.Embed(
                    title="Not Logged In",
                    description="You don't have a LastFM account linked.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}", 
                               icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.send(embed=embed)
                return
                
            # Remove the user's data
            del user_data[str(user_id)]
            
            # Save the updated data
            with open('data/lastfm.json', 'w') as f:
                json.dump(user_data, f)
                
            embed = discord.Embed(
                title="LastFM Account Unlinked",
                description="Your LastFM account has been unlinked from Leurs!",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in logout: {str(e)}")
            await ctx.send("An error occurred while trying to unlink your LastFM account.")

async def setup(client):
    try:
        await client.add_cog(LastFMCog(client))
        print("LastFM cog loaded successfully")
    except Exception as e:
        print(f"Error loading LastFM cog: {e}")
