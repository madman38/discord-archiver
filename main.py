import discord
import datetime
import sys
import json
import os
import requests
import zipfile
import shutil
import re
from config import ALLOWED_FILE_TYPES, MAX_DOWNLOAD_SIZE_MB, DISCORD_TOKEN
import colorama
from colorama import Fore

colorama.init(autoreset=True)

print(f"""====================
discord-archiver.py
====================
{Fore.YELLOW}DISCLAIMER: {Fore.WHITE}Please check {Fore.GREEN}config.py {Fore.WHITE}before using this script.""")

if not DISCORD_TOKEN or DISCORD_TOKEN == "TOKEN":
    print(f"{Fore.RED}ERROR: {Fore.WHITE}Please enter your discord token in {Fore.GREEN}config.py")
    input("\nPress Enter to exit.")
    sys.exit(1)

client = discord.Client()

try: channel_id = int(input("\ndiscord channel id: "))
except:
    print(f"{Fore.RED}ERROR: {Fore.WHITE}discord channel id must be an integer.")
    input("\nPress Enter to exit.")
    sys.exit(1)

try: limit = int(input("message range(default = ALL): "))
except: limit = None

limitmessage = limit
if not limit:
    limitmessage = "ALL"

class Person:
    downloaded_pfps = set()

    def __init__(self, userid, pfp, username, time, message, attachment, message_id):
        self.userid = userid
        self.pfp = self.download_pfp(pfp, userid)
        self.username = username
        self.time = time
        self.message = self.process_emojis(message) if message else None
        self.message_id = message_id
        self.attachment = self.download_attachment(attachment) if attachment else None

    def download_pfp(self, pfp_url, userid):
        if not pfp_url:
            return None

        if userid in Person.downloaded_pfps:
            return f"{userid}.png"

        os.makedirs(f"temp_{channel_id}_profile_photos", exist_ok=True)
        filename = f"{userid}.png"
        file_path = os.path.join(f'temp_{channel_id}_profile_photos', filename)

        if not os.path.exists(file_path):
            with requests.get(pfp_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

        Person.downloaded_pfps.add(userid)
        return filename

    def download_attachment(self, attachment_urls):
        downloaded_attachments = []
        for url in attachment_urls:
            file_name = url.split('/')[-1].split('?')[0]
            file_extension = file_name.split('.')[-1].lower()
            
            if file_extension not in ALLOWED_FILE_TYPES:
                continue
            
            response = requests.head(url)
            file_size_mb = int(response.headers.get('Content-Length', 0)) / (1024 * 1024)
            
            if file_size_mb > MAX_DOWNLOAD_SIZE_MB:
                continue
            
            os.makedirs(f'temp_{channel_id}_attachments', exist_ok=True)
            
            unique_filename = f"{self.message_id}_{file_name}"
            file_path = os.path.join(f'temp_{channel_id}_attachments', unique_filename)
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            downloaded_attachments.append(unique_filename)
        
        return downloaded_attachments

    @staticmethod
    def download_emoji(emoji_id, emoji_name, animated=False):
        extension = 'gif' if animated else 'png'
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
        os.makedirs(f"temp_{channel_id}_emojis", exist_ok=True)
        filename = f"{emoji_id}_{emoji_name}.{extension}"
        file_path = os.path.join(f'temp_{channel_id}_emojis', filename)

        if not os.path.exists(file_path):
            with requests.get(emoji_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

        return filename

    def process_emojis(self, message):
        static_emoji_pattern = r'<:(\w+):(\d+)>'
        animated_emoji_pattern = r'<a:(\w+):(\d+)>'

        static_emojis = re.findall(static_emoji_pattern, message)
        for emoji_name, emoji_id in static_emojis:
            filename = self.download_emoji(emoji_id, emoji_name, animated=False)
            message = message.replace(f'<:{emoji_name}:{emoji_id}>', f'[EMOJI:{filename}]')

        animated_emojis = re.findall(animated_emoji_pattern, message)
        for emoji_name, emoji_id in animated_emojis:
            filename = self.download_emoji(emoji_id, emoji_name, animated=True)
            message = message.replace(f'<a:{emoji_name}:{emoji_id}>', f'[EMOJI:{filename}]')
        
        return message

    def makejson(self):
        data = {
            "userid": self.userid,
            "pfp": self.pfp,
            "username": self.username,
            "time": self.time,
            "message": self.message,
            "attachment": self.attachment,
            "message_id": self.message_id
        }
        return data

@client.event
async def on_ready():
    print("Bot is ready.")

    channel = client.get_channel(channel_id)
    if channel:
        print(f"fetching and archiving messages from #{channel.name}...")
    else:
        input("channel not found.\n\nPress Enter to exit.")
        sys.exit(1)

    messages = await channel.history(limit=limit).flatten()
    messages.reverse()

    all_messages = []
    for message in messages:
        try:
            time = (datetime.datetime.strptime(str(message.created_at), "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M") # 'hours=3' is for GMT+3
        except:
            pass

        content = message.content
        att = None

        if message.attachments:
            att = [attachment.url for attachment in message.attachments]
            if not content:
                content = None

        if not content and not att:
            continue

        if content or att:
            jsondata = {
                "userid": message.author.id,
                "pfp": str(message.author.avatar_url),
                "username": message.author.display_name,
                "time": time,
                "message": content,
                "attachment": att,
                "message_id": message.id
            }
            all_messages.append(jsondata)

    temp_json_filename = f"temp_{channel_id}_{channel.name}.json"
    with open(temp_json_filename, "w", encoding="utf-8") as file:
        json.dump(all_messages, file, indent=2, ensure_ascii=False)

    print(f"JSON file saved: {temp_json_filename}")

    for message_data in all_messages:
        p = Person(message_data["userid"], message_data["pfp"], message_data["username"], 
                   message_data["time"], message_data["message"], message_data["attachment"], 
                   message_data["message_id"])
        message_data["pfp"] = p.pfp
        message_data["message"] = p.message
        message_data["attachment"] = p.attachment

    with open(temp_json_filename, "w", encoding="utf-8") as file:
        json.dump(all_messages, file, indent=2, ensure_ascii=False)

    zip_filename = f"#{channel.name}_archive.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        zipf.write(temp_json_filename, arcname=f"#{channel.name}.json")
        if os.path.exists(f'temp_{channel_id}_attachments'):
            for root, _, files in os.walk(f'temp_{channel_id}_attachments'):
                for file in files:
                    zipf.write(os.path.join(root, file), f"attachments/{file}")

        if os.path.exists(f'temp_{channel_id}_profile_photos'):
            for root, _, files in os.walk(f'temp_{channel_id}_profile_photos'):
                for file in files:
                    zipf.write(os.path.join(root, file), f"profile_photos/{file}")

        if os.path.exists(f'temp_{channel_id}_emojis'):
            for root, _, files in os.walk(f'temp_{channel_id}_emojis'):
                for file in files:
                    zipf.write(os.path.join(root, file), f"emojis/{file}")

    os.remove(temp_json_filename)
    shutil.rmtree(f"temp_{channel_id}_attachments", ignore_errors=True)
    shutil.rmtree(f"temp_{channel_id}_profile_photos", ignore_errors=True)
    shutil.rmtree(f"temp_{channel_id}_emojis", ignore_errors=True)

    input(f"Saved last {limitmessage} messages from {channel.name} to {zip_filename}\n\nPress Enter to exit.")
    sys.exit(1)

client.run(DISCORD_TOKEN, bot=False)
