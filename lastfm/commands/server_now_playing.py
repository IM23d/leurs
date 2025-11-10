"""
LastFM server now playing command - Shows all currently playing tracks in the server.
"""

import discord
from discord.ext import commands
from ..helpers.data_manager import LastFMDataManager
from ..helpers.api_client import LastFMAPIClient
from ..helpers.utils import format_server_now_playing_embed, create_error_embed

class ServerNowPlayingCommand(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data_manager = LastFMDataManager()
        self.api_client = LastFMAPIClient()

    @commands.command(aliases=["snp"])
    async def servernowplaying(self, ctx):
        """Show all currently playing tracks from linked LastFM accounts in the server."""
        try:
            # Get all linked LastFM accounts
            all_accounts = self.data_manager.get_all_accounts()
            
            if not all_accounts:
                await ctx.send("No LastFM accounts are linked to any server members.")
                return
                
            playing_users = []
            
            # Check each linked LastFM account
            for user_id, lastfm_username in all_accounts.items():
                try:
                    # Get recent tracks
                    recent_tracks = self.api_client.get_recent_tracks(lastfm_username, limit=1)
                    
                    if recent_tracks and 'track' in recent_tracks:
                        tracks = recent_tracks['track']
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
            
            # Create and send embed
            embed = format_server_now_playing_embed(playing_users, len(all_accounts))
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error in servernowplaying: {str(e)}")
            embed = create_error_embed(
                "Error",
                "An error occurred while fetching currently playing tracks."
            )
            await ctx.send(embed=embed)

async def setup(client):
    client.add_cog(ServerNowPlayingCommand(client))