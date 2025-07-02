-- Goldfinch Research API Database Schema
-- PostgreSQL compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    user_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    default_domain_set_id VARCHAR
);

-- Domain sets table
CREATE TABLE domain_sets (
    domain_set_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    name VARCHAR NOT NULL,
    description TEXT,
    domain_metadata_list JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_default BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0
);

-- Add foreign key constraint for users.default_domain_set_id
ALTER TABLE users ADD CONSTRAINT fk_users_default_domain_set 
    FOREIGN KEY (default_domain_set_id) REFERENCES domain_sets(domain_set_id);

-- Sessions table
CREATE TABLE chat_sessions (
    session_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    title VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    session_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    current_memory_id VARCHAR
);

-- Conversation memory table
CREATE TABLE conversation_memory (
    memory_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    session_id VARCHAR NOT NULL REFERENCES chat_sessions(session_id),
    summary TEXT,
    up_to_message_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    key_context JSONB DEFAULT '{}',
    summarization_strategy VARCHAR
);

-- Add foreign key constraint for sessions.current_memory_id
ALTER TABLE chat_sessions ADD CONSTRAINT fk_chat_sessions_current_memory 
    FOREIGN KEY (current_memory_id) REFERENCES conversation_memory(memory_id);

-- Chat messages table
CREATE TABLE chat_messages (
    message_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    session_id VARCHAR NOT NULL REFERENCES chat_sessions(session_id),
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_order INTEGER NOT NULL,
    message_metadata JSONB DEFAULT '{}',
    is_summarized BOOLEAN DEFAULT FALSE
);

-- Research requests table
CREATE TABLE research_requests (
    request_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    session_id VARCHAR NOT NULL REFERENCES chat_sessions(session_id),
    message_id VARCHAR REFERENCES chat_messages(message_id),
    research_question TEXT NOT NULL,
    workflow_type VARCHAR NOT NULL,
    domain_metadata_used JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time FLOAT,
    status VARCHAR NOT NULL DEFAULT 'pending',
    query_strategy JSONB DEFAULT '{}'
);



-- Query logs table
CREATE TABLE query_logs (
    query_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    request_id VARCHAR NOT NULL REFERENCES research_requests(request_id),
    query_text TEXT NOT NULL,
    query_type VARCHAR NOT NULL,
    target_domain VARCHAR,
    tool_used VARCHAR NOT NULL,
    time_taken FLOAT,
    raw_response JSONB,
    processed_response JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR NOT NULL DEFAULT 'pending',
    performance_metrics JSONB DEFAULT '{}'
);




-- Analytics table
CREATE TABLE analytics (
    analytics_id VARCHAR PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR REFERENCES users(user_id),
    session_id VARCHAR REFERENCES chat_sessions(session_id),
    event_type VARCHAR NOT NULL,
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address VARCHAR,
    user_agent VARCHAR,
    performance_data JSONB DEFAULT '{}'
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_research_requests_session_id ON research_requests(session_id);
CREATE INDEX idx_research_requests_timestamp ON research_requests(timestamp);

CREATE INDEX idx_query_logs_request_id ON query_logs(request_id);
CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_timestamp ON analytics(timestamp);


-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domain_sets_updated_at BEFORE UPDATE ON domain_sets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 