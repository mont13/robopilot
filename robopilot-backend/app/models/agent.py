"""
Enhanced Pydantic models for BeeAI Agent integration.

This module provides comprehensive models for agent interactions, message handling,
API request/response schemas, and monitoring capabilities optimized for the latest
BeeAI framework patterns and production usage.

Features:
- Full BeeAI framework compatibility with proper typing
- Enhanced validation and error handling
- Comprehensive monitoring and performance tracking
- Advanced tool calling support
- Memory management integration
- Health checking and diagnostics
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class AgentMessage(BaseModel):
    """
    Enhanced message model compatible with BeeAI framework.

    This model represents a single message in a conversation and provides
    seamless conversion to/from BeeAI message types with enhanced metadata support.
    """

    role: Literal["system", "user", "assistant"] = Field(
        ..., description="Message role - determines how the AI interprets the message"
    )
    content: str = Field(
        ..., description="Message content text", min_length=1, max_length=100000
    )
    timestamp: datetime | None = Field(
        default_factory=datetime.now, description="Message creation timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata and context"
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, description="Tool calls associated with this message"
    )
    token_count: int | None = Field(
        default=None, description="Estimated token count for this message"
    )
    processing_time: float | None = Field(
        default=None, description="Time taken to process this message in seconds"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate message content with enhanced checks."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        # Remove excessive whitespace while preserving intentional formatting
        return " ".join(v.split())

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Ensure role is properly formatted."""
        return v.lower()

    def estimate_tokens(self) -> int:
        """Estimate token count using a simple approximation."""
        if self.token_count is not None:
            return self.token_count
        # Simple approximation: ~4 characters per token
        return len(self.content) // 4 + 1

    def to_beeai_message(self):
        """Convert to appropriate BeeAI message type."""
        from beeai_framework.backend import AssistantMessage, SystemMessage, UserMessage

        if self.role == "system":
            return SystemMessage(self.content)
        elif self.role == "user":
            return UserMessage(self.content)
        elif self.role == "assistant":
            return AssistantMessage(self.content)
        else:
            raise ValueError(f"Invalid role: {self.role}")

    class Config:
        """Pydantic configuration with enhanced settings."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        validate_assignment = True


class ConversationHistory(BaseModel):
    """
    Model for managing conversation history with BeeAI compatibility.
    """

    session_id: str = Field(..., description="Unique session identifier")
    messages: list[AgentMessage] = Field(
        default_factory=list, description="Chronological list of messages"
    )
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a new message to the conversation."""
        message = AgentMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_last_message(self) -> AgentMessage | None:
        """Get the most recent message."""
        return self.messages[-1] if self.messages else None

    def get_messages_by_role(self, role: str) -> list[AgentMessage]:
        """Get all messages with specific role."""
        return [msg for msg in self.messages if msg.role == role]


class AgentExecutionRequest(BaseModel):
    """
    Enhanced request model for agent execution with comprehensive BeeAI configuration.

    Supports advanced execution parameters, memory management options, and
    monitoring configurations for production deployments.
    """

    session_id: str = Field(..., description="Session identifier", min_length=1)
    message: str = Field(
        ..., description="User message to process", min_length=1, max_length=50000
    )
    temperature: float | None = Field(
        default=0.7,
        description="Sampling temperature for response generation",
        ge=0.0,
        le=2.0,
    )
    max_iterations: int | None = Field(
        default=20, description="Maximum agent iterations", ge=1, le=100
    )
    max_retries: int | None = Field(
        default=3, description="Maximum retries per step", ge=0, le=20
    )
    include_robot_tools: bool = Field(
        default=True, description="Whether to include robot control tools"
    )
    stream_response: bool = Field(
        default=False, description="Enable streaming response mode"
    )
    system_prompt_override: str | None = Field(
        default=None, description="Override default system prompt", max_length=10000
    )
    memory_type: Literal["unconstrained", "token", "sliding"] | None = Field(
        default=None, description="Override memory type for this execution"
    )
    max_memory_tokens: int | None = Field(
        default=None, description="Maximum memory tokens (for token memory)", ge=1000
    )
    enable_monitoring: bool = Field(
        default=True, description="Enable detailed execution monitoring"
    )
    timeout_seconds: int | None = Field(
        default=300, description="Maximum execution timeout in seconds", ge=10, le=1800
    )
    priority: Literal["low", "normal", "high"] = Field(
        default="normal", description="Execution priority level"
    )
    custom_tools: list[str] = Field(
        default_factory=list, description="Additional custom tool names to include"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        """Validate message content with enhanced checks."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        # Clean and normalize message
        cleaned = " ".join(v.strip().split())
        if len(cleaned) < 1:
            raise ValueError("Message must contain meaningful content")
        return cleaned

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v or not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_memory_config(self):
        """Validate memory configuration consistency."""
        if self.memory_type == "token" and self.max_memory_tokens is None:
            self.max_memory_tokens = 8192  # Default for token memory
        elif self.memory_type != "token" and self.max_memory_tokens is not None:
            # Only token memory uses max_memory_tokens
            self.max_memory_tokens = None
        return self


class AgentExecutionResponse(BaseModel):
    """
    Enhanced response model for agent execution results with comprehensive metrics.

    Provides detailed execution information, performance metrics, and diagnostic
    data for monitoring and optimization purposes.
    """

    session_id: str = Field(..., description="Session identifier")
    response: str = Field(..., description="Agent-generated response")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed list of tools called during execution",
    )
    execution_time: float | None = Field(
        default=None, description="Total execution time in seconds"
    )
    iterations_used: int | None = Field(
        default=None, description="Number of agent iterations used"
    )
    retries_used: int | None = Field(
        default=None, description="Number of retries that occurred"
    )
    tokens_used: int | None = Field(
        default=None, description="Estimated tokens used for this execution"
    )
    memory_state: dict[str, Any] | None = Field(
        default_factory=dict, description="Current memory state information"
    )
    performance_metrics: dict[str, float] | None = Field(
        default_factory=dict, description="Detailed performance timing metrics"
    )
    error_details: dict[str, Any] | None = Field(
        default=None, description="Error information if execution partially failed"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal warnings during execution"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata and context"
    )

    def get_success_rate(self) -> float:
        """Calculate execution success rate based on retries."""
        if self.retries_used is None:
            return 1.0
        total_attempts = 1 + self.retries_used
        return 1.0 / total_attempts if total_attempts > 0 else 0.0

    def has_errors(self) -> bool:
        """Check if execution had any errors."""
        return self.error_details is not None and len(self.error_details) > 0

    def has_warnings(self) -> bool:
        """Check if execution had any warnings."""
        return len(self.warnings) > 0


class AgentToolCall(BaseModel):
    """
    Model for representing agent tool calls.
    """

    tool_name: str = Field(..., description="Name of the called tool")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool"
    )
    result: Any | None = Field(default=None, description="Tool execution result")
    timestamp: datetime | None = Field(default=None, description="Tool call timestamp")
    execution_time: float | None = Field(
        default=None, description="Tool execution time in seconds"
    )
    success: bool = Field(
        default=True, description="Whether tool execution was successful"
    )
    error_message: str | None = Field(
        default=None, description="Error message if tool execution failed"
    )


class AgentSessionInfo(BaseModel):
    """
    Model for agent session information and statistics.
    """

    session_id: str = Field(..., description="Session identifier")
    session_name: str | None = Field(default=None)
    message_count: int = Field(default=0, description="Number of messages in session")
    tool_calls_count: int = Field(default=0, description="Number of tool calls made")
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True, description="Whether session is active")
    agent_config: dict[str, Any] | None = Field(
        default_factory=dict, description="Agent configuration used for this session"
    )


class AgentHealthCheck(BaseModel):
    """
    Comprehensive model for agent service health status and system diagnostics.

    Provides detailed health information including component status, performance
    metrics, and diagnostic data for monitoring and alerting systems.
    """

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall health status"
    )
    llm_connection: bool = Field(..., description="LLM connection status")
    database_connection: bool = Field(..., description="Database connection status")
    tools_available: list[str] = Field(
        default_factory=list, description="List of available tools"
    )
    active_sessions: int = Field(default=0, description="Number of active sessions")
    total_sessions: int | None = Field(
        default=None, description="Total number of sessions in database"
    )
    memory_usage: dict[str, Any] | None = Field(
        default_factory=dict, description="Memory usage statistics"
    )
    performance_metrics: dict[str, float] | None = Field(
        default_factory=dict, description="System performance metrics"
    )
    last_check: datetime = Field(default_factory=datetime.now)
    uptime_seconds: float | None = Field(
        default=None, description="Service uptime in seconds"
    )
    errors: list[str] = Field(
        default_factory=list, description="List of current errors"
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of current warnings"
    )
    version_info: dict[str, str] | None = Field(
        default_factory=dict, description="Version information for key components"
    )
    mcp_status: dict[str, Any] | None = Field(
        default_factory=dict, description="MCP integration status and connections"
    )

    def is_healthy(self) -> bool:
        """Check if the service is in a healthy state."""
        return self.status == "healthy"

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return not (self.llm_connection and self.database_connection)

    def get_health_score(self) -> float:
        """Calculate a health score between 0.0 and 1.0."""
        score = 0.0
        if self.llm_connection:
            score += 0.4
        if self.database_connection:
            score += 0.4
        if len(self.errors) == 0:
            score += 0.2
        return min(score, 1.0)


class WeatherToolInput(BaseModel):
    """
    Example custom tool input model for weather queries.
    """

    location: str = Field(..., description="Location for weather query")
    date: str | None = Field(
        default=None, description="Date for weather query (YYYY-MM-DD format)"
    )
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius", description="Temperature units"
    )


class RobotControlToolInput(BaseModel):
    """
    Input model for robot control operations.
    """

    action: Literal[
        "move_home",
        "move_to_position",
        "control_gripper",
        "led_control",
        "pick_and_place",
        "reset_all",
    ] = Field(..., description="Robot action to perform")
    parameters: dict[str, Any] | None = Field(
        default_factory=dict, description="Action-specific parameters"
    )
    confirm_execution: bool = Field(
        default=False,
        description="Whether to confirm before executing potentially destructive actions",
    )


class StreamingResponse(BaseModel):
    """
    Model for streaming response chunks.
    """

    chunk_id: int = Field(..., description="Chunk sequence number")
    content: str = Field(..., description="Partial response content")
    is_complete: bool = Field(
        default=False, description="Whether this is the final chunk"
    )
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class AgentError(BaseModel):
    """
    Enhanced error model for agent operations.
    """

    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional error details"
    )
    session_id: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)
    recovery_suggestions: list[str] | None = Field(
        default_factory=list, description="Suggested recovery actions"
    )


class AgentMemorySnapshot(BaseModel):
    """
    Enhanced model for capturing comprehensive agent memory state.

    Provides detailed memory information including capacity utilization,
    performance metrics, and memory health indicators.
    """

    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Number of messages in memory")
    memory_type: str = Field(..., description="Type of memory being used")
    token_count: int | None = Field(default=None, description="Current token count")
    max_tokens: int | None = Field(default=None, description="Maximum token limit")
    token_utilization: float | None = Field(
        default=None, description="Token utilization percentage (0.0-1.0)"
    )
    last_message_timestamp: datetime | None = Field(default=None)
    memory_efficiency: float | None = Field(
        default=None, description="Memory efficiency score (0.0-1.0)"
    )
    compression_ratio: float | None = Field(
        default=None, description="Memory compression ratio if applicable"
    )
    sync_status: str | None = Field(
        default=None, description="Memory synchronization status"
    )
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Memory performance metrics"
    )
    health_indicators: dict[str, Any] = Field(
        default_factory=dict, description="Memory health indicators"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional memory metadata"
    )

    def calculate_utilization(self) -> float | None:
        """Calculate token utilization if both current and max are available."""
        if (
            self.token_count is not None
            and self.max_tokens is not None
            and self.max_tokens > 0
        ):
            return min(self.token_count / self.max_tokens, 1.0)
        return None

    def is_near_capacity(self, threshold: float = 0.8) -> bool:
        """Check if memory is near capacity."""
        utilization = self.calculate_utilization()
        return utilization is not None and utilization >= threshold

    def get_available_tokens(self) -> int | None:
        """Get number of available tokens."""
        if self.token_count is not None and self.max_tokens is not None:
            return max(0, self.max_tokens - self.token_count)
        return None


class AgentPerformanceMetrics(BaseModel):
    """
    Comprehensive model for agent performance tracking and analytics.

    Captures detailed performance data for optimization and monitoring
    purposes across multiple execution cycles.
    """

    session_id: str = Field(..., description="Session identifier")
    total_executions: int = Field(default=0, description="Total number of executions")
    successful_executions: int = Field(
        default=0, description="Number of successful executions"
    )
    failed_executions: int = Field(default=0, description="Number of failed executions")
    average_execution_time: float | None = Field(
        default=None, description="Average execution time in seconds"
    )
    min_execution_time: float | None = Field(
        default=None, description="Minimum execution time in seconds"
    )
    max_execution_time: float | None = Field(
        default=None, description="Maximum execution time in seconds"
    )
    average_iterations: float | None = Field(
        default=None, description="Average number of iterations per execution"
    )
    total_tool_calls: int = Field(default=0, description="Total number of tool calls")
    tool_success_rate: float | None = Field(
        default=None, description="Tool execution success rate"
    )
    memory_peak_usage: int | None = Field(
        default=None, description="Peak memory token usage"
    )
    error_patterns: dict[str, int] = Field(
        default_factory=dict, description="Error pattern frequency"
    )
    performance_trends: dict[str, list[float]] = Field(
        default_factory=dict, description="Performance trend data"
    )
    last_updated: datetime = Field(default_factory=datetime.now)

    def get_success_rate(self) -> float:
        """Calculate overall execution success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    def get_failure_rate(self) -> float:
        """Calculate overall execution failure rate."""
        return 1.0 - self.get_success_rate()

    def add_execution(
        self,
        execution_time: float,
        success: bool,
        iterations: int = 1,
        tool_calls: int = 0,
    ):
        """Add a new execution to the metrics."""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update timing metrics
        if self.average_execution_time is None:
            self.average_execution_time = execution_time
        else:
            self.average_execution_time = (
                self.average_execution_time * (self.total_executions - 1)
                + execution_time
            ) / self.total_executions

        if self.min_execution_time is None or execution_time < self.min_execution_time:
            self.min_execution_time = execution_time

        if self.max_execution_time is None or execution_time > self.max_execution_time:
            self.max_execution_time = execution_time

        # Update iteration metrics
        if self.average_iterations is None:
            self.average_iterations = iterations
        else:
            self.average_iterations = (
                self.average_iterations * (self.total_executions - 1) + iterations
            ) / self.total_executions

        self.total_tool_calls += tool_calls
        self.last_updated = datetime.now()
