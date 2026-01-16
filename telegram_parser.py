import asyncio
import os
import random
import string
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.errors import ChannelPrivateError, PeerFloodError, UserPrivacyRestrictedError

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'telegram_session'

def generate_random_filename(length=4):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length)) + '.txt'

async def parse_participants():
    output_file = generate_random_filename()
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("Connecting to Telegram...")
        await client.start()
        print("Successfully connected!")
        
        participants_set = set()
        bots_count = 0
        total_scanned = 0
        dialogs_processed = 0
        dialogs_skipped = 0
        
        print("\nStage 1: Scanning all dialogs...")
        print("Searching for groups, chats, and channels...\n")
        
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, User):
                continue
            
            if isinstance(entity, (Channel, Chat)):
                dialogs_processed += 1
                dialog_title = getattr(entity, 'title', 'No title')
                dialog_id = entity.id
                
                print(f"[{dialogs_processed}] Processing: {dialog_title} (ID: {dialog_id})")
                
                try:
                    dialog_users_count = 0
                    dialog_bots_count = 0
                    
                    async for user in client.iter_participants(entity):
                        if user.id:
                            total_scanned += 1
                            
                            if not user.bot:
                                participants_set.add(user.id)
                                dialog_users_count += 1
                            else:
                                bots_count += 1
                                dialog_bots_count += 1
                    
                    print(f"    ✓ Found users: {dialog_users_count}, bots: {dialog_bots_count}")
                    
                except ChannelPrivateError:
                    print(f"    ⚠ Skipped (private/no access)")
                    dialogs_skipped += 1
                except UserPrivacyRestrictedError:
                    print(f"    ⚠ Skipped (restricted access)")
                    dialogs_skipped += 1
                except PeerFloodError:
                    print(f"    ⚠ Request limit exceeded, pausing...")
                    await asyncio.sleep(60)
                    dialogs_skipped += 1
                except Exception as e:
                    print(f"    ⚠ Error: {e}")
                    dialogs_skipped += 1
                
                await asyncio.sleep(0.5)
        
        print(f"\n{'='*50}")
        print(f"Scanning completed!")
        print(f"{'='*50}")
        print(f"Dialogs processed: {dialogs_processed}")
        print(f"Dialogs skipped: {dialogs_skipped}")
        print(f"Total participants scanned: {total_scanned}")
        print(f"Bots filtered: {bots_count}")
        print(f"Unique users found: {len(participants_set)}")
        
        if len(participants_set) == 0:
            print("\n⚠️ No users found to save!")
            return
        
        print(f"\nStage 2: Saving user IDs...")
        
        sorted_ids = sorted(participants_set)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for user_id in sorted_ids:
                f.write(f"{user_id}\n")
        
        print(f"\n{'='*50}")
        print(f"Parsing completed!")
        print(f"{'='*50}")
        print(f"Total unique user IDs saved: {len(participants_set)}")
        print(f"IDs saved to file: {output_file}")
        
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

async def main():
    print("=" * 50)
    print("Telegram Participants Parser")
    print("=" * 50)
    
    if not API_ID or not API_HASH:
        print("\n⚠️  WARNING!")
        print("You need to specify API_ID and API_HASH in the .env file")
        print("1. Go to https://my.telegram.org")
        print("2. Log in with your phone number")
        print("3. Go to 'API development tools'")
        print("4. Create an application and copy api_id and api_hash")
        print("5. Paste them into the .env file (copy .env.example to .env and fill it)\n")
        return
    
    await parse_participants()

if __name__ == '__main__':
    asyncio.run(main())