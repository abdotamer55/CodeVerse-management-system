-- Migration 014: Allow 'personal' in notifications type check constraint
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_type_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_type_check 
    CHECK (type IN ('exam', 'assignment', 'live', 'announcement', 'personal'));
