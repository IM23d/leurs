"""
Reminder manager for handling reminders functionality.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class ReminderManager:
    def __init__(self, client):
        self.client = client
        self.reminder_tasks: Dict[int, List[asyncio.Task]] = {}
        
    def parse_time(self, time_str: str, reason: str) -> Tuple[Optional[datetime], str]:
        """Parse various time formats into datetime objects."""
        now = datetime.now()
        
        # Handle relative time formats (15m, 2h, 3d)
        relative_match = re.match(r'^(\d+)([smhd])$', time_str.lower())
        if relative_match:
            amount, unit = relative_match.groups()
            amount = int(amount)
            delta = {
                's': timedelta(seconds=amount),
                'm': timedelta(minutes=amount),
                'h': timedelta(hours=amount),
                'd': timedelta(days=amount)
            }[unit]
            return now + delta, reason
            
        # Handle "tomorrow" or "tm"
        if time_str.lower() in ['tomorrow', 'tm']:
            return now + timedelta(days=1), reason
            
        # Handle HH:MM format (both 24h and 12h with am/pm)
        time_match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$', time_str.lower())
        if time_match:
            hour, minute, meridiem = time_match.groups()
            hour = int(hour)
            minute = int(minute) if minute else 0
            
            if meridiem:
                if meridiem == 'pm' and hour < 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0
                    
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target, reason
            
        # Handle date formats (15.05 or 15.05.26 or 15.05.2026)
        date_match = re.match(r'^(\d{1,2})\.(\d{1,2})(?:\.(\d{2}|\d{4}))?$', time_str)
        if date_match:
            day, month, year = date_match.groups()
            day = int(day)
            month = int(month)
            
            if year:
                year = int(year)
                if year < 100:
                    year += 2000
            else:
                year = now.year
                
            try:
                target = datetime(year, month, day, 0, 0, 0)
                if target <= now:
                    if not year:
                        target = target.replace(year=target.year + 1)
                return target, reason
            except ValueError:
                return None, reason
                
        # Handle full datetime format (15.07:15:25:00 or 15.07:15:25)
        datetime_match = re.match(r'^(\d{1,2})\.(\d{1,2}):(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$', time_str)
        if datetime_match:
            day, month, hour, minute, second = datetime_match.groups()
            try:
                target = now.replace(
                    day=int(day),
                    month=int(month),
                    hour=int(hour),
                    minute=int(minute),
                    second=int(second) if second else 0,
                    microsecond=0
                )
                if target <= now:
                    target = target.replace(year=target.year + 1)
                return target, reason
            except ValueError:
                return None, reason
                
        return None, reason
        
    async def send_reminder(self, ctx, user_id: int, channel_id: int, remind_time: datetime, reason: str):
        """Send a reminder after the specified time."""
        try:
            await asyncio.sleep((remind_time - datetime.now()).total_seconds())
            channel = self.client.get_channel(channel_id)
            if channel:
                user = await self.client.fetch_user(user_id)
                embed = {
                    "title": "Reminder",
                    "description": f"{user.mention}, here's your reminder: {reason}",
                    "color": 0x00FF00
                }
                await channel.send(embed=embed)
        except asyncio.CancelledError:
            pass
        finally:
            if user_id in self.reminder_tasks:
                self.reminder_tasks[user_id] = [task for task in self.reminder_tasks[user_id] if not task.done()]
                
    def create_reminder(self, ctx, user_id: int, channel_id: int, remind_time: datetime, reason: str) -> bool:
        """Create a new reminder."""
        if remind_time > datetime.now() + timedelta(days=365):
            return False
            
        if user_id not in self.reminder_tasks:
            self.reminder_tasks[user_id] = []
            
        reminder_task = asyncio.create_task(
            self.send_reminder(ctx, user_id, channel_id, remind_time, reason)
        )
        self.reminder_tasks[user_id].append(reminder_task)
        return True
        
    def get_user_reminders(self, user_id: int) -> List[Dict]:
        """Get active reminders for a user."""
        if user_id not in self.reminder_tasks or not self.reminder_tasks[user_id]:
            return []
            
        # Clean up completed tasks first
        self.reminder_tasks[user_id] = [task for task in self.reminder_tasks[user_id] if not task.done()]
        
        if not self.reminder_tasks[user_id]:
            return []
            
        # Get reminder details from task names
        reminders = []
        now = datetime.now()
        
        for task in self.reminder_tasks[user_id]:
            # Extract reminder time and reason from the task's internal data
            coro = task.get_coro()
            frame = coro.cr_frame
            remind_time = frame.f_locals.get('remind_time')
            reason = frame.f_locals.get('reason')
            
            if remind_time and reason:
                time_diff = remind_time - now
                days = time_diff.days
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                time_parts = []
                if days > 0:
                    time_parts.append(f"{days} days")
                if hours > 0:
                    time_parts.append(f"{hours} hours")
                if minutes > 0:
                    time_parts.append(f"{minutes} minutes")
                if seconds > 0 and not (days or hours or minutes):
                    time_parts.append(f"{seconds} seconds")
                
                time_until = ", ".join(time_parts)
                reminders.append({
                    'time': remind_time,
                    'reason': reason,
                    'time_until': time_until
                })
        
        # Sort reminders by time
        reminders.sort(key=lambda x: x['time'])
        return reminders