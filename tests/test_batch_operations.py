"""Tests for batch operations and rollback functionality."""

from repoforgex.batch_operations import BatchOperationManager, Operation, RepositoryBatchCreator


class TestBatchOperationManager:
    """Test batch operation manager."""

    def test_add_operation(self):
        """Test adding operations."""
        manager = BatchOperationManager()

        def dummy_execute():
            pass

        manager.add_operation("test-op", dummy_execute)
        assert len(manager.operations) == 1
        assert manager.operations[0].name == "test-op"

    def test_execute_all_success(self):
        """Test executing all operations successfully."""
        manager = BatchOperationManager()
        results = []

        def op1():
            results.append(1)

        def op2():
            results.append(2)

        manager.add_operation("op1", op1)
        manager.add_operation("op2", op2)

        summary = manager.execute_all()

        assert summary["total"] == 2
        assert summary["succeeded"] == 2
        assert summary["failed"] == 0
        assert results == [1, 2]

    def test_execute_with_failure(self):
        """Test execution with failures."""
        manager = BatchOperationManager()

        def success_op():
            pass

        def fail_op():
            raise ValueError("Test error")

        manager.add_operation("success", success_op)
        manager.add_operation("fail", fail_op)

        summary = manager.execute_all(stop_on_error=False)

        assert summary["total"] == 2
        assert summary["succeeded"] == 1
        assert summary["failed"] == 1

    def test_stop_on_error(self):
        """Test stopping on first error."""
        manager = BatchOperationManager()
        results = []

        def op1():
            results.append(1)

        def fail_op():
            raise ValueError("Error")

        def op3():
            results.append(3)

        manager.add_operation("op1", op1)
        manager.add_operation("fail", fail_op)
        manager.add_operation("op3", op3)

        summary = manager.execute_all(stop_on_error=True)

        assert results == [1]  # op3 should not execute
        assert summary["executed"] == 1  # Only first operation succeeded
        assert summary["failed"] == 1  # Second operation failed and stopped execution

    def test_rollback_all(self):
        """Test rolling back operations."""
        manager = BatchOperationManager()
        rollback_results = []

        def execute():
            pass

        def rollback():
            rollback_results.append("rolled back")

        manager.add_operation("op1", execute, rollback)
        manager.add_operation("op2", execute, rollback)

        manager.execute_all()
        summary = manager.rollback_all()

        assert summary["rolled_back"] == 2
        assert len(rollback_results) == 2

    def test_rollback_reverse_order(self):
        """Test rollback happens in reverse order."""
        manager = BatchOperationManager()
        order = []

        def make_execute(n):
            def execute():
                order.append(f"exec-{n}")

            return execute

        def make_rollback(n):
            def rollback():
                order.append(f"rollback-{n}")

            return rollback

        manager.add_operation("op1", make_execute(1), make_rollback(1))
        manager.add_operation("op2", make_execute(2), make_rollback(2))

        manager.execute_all()
        manager.rollback_all()

        assert order == ["exec-1", "exec-2", "rollback-2", "rollback-1"]

    def test_get_status(self):
        """Test getting batch status."""
        manager = BatchOperationManager()

        manager.add_operation("op1", lambda: None, metadata={"key": "value"})
        status = manager.get_status()

        assert status["total_operations"] == 1
        assert status["pending"] == 1
        assert status["executed"] == 0

        manager.execute_all()
        status = manager.get_status()

        assert status["executed"] == 1
        assert status["pending"] == 0


class TestRepositoryBatchCreator:
    """Test repository batch creator."""

    def test_add_repository_creation(self):
        """Test adding repository creation to batch."""

        # Mock GitHub client
        class MockClient:
            def create_repo(self, **kwargs):
                return {"id": 123}

        client = MockClient()
        creator = RepositoryBatchCreator(client)

        creator.add_repository_creation(
            name="test-repo",
            owner="test-owner",
            description="Test description",
            private=True,
        )

        assert len(creator.batch_manager.operations) == 1

    def test_batch_status(self):
        """Test getting batch status."""

        class MockClient:
            def create_repo(self, **kwargs):
                return {"id": 123}

        client = MockClient()
        creator = RepositoryBatchCreator(client)

        creator.add_repository_creation("repo1", "owner1")
        creator.add_repository_creation("repo2", "owner2")

        status = creator.get_status()
        assert status["total_operations"] == 2
        assert status["pending"] == 2


class TestOperation:
    """Test Operation dataclass."""

    def test_operation_initialization(self):
        """Test operation creation."""

        def dummy():
            pass

        op = Operation(name="test", execute=dummy)

        assert op.name == "test"
        assert op.executed is False
        assert op.success is False
        assert op.error is None
        assert op.metadata == {}

    def test_operation_with_metadata(self):
        """Test operation with metadata."""
        op = Operation(
            name="test",
            execute=lambda: None,
            metadata={"repo": "test-repo", "owner": "user"},
        )

        assert op.metadata["repo"] == "test-repo"
        assert op.metadata["owner"] == "user"
