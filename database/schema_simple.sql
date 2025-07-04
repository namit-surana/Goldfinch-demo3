-- Simple schema updates for cancellation functionality
-- Add cancellation fields to chat_messages table

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN DEFAULT FALSE;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS cancellation_timestamp TIMESTAMP WITH TIME ZONE;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS cancellation_reason TEXT; 