"""Batch operations with rollback capability for repository management."""
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("repoforgex.batch_operations")


@dataclass
class Operation:
    """Represents a single operation in a batch."""
    name: str
    execute: Callable
    rollback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    success: bool = False
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class BatchOperationManager:
    """Manages batch operations with rollback capability."""
    
    def __init__(self):
        self.operations: List[Operation] = []
        self.executed_operations: List[Operation] = []
        self.failed_operations: List[Operation] = []
        
    def add_operation(self, name: str, execute: Callable, rollback: Optional[Callable] = None, **metadata):
        """
        Add an operation to the batch.
        
        Args:
            name: Name of the operation
            execute: Function to execute the operation
            rollback: Function to rollback the operation (if possible)
            **metadata: Additional metadata for the operation
        """
        op = Operation(name=name, execute=execute, rollback=rollback, metadata=metadata)
        self.operations.append(op)
        logger.debug(f"Added operation: {name}")
        
    def execute_all(self, stop_on_error: bool = True) -> Dict[str, Any]:
        """
        Execute all operations in the batch.
        
        Args:
            stop_on_error: If True, stop execution on first error
            
        Returns:
            Summary of execution results
        """
        logger.info(f"Executing batch of {len(self.operations)} operations")
        start_time = datetime.now()
        
        for op in self.operations:
            try:
                op.timestamp = datetime.now()
                logger.info(f"Executing: {op.name}")
                op.execute()
                op.executed = True
                op.success = True
                self.executed_operations.append(op)
                logger.info(f"✓ Success: {op.name}")
            except Exception as e:
                op.executed = True
                op.success = False
                op.error = str(e)
                self.failed_operations.append(op)
                logger.error(f"✗ Failed: {op.name} - {e}")
                
                if stop_on_error:
                    logger.warning("Stopping execution due to error")
                    break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'total': len(self.operations),
            'executed': len(self.executed_operations),
            'succeeded': len([op for op in self.executed_operations if op.success]),
            'failed': len(self.failed_operations),
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
        }
        
        logger.info(f"Batch execution complete: {summary['succeeded']}/{summary['executed']} succeeded")
        return summary
    
    def rollback_all(self) -> Dict[str, Any]:
        """
        Rollback all executed operations in reverse order.
        
        Returns:
            Summary of rollback results
        """
        logger.warning("Starting rollback of all operations")
        rollback_count = 0
        rollback_errors = []
        
        # Rollback in reverse order
        for op in reversed(self.executed_operations):
            if op.rollback is None:
                logger.warning(f"No rollback function for: {op.name}")
                continue
                
            try:
                logger.info(f"Rolling back: {op.name}")
                op.rollback()
                rollback_count += 1
                logger.info(f"✓ Rolled back: {op.name}")
            except Exception as e:
                error_msg = f"Failed to rollback {op.name}: {e}"
                logger.error(f"✗ {error_msg}")
                rollback_errors.append(error_msg)
        
        summary = {
            'rolled_back': rollback_count,
            'total_executed': len(self.executed_operations),
            'errors': rollback_errors
        }
        
        logger.info(f"Rollback complete: {rollback_count} operations rolled back")
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the batch."""
        return {
            'total_operations': len(self.operations),
            'executed': len(self.executed_operations),
            'pending': len(self.operations) - len(self.executed_operations),
            'succeeded': len([op for op in self.executed_operations if op.success]),
            'failed': len(self.failed_operations),
            'operations': [
                {
                    'name': op.name,
                    'executed': op.executed,
                    'success': op.success,
                    'error': op.error,
                    'metadata': op.metadata
                }
                for op in self.operations
            ]
        }


class RepositoryBatchCreator:
    """Helper class for creating repositories in batch with rollback support."""
    
    def __init__(self, github_client):
        self.client = github_client
        self.batch_manager = BatchOperationManager()
        self.created_repos: List[Dict[str, str]] = []
        self.created_local_dirs: List[Path] = []
    
    def add_repository_creation(self, name: str, owner: str, description: str = "",
                                private: bool = True, local_path: Optional[Path] = None):
        """
        Add a repository creation operation to the batch.
        
        Args:
            name: Repository name
            owner: Repository owner
            description: Repository description
            private: Whether the repository should be private
            local_path: Local path for the repository
        """
        def execute():
            # Create on GitHub
            result = self.client.create_repo(name=name, description=description, 
                                             private=private, owner=owner)
            self.created_repos.append({'owner': owner, 'name': name})
            
            # Create local directory if specified
            if local_path:
                local_path.mkdir(parents=True, exist_ok=True)
                self.created_local_dirs.append(local_path)
            
            return result
        
        def rollback():
            # Note: GitHub API doesn't provide easy repo deletion in basic client
            # This would require additional permissions and implementation
            logger.warning(f"Rollback for GitHub repo {owner}/{name} not fully implemented")
            
            # Remove local directory
            if local_path and local_path.exists():
                shutil.rmtree(local_path)
                logger.info(f"Removed local directory: {local_path}")
        
        self.batch_manager.add_operation(
            name=f"Create repository {owner}/{name}",
            execute=execute,
            rollback=rollback,
            owner=owner,
            repo_name=name,
            local_path=str(local_path) if local_path else None
        )
    
    def execute(self, stop_on_error: bool = True) -> Dict[str, Any]:
        """Execute all repository creations."""
        return self.batch_manager.execute_all(stop_on_error=stop_on_error)
    
    def rollback(self) -> Dict[str, Any]:
        """Rollback all created repositories."""
        return self.batch_manager.rollback_all()
    
    def get_status(self) -> Dict[str, Any]:
        """Get batch operation status."""
        return self.batch_manager.get_status()
