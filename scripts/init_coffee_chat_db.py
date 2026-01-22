"""
Initialize Coffee Chat Database Tables
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.coffee_chat_models import Base, UserProfile, CoffeeChatContact, CoffeeChatInteraction

# Load environment variables
load_dotenv()

def init_database():
    """
    Initialize database tables
    """
    # Connect to database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("Please configure DATABASE_URL in .env file")
        return False
    
    print(f"📡 Connecting to database...")
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local SQLite'}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"\n📋 Existing tables: {existing_tables}")
        
        # Create all tables
        print("\n🔨 Creating Coffee Chat tables...")
        Base.metadata.create_all(engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        
        coffee_chat_tables = ['user_profiles', 'coffee_chat_contacts', 'coffee_chat_interactions']
        
        print("\n✅ Database tables created successfully!")
        print("\nCreated tables:")
        for table in coffee_chat_tables:
            if table in new_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (creation failed)")
        
        # Check if default UserProfile needs to be created
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        profile_count = session.query(UserProfile).count()
        if profile_count == 0:
            print("\n📝 Creating default User Profile...")
            default_profile = UserProfile(
                schools=[],
                target_fields=[],
                daily_connection_limit=20,
                daily_message_limit=10,
                target_location='Canada'
            )
            session.add(default_profile)
            session.commit()
            print("✅ Default User Profile created")
        else:
            print(f"\n✓ User Profile already exists ({profile_count} record(s))")
        
        session.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Coffee Chat Database Initialization")
    print("=" * 50)
    
    success = init_database()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Initialization Complete!")
        print("=" * 50)
        print("\nNext step:")
        print("  Run User Profile page:")
        print("  streamlit run pages/user_profile.py")
    else:
        print("\n" + "=" * 50)
        print("❌ Initialization Failed")
        print("=" * 50)
