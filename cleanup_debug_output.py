#!/usr/bin/env python3
"""
SmugDups Debug Cleanup Script v5.0
File: cleanup_debug_output.py
PURPOSE: Remove excessive debug output and development artifacts
APPROACH: Quick cleanup - remove celebration messages, reduce verbose logging
"""

import os
import re
from pathlib import Path

def cleanup_file_debug(file_path: str) -> bool:
    """Clean up debug output in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Remove celebration/development artifact messages
        celebration_patterns = [
            r'print\(f?".*FINALLY WORKS.*"\)',
            r'print\(f?".*WORKING MOVEIMAGES.*"\)',
            r'print\(f?".*SUCCESS:.*"\)',
            r'print\(f?".*CONFIRMED:.*"\)',
            r'print\(f?".*TESTED:.*"\)',
            r'print\(f?".*VERIFIED:.*"\)',
            r'print\(f?".*COMPLETE:.*"\)',
            r'print\(f?".*REBRANDED:.*"\)',
            r'print\("🎉.*"\)',
            r'print\("✅.*WORKING.*"\)',
            r'print\("=".*"\)',  # ASCII banners
            r'print\("-".*"\)',  # ASCII separators
        ]
        
        for pattern in celebration_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
                changes_made.append(f"Removed {len(matches)} celebration message(s)")
        
        # Reduce verbose API logging - keep only essential info
        verbose_api_patterns = [
            r'print\(f?".*🔄 Following redirect.*"\)',
            r'print\(f?".*📥 Response:.*"\)',
            r'print\(f?".*📥 Redirect response:.*"\)',
            r'print\(f?".*🔍 Unexpected response format:.*"\)',
            r'print\(f?".*Attempt \d+:.*"\)',
            r'print\(f?".*📊 Source album still has image:.*"\)',
            r'print\(f?".*📊 Target album now has image:.*"\)',
            r'print\(f?".*🔍 Verifying move:.*"\)',
        ]
        
        for pattern in verbose_api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
                changes_made.append(f"Reduced verbose API logging ({len(matches)} lines)")
        
        # Remove redundant verification logging but keep essential ones
        redundant_patterns = [
            r'print\(f?".*Using CONFIRMED WORKING format.*"\)',
            r'print\(f?".*Using CONFIRMED WORKING moveimages format.*"\)',
            r'print\(f?".*CONFIRMED WORKING.*"\)',
            r'print\(f?".*KEY FIX.*"\)',
            r'print\(f?".*CRITICAL FIX.*"\)',
            r'print\(f?".*SmugMug engineering.*fix.*"\)',
        ]
        
        for pattern in redundant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
                changes_made.append(f"Removed redundant verification logging ({len(matches)} lines)")
        
        # Clean up excessive emoji usage in debug messages (keep user-facing ones)
        excessive_emoji_patterns = [
            r'print\(f?".*[📦📁✅❌🔄🎯🚀]{3,}.*"\)',  # Lines with 3+ emojis
        ]
        
        for pattern in excessive_emoji_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
                changes_made.append(f"Cleaned excessive emoji usage ({len(matches)} lines)")
        
        # Remove development workflow comments
        dev_comments = [
            r'# WORKING FORMAT.*',
            r'# CONFIRMED WORKING.*',
            r'# FINALLY WORKS.*',
            r'# SUCCESS:.*',
            r'# KEY FIX:.*',
            r'# CRITICAL FIX:.*',
        ]
        
        for pattern in dev_comments:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                changes_made.append(f"Removed development comments ({len(matches)} lines)")
        
        # Remove empty lines created by deletions (but not all empty lines)
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Max 2 consecutive empty lines
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if changes_made:
                print(f"   ✅ Cleaned: {file_path}")
                for change in changes_made:
                    print(f"      ▸ {change}")
                return True
        
        print(f"   ℹ️  No cleanup needed: {file_path}")
        return False
            
    except Exception as e:
        print(f"   ❌ Error cleaning {file_path}: {e}")
        return False

def get_files_to_cleanup() -> list:
    """Get list of files that likely have excessive debug output"""
    
    # High priority files (most verbose debug)
    high_priority = [
        "smugmug_api.py",
        "operations/smugmug_copy_operations.py", 
        "operations/enhanced_photo_copy_move.py",
        "gui/duplicate_widget.py"
    ]
    
    # Medium priority files
    medium_priority = [
        "operations/smugmug_album_operations.py",
        "core/duplicate_finder.py",
        "gui/main_window.py"
    ]
    
    # Find existing files
    files_to_clean = []
    
    for file_path in high_priority + medium_priority:
        if os.path.exists(file_path):
            files_to_clean.append((file_path, "HIGH" if file_path in high_priority else "MEDIUM"))
    
    return files_to_clean

def analyze_debug_levels():
    """Analyze current debug levels in the codebase"""
    print("🔍 ANALYZING CURRENT DEBUG LEVELS")
    print("="*50)
    
    files_to_check = get_files_to_cleanup()
    
    for file_path, priority in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count different types of debug output
            print_count = len(re.findall(r'print\(', content))
            celebration_count = len(re.findall(r'print\(.*[🎉✅🚀].*\)', content, re.IGNORECASE))
            api_debug_count = len(re.findall(r'print\(.*[📥🔄📊].*\)', content, re.IGNORECASE))
            
            print(f"\n📄 {file_path} ({priority} priority):")
            print(f"   📊 Total print statements: {print_count}")
            print(f"   🎉 Celebration/success messages: {celebration_count}")
            print(f"   🔧 API debug messages: {api_debug_count}")
            
            if print_count > 20:
                print(f"   ⚠️  HIGH debug volume - good candidate for cleanup")
            elif print_count > 10:
                print(f"   🟡 MEDIUM debug volume - moderate cleanup needed")
            else:
                print(f"   ✅ LOW debug volume - minimal cleanup needed")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {file_path}: {e}")

def main():
    """Main cleanup function"""
    print("🧹 SMUGDUPS DEBUG CLEANUP SCRIPT v5.0")
    print("STRATEGY: Quick cleanup - remove development artifacts")
    print("="*60)
    
    # Step 1: Analyze current state
    analyze_debug_levels()
    
    # Step 2: Get confirmation
    print(f"\n🎯 CLEANUP PLAN:")
    print(f"✅ REMOVE: Celebration messages, development artifacts")
    print(f"✅ REDUCE: Verbose API logging, redundant verification")
    print(f"✅ KEEP: User feedback, error messages, essential progress info")
    
    response = input(f"\n🤔 Proceed with cleanup? (y/n): ").lower().strip()
    if response != 'y':
        print("Cleanup cancelled.")
        return
    
    # Step 3: Clean up files
    print(f"\n🧹 CLEANING UP DEBUG OUTPUT...")
    
    files_to_clean = get_files_to_cleanup()
    updated_count = 0
    
    for file_path, priority in files_to_clean:
        print(f"\n📄 Processing {file_path} ({priority} priority)...")
        if cleanup_file_debug(file_path):
            updated_count += 1
    
    # Step 4: Summary
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   📄 Files processed: {len(files_to_clean)}")
    print(f"   ✅ Files cleaned: {updated_count}")
    print(f"   🎯 Approach: Conservative cleanup preserving essential feedback")
    
    print(f"\n📋 RECOMMENDED NEXT STEPS:")
    print(f"1. Test the application: python main.py")
    print(f"2. Check console output during a scan to see remaining verbosity")
    print(f"3. If still too verbose, consider implementing debug levels")
    print(f"4. Focus on optimizing _verify_image_moved() for performance")
    
    print(f"\n✨ SmugDups v5.0 debug cleanup complete!")

if __name__ == "__main__":
    main()
