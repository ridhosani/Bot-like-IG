import json
import time
import random
import schedule
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramBot:
    def __init__(self, config_file='config.json'):
        self.client = Client()
        self.config = self.load_config(config_file)
        self.likes_count_today = 0
        self.reset_time = datetime.now().date()
        
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def login(self):
        """Login to Instagram"""
        try:
            logger.info("Attempting to login...")
            self.client.login(self.config['username'], self.config['password'])
            logger.info("Login successful!")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def like_user_posts(self, username, count=5):
        """Like posts from a specific user"""
        try:
            user_id = self.client.user_id_from_username(username)
            posts = self.client.user_medias(user_id, count)
            
            for post in posts:
                if self.should_like():
                    self.like_post(post)
                time.sleep(random.randint(5, 15))
                
        except Exception as e:
            logger.error(f"Error liking posts from {username}: {e}")
    
    def like_hashtag_posts(self, hashtag, count=10):
        """Like posts from a specific hashtag"""
        try:
            posts = self.client.hashtag_medias_recent(hashtag, count)
            
            for post in posts:
                if self.should_like() and self.likes_count_today < self.config['max_likes_per_day']:
                    self.like_post(post)
                    self.likes_count_today += 1
                    
                    # Random delay between actions
                    delay = random.randint(
                        self.config['delay_between_actions'] - 10,
                        self.config['delay_between_actions'] + 10
                    )
                    time.sleep(delay)
                    
        except Exception as e:
            logger.error(f"Error liking posts from #{hashtag}: {e}")
    
    def like_post(self, post):
        """Like a single post"""
        try:
            if not post.has_liked:
                self.client.media_like(post.id)
                logger.info(f"Liked post: {post.code}")
                return True
        except Exception as e:
            logger.error(f"Error liking post {post.code}: {e}")
        return False
    
    def should_like(self):
        """Determine if should like based on probability"""
        return random.randint(1, 100) <= self.config['like_probability']
    
    def reset_daily_counter(self):
        """Reset daily like counter"""
        today = datetime.now().date()
        if today > self.reset_time:
            self.likes_count_today = 0
            self.reset_time = today
            logger.info("Daily counter reset")
    
    def run_bot_session(self):
        """Run one bot session"""
        self.reset_daily_counter()
        
        if self.likes_count_today >= self.config['max_likes_per_day']:
            logger.info("Daily like limit reached")
            return
        
        # Like posts from target users
        for user in self.config['target_users']:
            if self.likes_count_today < self.config['max_likes_per_day']:
                self.like_user_posts(user, count=3)
        
        # Like posts from hashtags
        for hashtag in self.config['hashtags']:
            if self.likes_count_today < self.config['max_likes_per_day']:
                remaining_likes = self.config['max_likes_per_day'] - self.likes_count_today
                count = min(10, remaining_likes)
                self.like_hashtag_posts(hashtag, count)
    
    def start_scheduled(self):
        """Start bot with scheduling"""
        # Run every 2 hours between 8 AM and 10 PM
        schedule.every(2).hours.between("08:00", "22:00").do(self.run_bot_session)
        
        # Run immediately first time
        self.run_bot_session()
        
        logger.info("Bot started with scheduling...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main function"""
    print("=" * 50)
    print("Instagram Bot - Like Automation")
    print("=" * 50)
    
    bot = InstagramBot()
    
    if bot.login():
        print("\n1. Run one session")
        print("2. Start scheduled bot")
        print("3. Exit")
        
        choice = input("\nChoose option (1-3): ")
        
        if choice == '1':
            print("\nRunning one session...")
            bot.run_bot_session()
            print(f"Liked {bot.likes_count_today} posts today")
            
        elif choice == '2':
            print("\nStarting scheduled bot...")
            try:
                bot.start_scheduled()
            except KeyboardInterrupt:
                print("\nBot stopped by user")
        else:
            print("Exiting...")

if __name__ == "__main__":
    main()
