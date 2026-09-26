-- ==============================================================================
-- CodeVerse LMS: Expand files category check constraint to support folder and all types
-- Migration: 009_expand_files_category_check.sql
-- ==============================================================================

ALTER TABLE files DROP CONSTRAINT IF EXISTS files_category_check;
ALTER TABLE files ADD CONSTRAINT files_category_check 
    CHECK (category IN ('pdf', 'zip', 'video', 'slides', 'folder', 'code', 'doc', 'image', 'audio', 'other'));
