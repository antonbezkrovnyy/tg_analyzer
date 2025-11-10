"""Analysis Worker - processes tasks from Redis queue.

Usage:
    python scripts/analysis_worker.py

This worker will:
1. Connect to Redis
2. Poll for tasks in the queue
3. Execute analysis for each task
4. Update task status
5. Repeat
"""

import sys
import time
import redis
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AnalysisWorker:
    """Worker that processes analysis tasks from Redis queue."""
    
    def __init__(
        self, 
        redis_host: str = "localhost",
        redis_port: int = 6379,
        poll_interval: float = 5.0
    ):
        """Initialize worker.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            poll_interval: Seconds to wait between polls
        """
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True
        )
        self.poll_interval = poll_interval
        self.queue_name = "tg_analyzer:analysis_queue"
        self.python_exe = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
        self.analyze_script = Path(__file__).parent / "analyze_full_day.py"
        self.running = True
        
    def get_next_task(self) -> Optional[Dict]:
        """Get next task from queue (highest priority).
        
        Returns:
            Task dict or None if queue is empty
        """
        # Get highest priority task (ZREVRANGE gets highest scores first)
        result = self.redis.zrevrange(self.queue_name, 0, 0, withscores=True)
        
        if not result:
            return None
        
        task_id, priority = result[0]
        
        # Get task details
        task_data = self.redis.hgetall(f"tg_analyzer:task:{task_id}")
        
        if not task_data:
            # Orphaned task ID, remove it
            self.redis.zrem(self.queue_name, task_id)
            return None
        
        task_data['task_id'] = task_id
        task_data['priority'] = int(priority)
        
        return task_data
    
    def mark_task_processing(self, task_id: str):
        """Mark task as being processed."""
        self.redis.hset(
            f"tg_analyzer:task:{task_id}",
            "status",
            "processing"
        )
        self.redis.hset(
            f"tg_analyzer:task:{task_id}",
            "started_at",
            datetime.utcnow().isoformat()
        )
    
    def mark_task_completed(self, task_id: str, success: bool, error: str = None):
        """Mark task as completed.
        
        Args:
            task_id: Task identifier
            success: Whether task completed successfully
            error: Error message if failed
        """
        # Remove from queue
        self.redis.zrem(self.queue_name, task_id)
        
        # Update task details
        status = "completed" if success else "failed"
        self.redis.hset(f"tg_analyzer:task:{task_id}", "status", status)
        self.redis.hset(
            f"tg_analyzer:task:{task_id}",
            "completed_at",
            datetime.utcnow().isoformat()
        )
        
        if error:
            self.redis.hset(f"tg_analyzer:task:{task_id}", "error", error)
        
        # Set TTL for completed tasks (1 hour)
        self.redis.expire(f"tg_analyzer:task:{task_id}", 3600)
    
    def execute_analysis(self, task: Dict) -> bool:
        """Execute analysis for a task.
        
        Args:
            task: Task dictionary with chat_name, date, batch_size
            
        Returns:
            True if analysis succeeded
        """
        chat_name = task['chat_name']
        date = task['date']
        batch_size = task.get('batch_size', 100)
        
        logger.info(f"🔬 Starting analysis: {chat_name} @ {date} (batch_size={batch_size})")
        
        try:
            # Build command
            cmd = [
                str(self.python_exe),
                str(self.analyze_script),
                chat_name,
                date,
                "--batch-size", str(batch_size)
            ]
            
            # Execute analysis script
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Analysis completed in {duration:.1f}s")
                
                # Log output summary
                if "discussions" in result.stdout.lower():
                    for line in result.stdout.split('\n'):
                        if 'discussions' in line.lower() or 'batch' in line.lower():
                            logger.info(f"   {line.strip()}")
                
                return True
            else:
                logger.error(f"❌ Analysis failed (exit code {result.returncode})")
                logger.error(f"   Error: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Analysis timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Analysis exception: {e}")
            return False
    
    def run(self):
        """Main worker loop."""
        logger.info("=" * 60)
        logger.info("  🤖 Analysis Worker Started")
        logger.info("=" * 60)
        logger.info(f"  Queue: {self.queue_name}")
        logger.info(f"  Poll interval: {self.poll_interval}s")
        logger.info(f"  Python: {self.python_exe}")
        logger.info(f"  Script: {self.analyze_script}")
        logger.info("=" * 60)
        logger.info("")
        
        try:
            while self.running:
                # Get next task
                task = self.get_next_task()
                
                if task is None:
                    logger.info(f"📭 Queue empty, waiting {self.poll_interval}s...")
                    time.sleep(self.poll_interval)
                    continue
                
                task_id = task['task_id']
                logger.info(f"📥 Got task: {task_id} (priority: {task['priority']})")
                
                # Mark as processing
                self.mark_task_processing(task_id)
                
                # Execute
                success = self.execute_analysis(task)
                
                # Mark completed
                error = None if success else "Analysis script failed"
                self.mark_task_completed(task_id, success, error)
                
                if success:
                    logger.info(f"✅ Task completed: {task_id}")
                else:
                    logger.error(f"❌ Task failed: {task_id}")
                
                logger.info("")
                
        except KeyboardInterrupt:
            logger.info("")
            logger.info("🛑 Worker stopped by user")
        except Exception as e:
            logger.error(f"💥 Worker crashed: {e}")
            raise
        finally:
            logger.info("👋 Worker shutdown complete")


def main():
    """Main entry point."""
    worker = AnalysisWorker(
        redis_host="localhost",
        redis_port=6379,
        poll_interval=5.0
    )
    
    worker.run()


if __name__ == "__main__":
    main()
