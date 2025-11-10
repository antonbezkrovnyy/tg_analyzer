"""Queue analysis tasks to Redis for November ru_python data.

Usage:
    python queue_analysis_tasks.py

This script will:
1. Find all November 2025 data files in python-tg/data/ru_python
2. Check which ones need analysis (new or updated)
3. Queue analysis tasks to Redis
4. Worker can pick them up and process
"""

import json
import redis
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class AnalysisTaskQueue:
    """Queue analysis tasks to Redis."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """Initialize Redis connection."""
        self.redis = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=0,
            decode_responses=True
        )
        self.queue_name = "tg_analyzer:analysis_queue"
        
    def queue_task(self, chat_name: str, date: str, priority: int = 5) -> bool:
        """Queue an analysis task.
        
        Args:
            chat_name: Chat name (e.g., "ru_python")
            date: Date string (e.g., "2025-11-05")
            priority: Task priority (1-10, higher = more urgent)
            
        Returns:
            True if task was queued successfully
        """
        task = {
            "chat_name": chat_name,
            "date": date,
            "priority": priority,
            "queued_at": datetime.utcnow().isoformat(),
            "batch_size": 100
        }
        
        # Add to sorted set with priority as score (higher priority = higher score)
        task_id = f"{chat_name}:{date}"
        self.redis.zadd(self.queue_name, {task_id: priority})
        
        # Store task details
        self.redis.hset(f"tg_analyzer:task:{task_id}", mapping=task)
        
        return True
    
    def get_queue_length(self) -> int:
        """Get number of tasks in queue."""
        return self.redis.zcard(self.queue_name)
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks sorted by priority."""
        task_ids = self.redis.zrevrange(self.queue_name, 0, -1, withscores=True)
        
        tasks = []
        for task_id, priority in task_ids:
            task_data = self.redis.hgetall(f"tg_analyzer:task:{task_id}")
            task_data['priority'] = int(priority)
            tasks.append(task_data)
        
        return tasks
    
    def clear_queue(self):
        """Clear all tasks from queue (for testing)."""
        task_ids = self.redis.zrange(self.queue_name, 0, -1)
        for task_id in task_ids:
            self.redis.delete(f"tg_analyzer:task:{task_id}")
        self.redis.delete(self.queue_name)


def find_data_files(data_path: Path) -> List[tuple]:
    """Find all November 2025 data files.
    
    Returns:
        List of (date_string, file_path, file_size) tuples
    """
    files = []
    
    if not data_path.exists():
        print(f"❌ Data path not found: {data_path}")
        return files
    
    for json_file in sorted(data_path.glob("2025-11-*.json")):
        date_str = json_file.stem  # e.g., "2025-11-05"
        files.append((date_str, json_file, json_file.stat().st_size))
    
    return files


def check_needs_analysis(date: str, data_file: Path, output_path: Path) -> bool:
    """Check if a data file needs analysis.
    
    Returns:
        True if file needs analysis (new or updated since last analysis)
    """
    output_file = output_path / f"{date}.json"
    
    # If no output file exists, definitely needs analysis
    if not output_file.exists():
        return True
    
    # If data file is newer than output, needs re-analysis
    data_mtime = data_file.stat().st_mtime
    output_mtime = output_file.stat().st_mtime
    
    return data_mtime > output_mtime


def main():
    """Main function to queue analysis tasks."""
    print("=" * 60)
    print("  📋 Analysis Task Queue Manager")
    print("=" * 60)
    print()
    
    # Configuration
    data_path = Path(r"C:\Users\Мой компьютер\Desktop\python-tg\data\ru_python")
    output_path = Path(r"C:\Users\Мой компьютер\Desktop\tg_analyzer\output\ru_python")
    chat_name = "ru_python"
    
    # Initialize queue
    print("🔌 Connecting to Redis...")
    try:
        queue = AnalysisTaskQueue(redis_host="localhost", redis_port=6379)
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running: docker ps | grep redis")
        return
    
    print()
    
    # Find data files
    print(f"📂 Scanning: {data_path}")
    data_files = find_data_files(data_path)
    
    if not data_files:
        print("❌ No data files found for November 2025")
        return
    
    print(f"✅ Found {len(data_files)} data file(s)")
    print()
    
    # Check which need analysis
    tasks_to_queue = []
    
    print("Checking analysis status:")
    print("-" * 60)
    
    for date, data_file, size in data_files:
        size_kb = size / 1024
        needs_analysis = check_needs_analysis(date, data_file, output_path)
        
        status = "🆕 NEW" if not (output_path / f"{date}.json").exists() else "🔄 UPDATED"
        if not needs_analysis:
            status = "✅ UP-TO-DATE"
        
        print(f"  {date}: {size_kb:>8.1f} KB | {status}")
        
        if needs_analysis:
            tasks_to_queue.append(date)
    
    print("-" * 60)
    print()
    
    if not tasks_to_queue:
        print("✅ All files are up-to-date! Nothing to queue.")
        return
    
    # Queue tasks
    print(f"📤 Queuing {len(tasks_to_queue)} analysis task(s)...")
    print()
    
    for i, date in enumerate(tasks_to_queue, 1):
        # Priority: newer dates get higher priority
        priority = 10 - i  # Most recent = highest priority
        
        queue.queue_task(chat_name, date, priority)
        print(f"  ✓ Queued: {chat_name} @ {date} (priority: {priority})")
    
    print()
    print("=" * 60)
    print(f"✅ Successfully queued {len(tasks_to_queue)} task(s)")
    print("=" * 60)
    print()
    print("Queue statistics:")
    print(f"  Total tasks in queue: {queue.get_queue_length()}")
    print()
    print("Next steps:")
    print("  1. Start the analyzer worker: python scripts/analysis_worker.py")
    print("  2. Or manually process: python scripts/analyze_full_day.py ru_python <date> --batch-size 100")
    print()
    print("View queue status:")
    print("  docker exec tg-redis redis-cli ZRANGE tg_analyzer:analysis_queue 0 -1 WITHSCORES")
    print()


if __name__ == "__main__":
    main()
