import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../.env'))

class FirestoreService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirestoreService, cls).__new__(cls)
            cls._instance._initialize_firestore()
        return cls._instance

    def _initialize_firestore(self):
        if not firebase_admin._apps:
            try:
                # Use a service account JSON file for authentication
                # The path to this file should be in your environment variables or .env
                service_account_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
                if not service_account_key_path:
                    raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY_PATH environment variable not set.")

                # Ensure the path is absolute and correct
                if not os.path.isabs(service_account_key_path):
                    service_account_key_path = os.path.abspath(service_account_key_path)
                
                if not os.path.exists(service_account_key_path):
                    raise FileNotFoundError(f"Firebase service account key file not found at: {service_account_key_path}")

                cred = credentials.Certificate(service_account_key_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Firebase Admin SDK: {e}")
                # Depending on your application's needs, you might want to re-raise
                # or handle this error more gracefully (e.g., disable Firestore features).
                raise
        else:
            logger.info("Firebase Admin SDK already initialized.")
        self.db = firestore.client()

    async def add_document(self, collection_name: str, data: dict, doc_id: str = None):
        try:
            collection_ref = self.db.collection(collection_name)
            if doc_id:
                await collection_ref.document(doc_id).set(data)
                logger.info(f"Document with ID '{doc_id}' added/updated in collection '{collection_name}'.")
                return doc_id
            else:
                doc_ref = await collection_ref.add(data)
                logger.info(f"Document added to collection '{collection_name}' with ID: {doc_ref.id}")
                return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding document to '{collection_name}': {e}")
            raise

    async def get_document(self, collection_name: str, doc_id: str):
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc = await doc_ref.get()
            if doc.exists:
                logger.info(f"Document '{doc_id}' retrieved from '{collection_name}'.")
                return doc.to_dict()
            else:
                logger.warning(f"Document '{doc_id}' not found in '{collection_name}'.")
                return None
        except Exception as e:
            logger.error(f"Error getting document '{doc_id}' from '{collection_name}': {e}")
            raise

    async def update_document(self, collection_name: str, doc_id: str, data: dict):
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            await doc_ref.update(data)
            logger.info(f"Document '{doc_id}' updated in '{collection_name}'.")
        except Exception as e:
            logger.error(f"Error updating document '{doc_id}' in '{collection_name}': {e}")
            raise

    async def delete_document(self, collection_name: str, doc_id: str):
        try:
            await self.db.collection(collection_name).document(doc_id).delete()
            logger.info(f"Document '{doc_id}' deleted from '{collection_name}'.")
        except Exception as e:
            logger.error(f"Error deleting document '{doc_id}' from '{collection_name}': {e}")
            raise

    async def query_collection(self, collection_name: str, query_params: list = None, order_by: list = None, limit: int = None):
        try:
            collection_ref = self.db.collection(collection_name)
            query = collection_ref

            if query_params:
                for param in query_params:
                    field, op, value = param
                    query = query.where(field, op, value)
            
            if order_by:
                for field, direction in order_by:
                    query = query.order_by(field, direction=firestore.Query.ASCENDING if direction == 'asc' else firestore.Query.DESCENDING)

            if limit:
                query = query.limit(limit)

            docs = await query.get()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id  # Include document ID in the results
                results.append(data)
            logger.info(f"Queried collection '{collection_name}'. Found {len(results)} documents.")
            return results
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            raise
    
    # Task-specific methods
    async def create_task(self, task_data):
        return await self.add_document("tasks", task_data)
    
    async def get_tasks(self, status=None):
        query_params = None
        if status:
            query_params = [("status", "==", status)]
        
        order_by = [("due_date", "asc")]
        return await self.query_collection("tasks", query_params, order_by)
    
    async def update_task(self, task_id, task_data):
        await self.update_document("tasks", task_id, task_data)
    
    # Reminder-specific methods
    async def create_reminder(self, reminder_data):
        return await self.add_document("reminders", reminder_data)
    
    async def get_reminders(self):
        # Get reminders ordered by reminder time
        order_by = [("reminder_time", "asc")]
        return await self.query_collection("reminders", None, order_by)
    
    # Goal-specific methods
    async def create_goal(self, goal_data):
        return await self.add_document("goals", goal_data)
    
    async def get_goals(self):
        # Get goals ordered by target date
        order_by = [("target_date", "asc")]
        return await self.query_collection("goals", None, order_by)
    
    # Note-specific methods
    async def create_note(self, note_data):
        return await self.add_document("notes", note_data)
    
    async def get_notes(self, category=None):
        query_params = None
        if category and category != "all":
            query_params = [("category", "==", category)]
        
        order_by = [("created_at", "desc")]
        return await self.query_collection("notes", query_params, order_by)
    
    # User preference methods
    async def update_user_preferences(self, conversation_id, preferences):
        # Store user preferences in a user_preferences collection
        await self.update_document("user_preferences", conversation_id, {"preferences": preferences})

# Example Usage (for testing purposes, not part of the class itself)
async def test_firestore_service():
    # Ensure you have FIREBASE_SERVICE_ACCOUNT_KEY_PATH set in your .env
    # and a valid service account key file at that path.
    
    firestore_service = FirestoreService()

    # Add a document
    task_data = {
        "description": "Buy groceries",
        "completed": False,
        "priority": 1,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    task_id = await firestore_service.add_document("tasks", task_data)
    print(f"Added task with ID: {task_id}")

    # Get a document
    retrieved_task = await firestore_service.get_document("tasks", task_id)
    print(f"Retrieved task: {retrieved_task}")

    # Update a document
    await firestore_service.update_document("tasks", task_id, {"completed": True})
    updated_task = await firestore_service.get_document("tasks", task_id)
    print(f"Updated task: {updated_task}")

    # Add another document for querying
    task_data_2 = {
        "description": "Walk the dog",
        "completed": False,
        "priority": 3,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    task_id_2 = await firestore_service.add_document("tasks", task_data_2)
    print(f"Added task 2 with ID: {task_id_2}")

    # Query documents
    # Get all incomplete tasks with priority > 0, ordered by priority descending
    query_results = await firestore_service.query_collection(
        "tasks",
        query_params=[
            ("completed", "==", False),
            ("priority", ">", 0)
        ],
        order_by=[
            ("priority", "desc")
        ]
    )
    print("Query results (incomplete tasks, priority > 0, ordered by priority desc):")
    for task in query_results:
        print(task)

    # Delete a document
    await firestore_service.delete_document("tasks", task_id)
    print(f"Deleted task with ID: {task_id}")

    # Verify deletion
    deleted_task = await firestore_service.get_document("tasks", task_id)
    print(f"Task after deletion: {deleted_task}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_firestore_service())