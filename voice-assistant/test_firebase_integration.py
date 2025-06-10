#!/usr/bin/env python3
"""
Test script to verify Firebase integration for note-taking functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from firebase.firestore_service import FirestoreService
from functions.note_functions import NoteFunctions

async def test_firebase_connection():
    """Test basic Firebase connection"""
    print("Testing Firebase connection...")
    try:
        firestore_service = FirestoreService()
        print("✅ Firebase connection successful")
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

async def test_note_creation():
    """Test note creation functionality"""
    print("\nTesting note creation...")
    try:
        note_functions = NoteFunctions()
        
        # Create a test note
        test_content = f"Test note created at {datetime.now().isoformat()}"
        result = await note_functions.take_note(
            content=test_content,
            category="test",
            tags=["integration-test"],
            capture_context=False  # Disable context capture for testing
        )
        
        if result["success"]:
            print(f"✅ Note created successfully with ID: {result['note_id']}")
            print(f"   Content: {test_content}")
            return result["note_id"]
        else:
            print(f"❌ Note creation failed: {result['message']}")
            return None
            
    except Exception as e:
        print(f"❌ Note creation failed with exception: {e}")
        return None

async def test_note_retrieval(note_id):
    """Test note retrieval functionality"""
    print("\nTesting note retrieval...")
    try:
        firestore_service = FirestoreService()
        note = await firestore_service.get_document("notes", note_id)
        
        if note:
            print(f"✅ Note retrieved successfully:")
            print(f"   ID: {note_id}")
            print(f"   Content: {note['content']}")
            print(f"   Category: {note['category']}")
            print(f"   Tags: {note['tags']}")
            print(f"   Created: {note['created_at']}")
            return True
        else:
            print(f"❌ Note not found with ID: {note_id}")
            return False
            
    except Exception as e:
        print(f"❌ Note retrieval failed: {e}")
        return False

async def test_note_listing():
    """Test note listing functionality"""
    print("\nTesting note listing...")
    try:
        note_functions = NoteFunctions()
        result = await note_functions.list_notes(category="test")
        
        if result["success"]:
            notes = result["notes"]
            print(f"✅ Found {len(notes)} test notes")
            for note in notes[:3]:  # Show first 3 notes
                print(f"   - {note['content'][:50]}... (ID: {note['id']})")
            return True
        else:
            print(f"❌ Note listing failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Note listing failed: {e}")
        return False

async def cleanup_test_notes():
    """Clean up test notes"""
    print("\nCleaning up test notes...")
    try:
        firestore_service = FirestoreService()
        
        # Get all test notes
        test_notes = await firestore_service.get_notes(category="test")
        
        deleted_count = 0
        for note in test_notes:
            if "integration-test" in note.get("tags", []):
                await firestore_service.delete_document("notes", note["id"])
                deleted_count += 1
        
        print(f"✅ Cleaned up {deleted_count} test notes")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

async def main():
    """Run all Firebase integration tests"""
    print("🔥 Firebase Integration Test Suite")
    print("=" * 40)
    
    # Test 1: Firebase connection
    if not await test_firebase_connection():
        print("\n❌ Firebase connection failed. Stopping tests.")
        return
    
    # Test 2: Note creation
    note_id = await test_note_creation()
    if not note_id:
        print("\n❌ Note creation failed. Stopping tests.")
        return
    
    # Test 3: Note retrieval
    if not await test_note_retrieval(note_id):
        print("\n❌ Note retrieval failed.")
    
    # Test 4: Note listing
    await test_note_listing()
    
    # Test 5: Cleanup
    await cleanup_test_notes()
    
    print("\n🎉 Firebase integration tests completed!")
    print("\nYou can now test the voice assistant note-taking functionality.")
    print("Try saying: 'Take a note: This is my test note'")

if __name__ == "__main__":
    asyncio.run(main())