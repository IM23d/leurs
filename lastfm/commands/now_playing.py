"""
LastFM now playing command - Shows the current playing track for a user.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LastFMDataManager
from ..helpers.api_client import LastFMAPIClient
from ..helpers.utils import (
    create_not_linked_embed, 
    format_now_playing_embed, 
    format_no_track_embed, 
    create_error_embed,
    safe_get_scrobble_count
)

class NowPlayingCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LastFMDataManager()
        self.api_client = LastFMAPIClient()

    @commands.command()
    async def np(self, ctx):
        """Show your currently playing track on LastFM."""
        user_id = ctx.author.id
        lastfm_username = self.data_manager.get_lastfm_username(user_id)
        
        # Check if user has linked their account
        if not lastfm_username:
            embed = create_not_linked_embed(ctx.author)
            await ctx.send(embed=embed)
            return
        
        try:
            # Get current playing track
            recent_tracks = self.api_client.get_recent_tracks(lastfm_username, limit=1)
            
            if not recent_tracks or 'track' not in recent_tracks:
                raise Exception("No track data found")
            
            tracks = recent_tracks['track']
            if not tracks:
                raise Exception("No tracks found")
            
            current_track = tracks[0]
            
            # Check if track is currently playing
            is_playing = '@attr' in current_track and current_track['@attr'].get('nowplaying') == 'true'
            
            if not is_playing:
                embed = format_no_track_embed(lastfm_username, ctx.author)
                await ctx.send(embed=embed)
                return
            
            # Extract track information
            artist = current_track['artist']['#text']
            song = current_track['name']
            album = current_track.get('album', {}).get('#text', 'No album info')
            
            # Gather scrobble statistics
            stats_data = {}
            
            try:
                # Get track info for playcount
                track_info = self.api_client.get_track_info(artist, song, lastfm_username)
                stats_data['track_scrobbles'] = safe_get_scrobble_count(track_info, 'track', 'userplaycount')
                
                # Get artist info for scrobble count
                artist_info = self.api_client.get_artist_info(artist, lastfm_username)
                stats_data['artist_scrobbles'] = safe_get_scrobble_count(artist_info, 'artist', 'stats', 'userplaycount')
                
                # Get album info for scrobble count
                album_info = self.api_client.get_album_info(artist, album, lastfm_username)
                stats_data['album_scrobbles'] = safe_get_scrobble_count(album_info, 'album', 'userplaycount')
                
                # Total scrobbles from recent tracks
                stats_data['total_scrobbles'] = safe_get_scrobble_count(recent_tracks, '@attr', 'total')
                
            except Exception as e:
                print(f"Error gathering scrobble stats: {e}")
                # Continue without stats if there's an error
            
            # Create and send embed
            embed = format_now_playing_embed(ctx.author, lastfm_username, current_track, stats_data)
            await ctx.send(embed=embed)
                
        except Exception as e:
            embed = create_error_embed(
                "Error",
                f"Failed to fetch data from Last.fm API: {str(e)}"
            )
            await ctx.send(embed=embed)

async def setup(client):
    await client.add_cog(NowPlayingCommand(client))