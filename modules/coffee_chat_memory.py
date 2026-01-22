"""
Coffee Chat Memory Layer using ChromaDB
Stores interaction history, learns from successful messages, and optimizes outreach
"""
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger


class CoffeeChatMemory:
    """
    Memory layer for Coffee Chat automation
    Uses ChromaDB for vector storage and retrieval
    """
    
    def __init__(self, persist_directory: str = "./chroma_data"):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create collections
        self.messages_collection = self.client.get_or_create_collection(
            name="coffee_chat_messages",
            metadata={"description": "Message history and templates"}
        )
        
        self.contacts_collection = self.client.get_or_create_collection(
            name="coffee_chat_contacts",
            metadata={"description": "Contact profiles and interactions"}
        )
        
        self.interactions_collection = self.client.get_or_create_collection(
            name="coffee_chat_interactions",
            metadata={"description": "Interaction logs and outcomes"}
        )
        
        app_logger.info("Memory layer initialized")
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get OpenAI embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            app_logger.error(f"Failed to get embedding: {e}")
            # Return dummy embedding (1536 dims) as fallback
            return [0.0] * 1536
    
    def save_message(
        self,
        contact_id: str,
        message_text: str,
        message_type: str,  # 'connection_request' or 'coffee_chat'
        response_status: Optional[str] = None,  # 'accepted', 'ignored', 'replied'
        response_time_hours: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Save a sent message to memory
        
        Args:
            contact_id: Unique contact identifier
            message_text: The message content
            message_type: Type of message
            response_status: Response status (if known)
            response_time_hours: Hours until response
            metadata: Additional metadata
        """
        try:
            message_id = f"msg_{contact_id}_{datetime.utcnow().timestamp()}"
            
            # Get embedding
            embedding = self._get_embedding(message_text)
            
            # Prepare metadata
            msg_metadata = {
                'contact_id': contact_id,
                'type': message_type,
                'sent_at': datetime.utcnow().isoformat(),
                'response_status': response_status or 'pending',
                'response_time_hours': response_time_hours or 0
            }
            
            if metadata:
                msg_metadata.update(metadata)
            
            # Save to ChromaDB
            self.messages_collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[message_text],
                metadatas=[msg_metadata]
            )
            
            app_logger.info(f"Saved message: {message_id}")
            
        except Exception as e:
            app_logger.error(f"Failed to save message: {e}")
    
    def save_contact(
        self,
        contact_id: str,
        contact_data: Dict
    ):
        """
        Save contact profile to memory
        
        Args:
            contact_id: Unique contact identifier
            contact_data: Contact information
        """
        try:
            # Create profile text for embedding
            profile_text = f"{contact_data.get('title', '')} at {contact_data.get('company', '')}. "
            if contact_data.get('school_name'):
                profile_text += f"Alumni of {contact_data['school_name']}. "
            
            # Get embedding
            embedding = self._get_embedding(profile_text)
            
            # Prepare metadata
            metadata = {
                'name': contact_data.get('name', ''),
                'company': contact_data.get('company', ''),
                'title': contact_data.get('title', ''),
                'school': contact_data.get('school_name', ''),
                'first_contact_date': datetime.utcnow().isoformat(),
                'relationship_status': 'pending'
            }
            
            # Save to ChromaDB
            self.contacts_collection.add(
                ids=[contact_id],
                embeddings=[embedding],
                documents=[profile_text],
                metadatas=[metadata]
            )
            
            app_logger.info(f"Saved contact: {contact_id}")
            
        except Exception as e:
            app_logger.error(f"Failed to save contact: {e}")
    
    def save_interaction(
        self,
        contact_id: str,
        interaction_type: str,  # 'reply_received', 'coffee_chat_scheduled', etc.
        content: str,
        sentiment: str = 'neutral',  # 'positive', 'neutral', 'negative'
        outcome: Optional[str] = None
    ):
        """
        Save an interaction event
        
        Args:
            contact_id: Contact identifier
            interaction_type: Type of interaction
            content: Interaction content
            sentiment: Sentiment analysis result
            outcome: Outcome of interaction
        """
        try:
            interaction_id = f"interaction_{contact_id}_{datetime.utcnow().timestamp()}"
            
            # Get embedding
            embedding = self._get_embedding(content)
            
            # Metadata
            metadata = {
                'contact_id': contact_id,
                'type': interaction_type,
                'timestamp': datetime.utcnow().isoformat(),
                'sentiment': sentiment,
                'outcome': outcome or 'unknown'
            }
            
            # Save
            self.interactions_collection.add(
                ids=[interaction_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            app_logger.info(f"Saved interaction: {interaction_id}")
            
        except Exception as e:
            app_logger.error(f"Failed to save interaction: {e}")
    
    def get_successful_messages(
        self,
        message_type: str = 'coffee_chat',
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve successful message templates
        
        Args:
            message_type: Type of message to retrieve
            limit: Max number of messages
            
        Returns:
            List of successful messages
        """
        try:
            # Query for accepted messages
            results = self.messages_collection.get(
                where={
                    "type": message_type,
                    "response_status": "accepted"
                },
                limit=limit
            )
            
            messages = []
            for i, doc in enumerate(results['documents']):
                messages.append({
                    'message_text': doc,
                    'metadata': results['metadatas'][i]
                })
            
            return messages
            
        except Exception as e:
            app_logger.error(f"Failed to get successful messages: {e}")
            return []
    
    def find_similar_contacts(
        self,
        query_contact: Dict,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar contacts based on profile
        
        Args:
            query_contact: Contact to match against
            limit: Max results
            
        Returns:
            List of similar contacts
        """
        try:
            # Create query text
            query_text = f"{query_contact.get('title', '')} at {query_contact.get('company', '')}"
            
            # Get embedding
            query_embedding = self._get_embedding(query_text)
            
            # Query ChromaDB
            results = self.contacts_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            contacts = []
            for i, doc in enumerate(results['documents'][0]):
                contacts.append({
                    'profile': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity': results['distances'][0][i] if 'distances' in results else None
                })
            
            return contacts
            
        except Exception as e:
            app_logger.error(f"Failed to find similar contacts: {e}")
            return []
    
    def has_contacted(self, contact_id: str) -> bool:
        """
        Check if we've already contacted this person
        
        Args:
            contact_id: Contact identifier
            
        Returns:
            True if already contacted
        """
        try:
            result = self.contacts_collection.get(ids=[contact_id])
            return len(result['ids']) > 0
        except:
            return False
    
    def get_stats(self) -> Dict:
        """
        Get memory layer statistics
        
        Returns:
            Dict with stats
        """
        try:
            messages_count = self.messages_collection.count()
            contacts_count = self.contacts_collection.count()
            interactions_count = self.interactions_collection.count()
            
            # Get success rate
            accepted = self.messages_collection.get(
                where={"response_status": "accepted"}
            )
            accepted_count = len(accepted['ids'])
            success_rate = (accepted_count / messages_count * 100) if messages_count > 0 else 0
            
            return {
                'total_messages': messages_count,
                'total_contacts': contacts_count,
                'total_interactions': interactions_count,
                'accepted_connections': accepted_count,
                'success_rate': success_rate
            }
        except Exception as e:
            app_logger.error(f"Failed to get stats: {e}")
            return {}


# Demo/Test
if __name__ == "__main__":
    print("🧠 Memory Layer Demo\n")
    print("=" * 60)
    
    # Initialize memory
    memory = CoffeeChatMemory()
    
    # Test 1: Save a contact
    print("\n1. Saving Contact:")
    print("-" * 60)
    contact_data = {
        'name': 'Jane Smith',
        'title': 'Learning Designer',
        'company': 'Shopify',
        'school_name': 'University of Western Ontario'
    }
    memory.save_contact('contact_jane_001', contact_data)
    print("   ✅ Contact saved")
    
    # Test 2: Save a message
    print("\n2. Saving Message:")
    print("-" * 60)
    message = "Hi Jane, fellow UWO alum here! I'd love to connect and learn about your work at Shopify."
    memory.save_message(
        contact_id='contact_jane_001',
        message_text=message,
        message_type='connection_request',
        response_status='accepted',
        response_time_hours=24
    )
    print("   ✅ Message saved")
    
    # Test 3: Save interaction
    print("\n3. Saving Interaction:")
    print("-" * 60)
    memory.save_interaction(
        contact_id='contact_jane_001',
        interaction_type='reply_received',
        content="Thanks for reaching out! I'd be happy to chat.",
        sentiment='positive',
        outcome='coffee_chat_scheduled'
    )
    print("   ✅ Interaction saved")
    
    # Test 4: Get successful messages
    print("\n4. Retrieving Successful Messages:")
    print("-" * 60)
    successful = memory.get_successful_messages('connection_request', limit=3)
    print(f"   Found {len(successful)} successful messages")
    
    # Test 5: Find similar contacts
    print("\n5. Finding Similar Contacts:")
    print("-" * 60)
    query = {
        'title': 'Software Engineer',
        'company': 'Amazon'
    }
    similar = memory.find_similar_contacts(query, limit=3)
    print(f"   Found {len(similar)} similar contacts")
    
    # Test 6: Get stats
    print("\n6. Memory Stats:")
    print("-" * 60)
    stats = memory.get_stats()
    print(f"   Total Messages: {stats.get('total_messages', 0)}")
    print(f"   Total Contacts: {stats.get('total_contacts', 0)}")
    print(f"   Total Interactions: {stats.get('total_interactions', 0)}")
    print(f"   Success Rate: {stats.get('success_rate', 0):.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Memory Layer Demo Complete!")
