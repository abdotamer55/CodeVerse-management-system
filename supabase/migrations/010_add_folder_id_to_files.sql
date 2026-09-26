-- ==============================================================================
-- CodeVerse LMS: Add folder_id to files table for nested folder management
-- Migration: 010_add_folder_id_to_files.sql
-- ==============================================================================

ALTER TABLE files ADD COLUMN IF NOT EXISTS folder_id INTEGER REFERENCES files(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);
