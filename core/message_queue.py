#!/usr/bin/env python3
"""
Message Queue

Provides Redis-based inter-agent messaging for task coordination.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageQueue:
    """
    Redis-based message queue for inter-agent communication.
    
    Features:
    - Pub/Sub messaging
    - Task queues
    - Message persistence
    - Priority queuing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize message queue.
        
        Args:
            config: Configuration dictionary containing:
                - redis_host: Redis host (default: localhost)
                - redis_port: Redis port (default: 6379)
                - redis_db: Redis database number (default: 0)
                - redis_password: Redis password (optional)
        """
        self.config = config
        self._redis_client = None
        self._pubsub = None
        self._subscriptions = {}
        
        # Initialize Redis if available
        if self._init_redis():
            logger.info("Message queue initialized with Redis")
        else:
            logger.warning("Redis not available. Using in-memory queue.")
            self._in_memory_queue = []
    
    def _init_redis(self) -> bool:
        """
        Initialize Redis connection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import redis
            
            self._redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=self.config.get('redis_db', 0),
                password=self.config.get('redis_password'),
                decode_responses=True
            )
            
            # Test connection
            self._redis_client.ping()
            self._pubsub = self._redis_client.pubsub()
            
            return True
            
        except ImportError:
            logger.warning("redis-py not installed. Install with: pip install redis")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return False
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message dictionary
        """
        message_json = json.dumps(message)
        
        if self._redis_client:
            try:
                self._redis_client.publish(channel, message_json)
                logger.debug(f"Published message to channel '{channel}'")
            except Exception as e:
                logger.error(f"Error publishing to Redis: {str(e)}")
        else:
            # In-memory fallback
            logger.debug(f"Published message to in-memory channel '{channel}'")
    
    async def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to a channel with a callback.
        
        Args:
            channel: Channel name
            callback: Async callback function to handle messages
        """
        if self._redis_client:
            try:
                self._pubsub.subscribe(channel)
                self._subscriptions[channel] = callback
                logger.info(f"Subscribed to channel '{channel}'")
            except Exception as e:
                logger.error(f"Error subscribing to Redis channel: {str(e)}")
        else:
            self._subscriptions[channel] = callback
            logger.info(f"Subscribed to in-memory channel '{channel}'")
    
    async def unsubscribe(self, channel: str):
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name
        """
        if self._redis_client:
            try:
                self._pubsub.unsubscribe(channel)
                if channel in self._subscriptions:
                    del self._subscriptions[channel]
                logger.info(f"Unsubscribed from channel '{channel}'")
            except Exception as e:
                logger.error(f"Error unsubscribing from Redis channel: {str(e)}")
        else:
            if channel in self._subscriptions:
                del self._subscriptions[channel]
    
    async def enqueue(self, queue_name: str, task: Dict[str, Any], priority: int = 0):
        """
        Add a task to a queue.
        
        Args:
            queue_name: Queue name
            task: Task dictionary
            priority: Task priority (higher = more urgent)
        """
        task_with_metadata = {
            'task': task,
            'priority': priority,
            'enqueued_at': datetime.now().isoformat()
        }
        
        if self._redis_client:
            try:
                # Use sorted set for priority queue
                self._redis_client.zadd(
                    f"queue:{queue_name}",
                    {json.dumps(task_with_metadata): -priority}  # Negative for descending order
                )
                logger.debug(f"Enqueued task to '{queue_name}' with priority {priority}")
            except Exception as e:
                logger.error(f"Error enqueueing to Redis: {str(e)}")
        else:
            # In-memory fallback
            self._in_memory_queue.append(task_with_metadata)
            self._in_memory_queue.sort(key=lambda x: -x['priority'])
    
    async def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the next task from a queue.
        
        Args:
            queue_name: Queue name
            
        Returns:
            Task dictionary or None if queue is empty
        """
        if self._redis_client:
            try:
                # Get highest priority item (lowest score due to negative priority)
                result = self._redis_client.zpopmin(f"queue:{queue_name}")
                
                if result:
                    task_json, _ = result[0]
                    task_data = json.loads(task_json)
                    logger.debug(f"Dequeued task from '{queue_name}'")
                    return task_data['task']
                
                return None
                
            except Exception as e:
                logger.error(f"Error dequeuing from Redis: {str(e)}")
                return None
        else:
            # In-memory fallback
            if self._in_memory_queue:
                task_data = self._in_memory_queue.pop(0)
                return task_data['task']
            return None
    
    async def get_queue_size(self, queue_name: str) -> int:
        """
        Get the number of items in a queue.
        
        Args:
            queue_name: Queue name
            
        Returns:
            Number of items in queue
        """
        if self._redis_client:
            try:
                return self._redis_client.zcard(f"queue:{queue_name}")
            except Exception as e:
                logger.error(f"Error getting queue size: {str(e)}")
                return 0
        else:
            return len(self._in_memory_queue)
    
    async def listen(self):
        """
        Start listening for messages on subscribed channels.
        This is a long-running coroutine.
        """
        if not self._redis_client:
            logger.warning("Cannot listen without Redis connection")
            return
        
        logger.info("Started listening for messages")
        
        try:
            for message in self._pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    if channel in self._subscriptions:
                        callback = self._subscriptions[channel]
                        await callback(data)
                        
        except Exception as e:
            logger.error(f"Error in message listener: {str(e)}")
    
    def close(self):
        """Close Redis connections"""
        if self._pubsub:
            self._pubsub.close()
        if self._redis_client:
            self._redis_client.close()
