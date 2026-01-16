import asyncio
import os
import random
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputUser
from telethon.errors import (
    UserAlreadyParticipantError,
    UserPrivacyRestrictedError,
    PeerFloodError,
    FloodWaitError,
    UserNotMutualContactError,
    ChatWriteForbiddenError,
    UserBannedInChannelError,
    UserKickedError,
    ChannelsTooMuchError,
    ChannelPrivateError
)

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'telegram_session'

TARGET_CHAT_ID = -1003512070894
IDS_FILE = 'ids.txt'
DELAY_MIN = 3
DELAY_MAX = 5
BATCH_SIZE = 200

async def invite_users():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("Connecting to Telegram...")
        await client.start()
        print("Successfully connected!")
        
        try:
            target_entity = await client.get_entity(TARGET_CHAT_ID)
            chat_title = getattr(target_entity, 'title', 'No title')
            print(f"Target chat: {chat_title} (ID: {TARGET_CHAT_ID})")
        except ValueError:
            print(f"Error: Chat with ID {TARGET_CHAT_ID} not found")
            return
        except ChannelPrivateError:
            print(f"Error: Chat is private or you don't have access")
            return
        
        try:
            with open(IDS_FILE, 'r', encoding='utf-8') as f:
                user_ids = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            user_id = int(line)
                            user_ids.append(user_id)
                        except ValueError:
                            continue
        except FileNotFoundError:
            print(f"Error: File {IDS_FILE} not found!")
            return
        
        if not user_ids:
            print(f"Error: No valid IDs found in file {IDS_FILE}!")
            return
        
        print(f"Found user IDs: {len(user_ids)}")
        
        is_channel = hasattr(target_entity, 'broadcast') or (hasattr(target_entity, 'megagroup') and target_entity.megagroup)
        effective_batch_size = BATCH_SIZE if is_channel else 1
        
        if is_channel:
            print(f"Type: Channel/Supergroup (batch invitation: {BATCH_SIZE} at a time)")
        else:
            print(f"Type: Regular group (individual invitation)")
        
        print(f"Starting to add participants...\n")
        
        success_count = 0
        already_member_count = 0
        privacy_restricted_count = 0
        error_count = 0
        skipped_count = 0
        
        batches = [user_ids[i:i + effective_batch_size] for i in range(0, len(user_ids), effective_batch_size)]
        print(f"Batches formed: {len(batches)} (by {effective_batch_size} users)\n")
        
        total_processed = 0
        for batch_num, batch in enumerate(batches, 1):
            print(f"Batch {batch_num}/{len(batches)}: processing {len(batch)} users...")
            
            users_to_invite = []
            batch_skipped = []
            
            for user_id in batch:
                try:
                    user = await client.get_entity(user_id)
                    users_to_invite.append(user)
                except ValueError:
                    print(f"  User {user_id}: not found, skipping...")
                    skipped_count += 1
                    batch_skipped.append(user_id)
                except Exception as e:
                    print(f"  User {user_id}: error {e}, skipping...")
                    skipped_count += 1
                    batch_skipped.append(user_id)
            
            if not users_to_invite:
                print(f"  No valid users in batch, skipping...\n")
                continue
            
            try:
                if is_channel:
                    await client(InviteToChannelRequest(
                        channel=target_entity,
                        users=users_to_invite
                    ))
                    print(f"  ✓ Successfully added: {len(users_to_invite)} users")
                    success_count += len(users_to_invite)
                else:
                    for user in users_to_invite:
                        try:
                            await client(AddChatUserRequest(
                                chat_id=target_entity.id,
                                user_id=user,
                                fwd_limit=0
                            ))
                            success_count += 1
                            total_processed += 1
                            username = getattr(user, 'username', None)
                            display_name = f"@{username}" if username else f"ID:{user.id}"
                            print(f"  [{total_processed}] ✓ Added: {display_name}")
                        except UserAlreadyParticipantError:
                            already_member_count += 1
                            total_processed += 1
                        except UserPrivacyRestrictedError:
                            privacy_restricted_count += 1
                            total_processed += 1
                        except Exception as e:
                            print(f"  ✗ Error for user {user.id}: {e}")
                            error_count += 1
                            total_processed += 1
                    continue
                    
            except FloodWaitError as e:
                print(f"  ✗ Limit exceeded, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
                try:
                    if is_channel:
                        await client(InviteToChannelRequest(
                            channel=target_entity,
                            users=users_to_invite
                        ))
                        print(f"  ✓ Added after waiting: {len(users_to_invite)} users")
                        success_count += len(users_to_invite)
                    else:
                        for user in users_to_invite:
                            try:
                                await client(AddChatUserRequest(
                                    chat_id=target_entity.id,
                                    user_id=user,
                                    fwd_limit=0
                                ))
                                success_count += 1
                            except:
                                error_count += 1
                except Exception as retry_e:
                    print(f"  ✗ Error on retry: {retry_e}")
                    error_count += len(users_to_invite)
                    
            except (UserPrivacyRestrictedError, UserNotMutualContactError) as e:
                print(f"  ⚠ Some users cannot be added, processing individually...")
                for user in users_to_invite:
                    try:
                        if is_channel:
                            await client(InviteToChannelRequest(
                                channel=target_entity,
                                users=[user]
                            ))
                            success_count += 1
                            username = getattr(user, 'username', None)
                            display_name = f"@{username}" if username else f"ID:{user.id}"
                            print(f"    ✓ Added: {display_name}")
                        else:
                            await client(AddChatUserRequest(
                                chat_id=target_entity.id,
                                user_id=user,
                                fwd_limit=0
                            ))
                            success_count += 1
                            username = getattr(user, 'username', None)
                            display_name = f"@{username}" if username else f"ID:{user.id}"
                            print(f"    ✓ Added: {display_name}")
                    except UserAlreadyParticipantError:
                        already_member_count += 1
                    except UserPrivacyRestrictedError:
                        privacy_restricted_count += 1
                    except Exception as single_e:
                        error_count += 1
                        print(f"    ✗ Error: {single_e}")
                        
            except UserAlreadyParticipantError:
                print(f"  ⚠ All users are already in the group")
                already_member_count += len(users_to_invite)
            except ChatWriteForbiddenError:
                print("  ✗ No permission to add participants")
                print("Stopping: you don't have admin rights to add participants")
                break
            except PeerFloodError:
                print("  ✗ Too many requests, pausing for 60 seconds...")
                await asyncio.sleep(60)
                error_count += len(users_to_invite)
            except ChannelsTooMuchError:
                print("  ✗ Some users are in too many channels")
                error_count += len(users_to_invite)
            except Exception as e:
                print(f"  ✗ Batch error: {e}")
                error_count += len(users_to_invite)
            
            total_processed += len(batch)
            
            if batch_num < len(batches):
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                print(f"  Pause {delay:.1f} sec before next batch...\n")
                await asyncio.sleep(delay)
        
        print(f"\n{'='*50}")
        print("Completed!")
        print(f"{'='*50}")
        print(f"Total processed: {len(user_ids)}")
        print(f"✓ Successfully added: {success_count}")
        print(f"⚠ Already members: {already_member_count}")
        print(f"⚠ Privacy restricted: {privacy_restricted_count}")
        print(f"✗ Errors: {error_count}")
        print(f"⊘ Skipped: {skipped_count}")
        
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\nDisconnected from Telegram")

async def main():
    print("=" * 50)
    print("Telegram Participants Inviter")
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
    
    await invite_users()

if __name__ == '__main__':
    asyncio.run(main())